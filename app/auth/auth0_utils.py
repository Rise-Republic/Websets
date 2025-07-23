from datetime import datetime, timedelta
from typing import Any, Dict
import httpx
from jose import jwt
from jose.exceptions import JWTError
from app.config import settings

_jwks_cache: Dict[str, Any] = {
    "keys": None,
    "fetched": datetime.min,
}

async def get_jwks():
    if _jwks_cache["keys"] and datetime.utcnow() - _jwks_cache["fetched"] < timedelta(hours=12):
        return _jwks_cache["keys"]
    url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    _jwks_cache["keys"] = data["keys"]
    _jwks_cache["fetched"] = datetime.utcnow()
    return _jwks_cache["keys"]

async def verify_auth0_token(token: str) -> Dict[str, Any]:
    jwks = await get_jwks()
    unverified = jwt.get_unverified_header(token)
    rsa_key = None
    for key in jwks:
        if key["kid"] == unverified["kid"]:
            rsa_key = {k: key[k] for k in ["kty", "kid", "use", "n", "e"]}
            break
    if rsa_key is None:
        raise JWTError("Unable to find appropriate key")
    payload = jwt.decode(
        token,
        rsa_key,
        algorithms=["RS256"],
        audience=settings.auth0_audience,
        issuer=settings.auth0_issuer,
    )
    return payload
