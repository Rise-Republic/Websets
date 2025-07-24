"""Database setup and session helpers."""

from typing import Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
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
