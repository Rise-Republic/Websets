import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_cross_tenant_data_leak():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login as org_id=1 (simulate)
        ac.cookies.set("session", "dummy-session-for-org1")
        # Try to access datasets for org_id=2
        resp = await ac.get("/v1/datasets", headers={"X-Org-ID": "2"})
        assert resp.status_code in (403, 401)

@pytest.mark.asyncio
async def test_super_admin_header_spoof():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Non-admin user tries to spoof X-Org-ID
        ac.cookies.set("session", "dummy-session-for-org2")
        resp = await ac.get("/v1/jobs", headers={"X-Org-ID": "1"})
        assert resp.status_code in (403, 401)

@pytest.mark.asyncio
async def test_orphaned_session_revoked():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Simulate org_id change after login
        ac.cookies.set("session", "dummy-orphaned-session")
        resp = await ac.get("/v1/datasets")
        assert resp.status_code in (401, 403)
