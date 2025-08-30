import os
import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

pytestmark = pytest.mark.skipif(
    "postgresql" not in os.getenv("DATABASE_URL", ""),
    reason="Requires PostgreSQL with RLS enabled",
)


def test_rls_prevents_cross_tenant_access():
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(text("SET app.current_tenant = :t"), {"t": tenant_a})
        conn.execute(text("INSERT INTO datasets (id, tenant_id, name) VALUES (:id, :tenant, 'demo')"), {"id": str(uuid.uuid4()), "tenant": tenant_a})
    with engine.begin() as conn:
        conn.execute(text("SET app.current_tenant = :t"), {"t": tenant_b})
        rows = conn.execute(text("SELECT count(*) FROM datasets")).scalar()
        assert rows == 0
