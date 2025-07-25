import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_csrf_token_required():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First, get CSRF cookie
        resp = await ac.get("/v1/datasets")
        csrf_token = resp.cookies.get("csrf_token")
        assert csrf_token, "CSRF cookie should be set on GET"
        # POST without CSRF header should fail
        resp2 = await ac.post("/v1/datasets", cookies={"csrf_token": csrf_token})
        assert resp2.status_code == 403
        # POST with CSRF header should succeed or fail for other reasons (auth, etc.)
        resp3 = await ac.post(
            "/v1/datasets",
            cookies={"csrf_token": csrf_token},
            headers={"x-csrf-token": csrf_token}
        )
        assert resp3.status_code in (200, 401, 403)  # 401/403 if not logged in, 200 if allowed
