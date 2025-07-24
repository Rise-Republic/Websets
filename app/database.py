"""Database setup and session helpers."""

from typing import Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

# Convert async database URL to sync for SQLAlchemy operations
sync_database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
engine = create_engine(sync_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=Session
)

Base = declarative_base()
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """Yield a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
