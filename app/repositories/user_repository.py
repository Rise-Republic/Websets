from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    """Data access layer for ``User`` objects."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_verification_token(self, token_hash: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.verification_token == token_hash)
            .first()
        )

    def get_by_password_reset_token(self, token_hash: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.password_reset_token == token_hash)
            .first()
        )

    def get_by_refresh_token(self, token_hash: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.refresh_token == token_hash)
            .first()
        )

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, user: User) -> None:
        self.db.refresh(user)
