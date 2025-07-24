#!/usr/bin/env python3
"""
Command-line script to trigger a mining job.
Usage: python scripts/run_job.py "Your mining prompt here"
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Job, JobStatus, User
from app.tasks.mining_tasks import start_mining_job
from app.auth.jwt_handler import get_password_hash


def create_test_user_if_not_exists():
    """Create a test user if none exists."""
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            user = User(
                email="test@websetminer.com",
                hashed_password=get_password_hash("testpassword123"),
                full_name="Test User",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created test user: {user.email}")
        return user
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Run a WebSet Miner job")
    parser.add_argument("prompt", help="The mining prompt/query")
    parser.add_argument("--user-email", help="User email (optional)", default="test@websetminer.com")
    parser.add_argument("--sync", action="store_true", help="Run synchronously (blocking)")
    
    args = parser.parse_args()
    
    # Get or create user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.user_email).first()
        if not user:
            if args.user_email == "test@websetminer.com":
                user = create_test_user_if_not_exists()
            else:
                print(f"User {args.user_email} not found")
                return 1
        
        # Create job
        job = Job(
            user_id=user.id,
            prompt=args.prompt,
            status=JobStatus.PENDING
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        print(f"Created job {job.id} for user {user.email}")
        print(f"Prompt: {job.prompt}")
        
        if args.sync:
            # Run synchronously
            print("Running job synchronously...")
            # Note: This calls the actual function, not the Celery task
            result = start_mining_job(str(job.id))
            print(f"Job completed: {result}")
        else:
            # Queue with Celery
            print("Queuing job with Celery...")
            task = start_mining_job.delay(str(job.id))
            print(f"Task ID: {task.id}")
            print("Monitor job progress via API or logs")
        
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
