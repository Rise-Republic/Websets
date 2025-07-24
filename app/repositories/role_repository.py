from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models import Role


class RoleRepository:
    """Data access layer for ``Role`` objects."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_name(self, name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == name).first()

    def add(self, role: Role) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def commit(self) -> None:
        self.db.commit()
