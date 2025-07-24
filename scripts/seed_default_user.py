#!/usr/bin/env python3
"""Seed a default user for local development."""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import User
from app.auth.jwt_handler import get_password_hash


def main() -> None:
    email = os.environ["SEED_USER_EMAIL"]
    password = os.environ["SEED_USER_PASSWORD"]

    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            user = User(email=email, hashed_password=get_password_hash(password))
            db.add(user)
            db.commit()
            print(f"Created default user {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
