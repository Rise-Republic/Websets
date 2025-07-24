import pytest
from app.auth.auth0_utils import verify_auth0_token
from jose import jwt
from jose import jwk
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_auth0_token_valid(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    jwk_obj = jwk.construct(public_pem, algorithm="RS256")
    jwk_dict = jwk_obj.to_dict()
    jwk_dict["kid"] = "test"
    jwk_dict["use"] = "sig"

    token = jwt.encode(
        {"sub": "auth0|123", "aud": "test-aud", "iss": "https://demo/"},
        private_pem,
        algorithm="RS256",
        headers={"kid": "test"}
    )
    monkeypatch.setattr("app.config.settings.auth0_domain", "demo")
    monkeypatch.setattr("app.config.settings.auth0_audience", "test-aud")
    monkeypatch.setattr("app.config.settings.auth0_issuer", "https://demo/")
    async def fake_get(*args, **kwargs):
        class Resp:
            status_code = 200
            def json(self):
                return {"keys": [jwk_dict]}
            def raise_for_status(self):
                pass
        return Resp()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)

    payload = await verify_auth0_token(token)
    assert payload["sub"] == "auth0|123"
