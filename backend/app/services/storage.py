import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.app.models import Base
from backend.app.config import PostgreSQLSettings,settings

import boto3
from botocore.client import Config as BotoConfig



logger = logging.getLogger(__name__)


# asyncpg runs one statement per call, so these are kept as separate strings.
AUDIT_STATEMENTS = [
    """
    CREATE OR REPLACE FUNCTION forbid_audit_change() RETURNS trigger AS $$
    BEGIN
        RAISE EXCEPTION 'audit_log is append-only';
    END;
    $$ LANGUAGE plpgsql;
    """,
    "DROP TRIGGER IF EXISTS audit_log_append_only ON audit_log;",
    """
    CREATE TRIGGER audit_log_append_only
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION forbid_audit_change();
    """,
]


def _prepare_url(raw_url: str) -> tuple[str, dict]:
    """Make the URL asyncpg-friendly.

    - Forces the postgresql+asyncpg:// driver.
    - asyncpg does not understand `sslmode=...` in the URL, so it is removed
      and turned into asyncpg's `ssl` connect argument instead.
    """
    url = make_url(raw_url)

    if url.drivername in ("postgresql", "postgres", "postgresql+psycopg2"):
        url = url.set(drivername="postgresql+asyncpg")

    connect_args: dict = {}
    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    if sslmode in ("require", "verify-ca", "verify-full"):
        connect_args["ssl"] = "require"
    elif "neon.tech" in (url.host or ""):
        connect_args["ssl"] = "require"

    url = url.set(query=query)
    return url.render_as_string(hide_password=False), connect_args


class PostgreSQLDatabase():
    """Async PostgreSQL database implementation."""

    def __init__(self, config:PostgreSQLSettings):
        self.config = config
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def startup(self) -> None:
        """Connect, create missing tables, and install the audit_log trigger."""
        try:
            url, connect_args = _prepare_url(self.config.database_url)

            safe_target = url.split("@")[1] if "@" in url else "localhost"
            logger.info(f"Attempting to connect to PostgreSQL at: {safe_target}")

            self.engine = create_async_engine(
                url,
                echo=self.config.echo_sql,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_pre_ping=True,
                connect_args=connect_args,
            )

            self.session_factory = async_sessionmaker(
                bind=self.engine,
                expire_on_commit=False,  # keep attributes readable after commit
            )

            # Test the connection
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")

            # Create tables (idempotent) and compare before/after
            async with self.engine.begin() as conn:
                existing = set(
                    await conn.run_sync(
                        lambda sync_conn: inspect(sync_conn).get_table_names()
                    )
                )

                await conn.run_sync(Base.metadata.create_all)

                # Fresh inspector (the earlier one caches its results)
                updated = set(
                    await conn.run_sync(
                        lambda sync_conn: inspect(sync_conn).get_table_names()
                    )
                )

                # audit_log is append-only: block UPDATE and DELETE at DB level
                for statement in AUDIT_STATEMENTS:
                    await conn.execute(text(statement))

            new_tables = updated - existing
            if new_tables:
                logger.info(f"Created new tables: {', '.join(sorted(new_tables))}")
            else:
                logger.info("All tables already exist - no new tables created")

            logger.info("PostgreSQL database initialized successfully")
            logger.info(f"Database: {self.engine.url.database}")
            logger.info(
                f"Total tables: {', '.join(sorted(updated)) if updated else 'None'}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL database: {e}")
            raise

    async def health_check(self) -> bool:
        """Return True if the database is reachable. Never raises."""
        if not self.engine:
            logger.warning("Health check failed: database not initialized")
            return False

        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def teardown(self) -> None:
        """Close all pooled connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("PostgreSQL database connections closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Use as: `async with db.get_session() as session:`"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call await startup() first.")

        session = self.session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


from functools import lru_cache

@lru_cache(maxsize=1)
def get_postgresql_db() -> PostgreSQLDatabase:
    return PostgreSQLDatabase(config=PostgreSQLSettings())


# ───────────────────────── MINIO (S3 bucket for image )─────────────────────────────────────────────────────────────────────────

_PUBLIC_ENDPOINT = "http://localhost:9000"
_cfg = BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"})


def _client(endpoint: str | None = None):
    return boto3.client(
        "s3",
        endpoint_url=endpoint or settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=_cfg,
        region_name="auto",
    )


def put_bytes(key: str, data: bytes, content_type: str) -> None:
    _client().put_object(
        Bucket=settings.minio_bucket_name, Key=key, Body=data, ContentType=content_type
    )

def delete_object(key: str) -> None:
    _client().delete_object(Bucket=settings.minio_bucket_name, Key=key)


def presigned_get(key: str, expires: int = 3600) -> str:
    return _client(_PUBLIC_ENDPOINT).generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket_name, "Key": key},
        ExpiresIn=expires,
    )


def exists(key: str) -> bool:
    try:
        _client().head_object(Bucket=settings.minio_bucket_name, Key=key)
        return True
    except Exception:
        return False