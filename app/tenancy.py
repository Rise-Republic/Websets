"""Tenant context and SQLAlchemy hooks for multi-tenancy."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Optional

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from app.database import Base


_current_tenant: ContextVar[Optional[uuid.UUID]] = ContextVar(
    "current_tenant", default=None
)


def set_current_tenant(tenant_id: Optional[uuid.UUID]) -> None:
    """Set the active tenant for the current context."""
    _current_tenant.set(tenant_id)


def get_current_tenant() -> Optional[uuid.UUID]:
    """Get the active tenant for the current context."""
    return _current_tenant.get()


@event.listens_for(Session, "do_orm_execute", propagate=True)
def _add_tenant_criteria(execute_state) -> None:
    tenant_id = _current_tenant.get()
    if (
        tenant_id
        and execute_state.is_select
        and not execute_state.execution_options.get("include_all_tenants")
    ):
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            if hasattr(cls, "tenant_id"):
                execute_state.statement = execute_state.statement.options(
                    with_loader_criteria(
                        cls,
                        lambda cls: cls.tenant_id == tenant_id,
                        include_aliases=True,
                    )
                )


@event.listens_for(Session, "before_flush", propagate=True)
def _set_tenant_on_new(session: Session, flush_context, instances) -> None:
    tenant_id = _current_tenant.get()
    if tenant_id is None:
        return
    for obj in session.new:
        if hasattr(obj, "tenant_id"):
            obj_tenant = getattr(obj, "tenant_id")
            if obj_tenant is None:
                setattr(obj, "tenant_id", tenant_id)
            elif obj_tenant != tenant_id:
                raise RuntimeError("Cross-tenant insert forbidden")
    for obj in session.dirty:
        if hasattr(obj, "tenant_id") and getattr(obj, "tenant_id") != tenant_id:
            raise RuntimeError("Cross-tenant update forbidden")
