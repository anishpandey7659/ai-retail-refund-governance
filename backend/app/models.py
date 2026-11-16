from sqlalchemy import ( BigInteger,Boolean,CheckConstraint,DateTime,ForeignKey,Index,Integer,Numeric,UniqueConstraint,
                        String,Text,func,text,Enum,Float)
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
    name:Mapped[str]=mapped_column(String(64),unique=True) 


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
    
    def __repr__(self) -> str:
        return (
            f"<Product id={self.id} name={self.name!r} "
            f"category={self.category!r} price={self.price} stock={self.stock}>"
        )

class Order(Base,TS):
    __tablename__ = "orders"

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

    __table_args__ = (
        CheckConstraint("total_amount > 0", name="check_price_positive"),
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} user_id={self.user_id} status={self.status!r}>"


class OrderItem(Base,TS):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    name_at_purchase: Mapped[str] = mapped_column(String(255))

    order: Mapped["Order"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return (
            f"<OrderItem id={self.id} order_id={self.order_id} "
            f"product_id={self.product_id} qty={self.quantity}>"
        )


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

class ReturnStatus(str, enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    ESCALATED = "escalated"
    APPROVED = "approved"
    DENIED = "denied"
    REFUNDED = "refunded"


class Return(Base, TS):
    __tablename__ = "returns"

    id: Mapped[uuid.UUID] = PK()
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)

    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"),index=True,)

    reason_text: Mapped[str] = mapped_column(Text, nullable=False)
    reason_code: Mapped[str] = mapped_column(String(32), nullable=False)
    review_attempts: Mapped[int] = mapped_column(Integer, server_default="0", default=0)

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    status: Mapped[ReturnStatus] = mapped_column(
        Enum(ReturnStatus, name="return_status"),   
        default=ReturnStatus.PENDING,
        index=True,
    )
    ai_proposed_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    final_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)

    claimed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_runs.id"), nullable=True
    )

    photos: Mapped[list["ReturnPhoto"]] = relationship(
        back_populates="return_", cascade="all, delete-orphan"
    )
    inspection: Mapped["ReturnInspection | None"] = relationship(
        back_populates="return_", cascade="all, delete-orphan", uselist=False
    )
    refunds: Mapped[list["ReturnRefund"]] = relationship(back_populates="return_")
    __table_args__ = (
        CheckConstraint(
            "reason_code IN ('damaged', 'not_as_described','quality',"
            "'wrong_item', 'no_longer_needed', 'defective','arrived_late',"
            "'wrong_size','item_not_received','duplicate_item','accidental_order')",
            name="ck_returns_reason_code",
        ),
        CheckConstraint(
        "final_decision IS NULL OR final_decision IN ('approve', 'deny', 'in_review')",
        name="ck_returns_final_decision",
    ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Return id={self.id} order_id={self.order_id} item_id={self.order_item_id}"
            f"status={self.status.value} amount={self.amount}>"
        )


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

    def __repr__(self) -> str:
        return (
            f"<ReturnPhoto id={self.id} return_id={self.return_id} "
        )


class ReturnInspection(Base):
    """One optional inspection per return; nullable values represent unknown facts."""

    __tablename__ = "return_inspections"

    id: Mapped[uuid.UUID] = PK()
    return_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("returns.id"), unique=True
    )
    item_received: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    item_opened: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    inspected_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    inspected_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recorded_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    return_: Mapped["Return"] = relationship(back_populates="inspection")


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ReturnRefund(Base):
    __tablename__ = "return_refunds"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_return_refunds_amount_positive"),
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')",
            name="ck_return_refunds_status",
        ),
    )

    id: Mapped[uuid.UUID] = PK()
    return_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("returns.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(
        String(20),
        default=RefundStatus.PENDING.value,
        server_default=text("'pending'"),
    )
    destination_fingerprint: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Keyed fingerprint for comparison; never raw payment data",
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

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

# ------------------------- Rule & dials (The policy) -----------------------------------------------

class PolicyDoc(Base):
    __tablename__ = "policy_docs"

    id: Mapped[uuid.UUID] = PK()
    version: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(200))
    content_markdown: Mapped[str] = mapped_column(Text)
    return_window_days: Mapped[int] = mapped_column(Integer, default=30)
    category_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    evidence_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    effective_from: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<PolicyDoc id={self.id} version={self.version} "
            f"title={self.title!r} active={self.is_active}>"
        )


# ------------------------- The AI's work(how each decision was made) -----------------------------------------------

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = PK()
    return_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("returns.id"), index=True)

    agent_name: Mapped[str] = mapped_column(String(100), index=True)
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50))
    policy_version: Mapped[int] = mapped_column(Integer)
    input_hash: Mapped[str] = mapped_column(String(64), index=True)  # e.g. SHA-256 hex

    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    langfuse_trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    events: Mapped[list["AgentRunEvent"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AgentRunEvent.created_at",
    )

    def __repr__(self) -> str:
        return (
            f"<AgentRun id={self.id} return_id={self.return_id} "
            f"agent={self.agent_name!r} model={self.model!r} "
            f"confidence={self.confidence}>"
        )


class AgentRunEvent(Base):
    __tablename__ = "agent_run_events"
    __table_args__ = (Index("ix_agent_run_events_run_created", "run_id", "created_at"),)

    id: Mapped[uuid.UUID] = PK()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runs.id"), index=True)

    event_type: Mapped[str] = mapped_column(String(50), index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    run: Mapped["AgentRun"] = relationship(back_populates="events")

    def __repr__(self) -> str:
        return (
            f"<AgentRunEvent id={self.id} run_id={self.run_id} "
            f"type={self.event_type!r}>"
        )



# ───────────────────────── Safety net ─────────────────────────────────────────────────────────────────────────

class ActorType(str, enum.Enum):
    AI = "ai"
    HUMAN = "human"


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_entity", "entity_type", "entity_id"),)

    id: Mapped[uuid.UUID] = PK()
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # None for the first row
    action: Mapped[str] = mapped_column(String(100), index=True)
    actor_type: Mapped[ActorType] = mapped_column(Enum(ActorType, name="actor_type"))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50))   # "return", "policy", ...
    entity_id: Mapped[uuid.UUID] = mapped_column()          # no FK: it can point at any table
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    hash: Mapped[str] = mapped_column(String(64), unique=True)  # SHA-256 hex

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action!r} "
            f"entity={self.entity_type}:{self.entity_id}>"
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


class DeadLetter(Base):
    __tablename__ = "dead_letter"

    id: Mapped[uuid.UUID] = PK()
    return_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("returns.id"), index=True)
    error_message: Mapped[str] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)  # open | resolved
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<DeadLetter id={self.id} return_id={self.return_id} "
            f"attempts={self.attempts} status={self.status!r}>"
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

    def __repr__(self) -> str:
        return (
            f"<Fingerprint id={self.id} user_id={self.user_id} "
            f"type={self.fingerprint_type.value}>"
        )


# ───────────────────────── ML ─────────────────────────────────────────────────────────────────────────────────

class ModelType(str, enum.Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_name_version"),
        # at most one active version per model name
        Index(
            "uq_one_active_model_version",
            "model_name",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[uuid.UUID] = PK()
    model_name: Mapped[str] = mapped_column(String(100), index=True)
    version: Mapped[str] = mapped_column(String(50))
    model_type: Mapped[ModelType] = mapped_column(Enum(ModelType, name="model_type"))
    training_data_period: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    artifact_uri: Mapped[str] = mapped_column(String(500))  # MinIO location
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ModelRegistry id={self.id} name={self.model_name!r} "
            f"version={self.version!r} active={self.is_active}>"
        )


# ───────────────────────── Workflow ─────────────────────────────────────────────────────────────────────────

class AppealStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class Appeal(Base, TS):
    """
    When a return is denied, the customer can appeal, 
    Stores their reason, who originally denied it, and the (different) reviewer it's handed to for a fresh look.
    """

    __tablename__ = "appeals"
    __table_args__ = (
        CheckConstraint(
            "original_reviewer_id IS DISTINCT FROM assigned_reviewer_id",
            name="ck_appeal_different_reviewer",
        ),
    )

    id: Mapped[uuid.UUID] = PK()
    return_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("returns.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    original_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    assigned_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[AppealStatus] = mapped_column(
        Enum(AppealStatus, name="appeal_status"), default=AppealStatus.PENDING, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<Appeal id={self.id} return_id={self.return_id} "
            f"status={self.status.value}>"
        )


class InfoRequestTarget(str, enum.Enum):
    CUSTOMER = "customer"
    STAFF = "staff"


class InfoRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ANSWERED = "answered"


class InfoRequest(Base, TS):
    """
    When a reviewer needs more information from the customer (eg: "send the photo of the serial number "),
    all these detail are stored here
    """

    __tablename__ = "info_requests"

    id: Mapped[uuid.UUID] = PK()
    return_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("returns.id"), index=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    requested_from: Mapped[InfoRequestTarget] = mapped_column(
        Enum(InfoRequestTarget, name="info_request_target")
    )
    question: Mapped[str] = mapped_column(Text)

    status: Mapped[InfoRequestStatus] = mapped_column(
        Enum(InfoRequestStatus, name="info_request_status"),
        default=InfoRequestStatus.PENDING,
        index=True,
    )
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<InfoRequest id={self.id} return_id={self.return_id} "
            f"from={self.requested_from.value} status={self.status.value}>"
        )