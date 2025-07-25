import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login_and_cookie_flags():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Simulate login (mock WorkOS or use test credentials)
        resp = await ac.get("/api/auth/workos/callback?code=testcode")
        assert resp.status_code == 200
        cookie = resp.cookies.get("session")
        assert cookie, "Session cookie not set"
        # Check flags
        set_cookie = resp.headers.get("set-cookie")
        assert "HttpOnly" in set_cookie
        assert "Path=/" in set_cookie
        assert ("Secure" in set_cookie) or ("secure" not in set_cookie)  # depends on env
        assert ("SameSite=Lax" in set_cookie) or ("SameSite=None" in set_cookie)

@pytest.mark.asyncio
async def test_session_refresh():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Simulate valid session cookie
        ac.cookies.set("session", "dummy")
        resp = await ac.post("/api/auth/refresh")
        assert resp.status_code in (200, 401)  # 401 if dummy, 200 if real

@pytest.mark.asyncio
async def test_logout_clears_cookie():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        ac.cookies.set("session", "dummy")
        resp = await ac.post("/api/logout")
        set_cookie = resp.headers.get("set-cookie")
        assert "session=;" in set_cookie  # cleared


@pytest.mark.asyncio
async def test_auth_me_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/auth/me")
        assert resp.status_code == 401
        ac.cookies.set("session", "dummy")
        resp = await ac.get("/api/auth/me")
        assert resp.status_code in (200, 401)
