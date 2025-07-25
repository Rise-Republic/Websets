#!/usr/bin/env python3
"""Seed a default user for local development."""

import os
import sys
import time
from loguru import logger
from pathlib import Path

# Set up logging to see what's happening
logger.remove()
logger.add(sys.stderr, level="DEBUG")

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Use direct imports to avoid any config loading issues
from sqlalchemy import create_engine, Column, Integer, String, Boolean, MetaData, Table, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Import password hashing function
from app.auth.jwt_handler import get_password_hash

# Define the User model directly to avoid importing from app.models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

def main() -> None:
    # Get environment variables with defaults
    email = os.environ.get("SEED_USER_EMAIL", "admin@example.com")
    password = os.environ.get("SEED_USER_PASSWORD", "admin")
    
    # HARDCODED database URL for Docker environment
    db_url = "postgresql://postgres:changeme@db:5432/webset_miner"
    
    logger.info(f"Connecting to database: {db_url}")
    
    # Wait for database to be available
    max_retries = 5
    retry_count = 0
    connected = False
    
    while not connected and retry_count < max_retries:
        try:
            # Create engine and test connection
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1")).fetchone()
            connected = True
            logger.info("Successfully connected to database")
        except Exception as e:
            retry_count += 1
            logger.error(f"Database connection attempt {retry_count} failed: {e}")
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("Maximum retries reached. Could not connect to database.")
                sys.exit(1)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            user = User(email=email, hashed_password=get_password_hash(password), is_superuser=True)
            db.add(user)
            db.commit()
            logger.info(f"Created default user: {email}")
        else:
            logger.info(f"User {email} already exists")
    except Exception as e:
        logger.error(f"Error seeding user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
