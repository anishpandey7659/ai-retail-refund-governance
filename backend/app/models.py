from sqlalchemy import ( BigInteger,Boolean,CheckConstraint,DateTime,ForeignKey,Index,Integer,Numeric,UniqueConstraint,
                        String,Text,func,text,Enum,Float, JSON)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from decimal import Decimal
import datetime as dt
import uuid
import enum



def _uuid() -> uuid.UUID:
    return uuid.uuid4()

class Base(DeclarativeBase):
    pass


PK = lambda: mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)  # noqa: E731

class TS:
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )



# -------------------------Identity-----------------------------------------------

class User(Base,TS):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = PK()
    keycloak_sub: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name:Mapped[str]=mapped_column(String(64)) 
    email:Mapped[str]=mapped_column(String(320),unique=True)
    role: Mapped[str] = mapped_column(String(20), default="customer")  # customer|reviewer|admin
    __table_args__ = (CheckConstraint("role in ('customer','reviewer','admin')", name="ck_user_role"),)


class Reviewer(Base,TS):
    __tablename__ = "reviewers"
    id: Mapped[uuid.UUID] = PK()
    user_id:Mapped[uuid.UUID]= mapped_column(ForeignKey("users.id",ondelete="CASCADE"),unique=True)
    name:Mapped[str]=mapped_column(String(64))


# -------------------------The Shop (What you can buy) -----------------------------------------------

class Product(Base,TS):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = PK()
    name:Mapped[str]=mapped_column(String(64),unique=True) 
    description: Mapped[str] = mapped_column(Text)
    category:Mapped[str] = mapped_column(String(60),index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock:Mapped[int] =mapped_column(Integer,default=100)
    image_key: Mapped[str] = mapped_column(String(300))  # MinIO object key
    


class Order(Base,TS):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_amount > 0", name="check_price_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    shipping_address: Mapped[str] = mapped_column(Text)
    card_last4: Mapped[str] = mapped_column(String(4))
    # Store only a keyed fingerprint from the payment provider, never raw payment data.
    payment_method_fingerprint: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Keyed payment-provider fingerprint; never raw payment data",
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    delivered_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    address_changes: Mapped[list["OrderAddressChange"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )



class OrderItem(Base,TS):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    name_at_purchase: Mapped[str] = mapped_column(String(255))

    order: Mapped["Order"] = relationship(back_populates="items")


class OrderAddressChange(Base):
    """Record actual address changes so they can be compared with delivery time."""

    __tablename__ = "order_address_changes"
    __table_args__ = (
        Index("ix_order_address_changes_order_changed", "order_id", "changed_at"),
    )

    id: Mapped[uuid.UUID] = PK()
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    changed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    order: Mapped["Order"] = relationship(back_populates="address_changes")



# ------------------------- Return (The core of the problem) -----------------------------------------------
RETURN_STATUSES = ("pending", "in_review", "escalated", "approved", "denied", "refunded")
REASON_CODES = (
    "damaged", "not_as_described", "quality", "wrong_item", "no_longer_needed",
    "defective", "arrived_late", "wrong_size", "item_not_received",
    "duplicate_item", "accidental_order",
)

def _in_list(col: str, values: tuple[str, ...]) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


class Return(Base, TS):
    __tablename__ = "returns"
    __table_args__ = (
        CheckConstraint(_in_list("status", RETURN_STATUSES), name="ck_returns_status"),
        CheckConstraint(_in_list("reason_code", REASON_CODES), name="ck_returns_reason_code"),
        Index("ix_returns_queue", "status", "claimed_by"),
        Index("uq_open_return_per_item", "order_item_id", unique=True,
              postgresql_where=text("status NOT IN ('denied','refunded')")),
    )

    id: Mapped[uuid.UUID] = PK()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), index=True)

    reason_code: Mapped[str] = mapped_column(String(32))
    reason_text: Mapped[str] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    status: Mapped[str] = mapped_column(String(20), default="pending")
    ai_result: Mapped[dict | None] = mapped_column(JSONB)   
    review_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    claimed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    # Warehouse inspection (NULL = unknown)
    item_received: Mapped[bool | None] = mapped_column(Boolean)
    item_opened: Mapped[bool | None] = mapped_column(Boolean)
    inspected_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    inspected_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    order_item: Mapped["OrderItem"] = relationship()
    photos: Mapped[list["ReturnPhoto"]] = relationship(
        back_populates="return_", cascade="all, delete-orphan"
    )
    refunds: Mapped[list["ReturnRefund"]] = relationship(back_populates="return_")



class ReturnPhoto(Base, TS):
    __tablename__ = "return_photos"
    id: Mapped[uuid.UUID] = PK()
    return_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("returns.id", ondelete="CASCADE"), index=True)
    object_key: Mapped[str] = mapped_column(String(300))
    content_type: Mapped[str] = mapped_column(String(60))
    bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    return_: Mapped["Return"] = relationship(
        back_populates="photos"
    )

    
REFUND_STATUSES = ("pending", "succeeded", "failed")
class ReturnRefund(Base):
    __tablename__ = "return_refunds"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_return_refunds_amount_positive"),
        CheckConstraint(_in_list("status", REFUND_STATUSES), name="ck_return_refunds_status"),
        # Only one successful refund per return (prevents double refund)
        Index("uq_one_success_refund", "return_id", unique=True,
              postgresql_where=text("status = 'succeeded'")),
    )

    id: Mapped[uuid.UUID] = PK()
    return_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("returns.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")

    provider_refund_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    return_: Mapped["Return"] = relationship(back_populates="refunds")



class SupportContact(Base):
    """A customer-initiated support contact; count rows for contact-volume features."""

    __tablename__ = "support_contacts"
    __table_args__ = (
        Index("ix_support_contacts_user_contacted", "user_id", "contacted_at"),
    )

    id: Mapped[uuid.UUID] = PK()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    return_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("returns.id"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(20))
    contacted_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ───────────────────────── Fraud ─────────────────────────────────────────────────────────────────────────────────────────

class FingerprintType(str, enum.Enum):
    ADDRESS = "address"
    DEVICE = "device"
    CARD = "card"


class Fingerprint(Base):
    __tablename__ = "fingerprints"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "fingerprint_type", "fingerprint_hash", name="uq_fingerprint_per_user"
        ),
        # "which accounts share this address/device/card?"
        Index("ix_fingerprints_type_hash", "fingerprint_type", "fingerprint_hash"),
    )

    id: Mapped[uuid.UUID] = PK()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    fingerprint_type: Mapped[FingerprintType] = mapped_column(
        Enum(FingerprintType, name="fingerprint_type")
    )
    fingerprint_hash: Mapped[str] = mapped_column(String(64))
    normalized_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

class OutboxStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Outbox(Base):
    __tablename__ = "outbox"
    __table_args__ = (Index("ix_outbox_status_created", "status", "created_at"),)

    id: Mapped[uuid.UUID] = PK()
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus, name="outbox_status"), default=OutboxStatus.PENDING
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Outbox id={self.id} event_type={self.event_type!r} "
            f"status={self.status.value} attempts={self.attempts}>"
        )