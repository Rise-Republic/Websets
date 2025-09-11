"""Database setup and session helpers."""

from typing import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings
from app.tenancy import get_current_tenant

# Convert async database URL to sync for SQLAlchemy operations
import os

# Check if we're running in Docker environment and force the correct database URL
if os.environ.get("DOCKER_ENV") == "true" or os.path.exists("/.dockerenv"):
    # We're in Docker, use the container hostname
    import re
    # Replace localhost or 127.0.0.1 with 'db' in the database URL
    docker_db_url = re.sub(
        r'postgresql(\+[a-z]+)?://([^:]+):([^@]+)@(localhost|127\.0\.0\.1)([:/])',
        r'postgresql\1://\2:\3@db\5',
        settings.database_url,
    )
    sync_database_url = docker_db_url.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )
    print(f"Docker environment detected, using database URL: {sync_database_url}")
else:
    # Not in Docker, use the settings as is
    sync_database_url = settings.database_url.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )

engine = create_engine(sync_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=Session
)

Base = declarative_base()
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """Yield a transactional database session scoped to the current tenant."""
    db = SessionLocal()
    tenant_id = get_current_tenant()
    if tenant_id:
        # Ensure PostgreSQL RLS policy uses tenant context
        db.execute(text("SET app.current_tenant = :tenant"), {"tenant": str(tenant_id)})
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
