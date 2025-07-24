from typing import Optional, Mapping

from app.auth.jwt_handler import verify_token


def get_email_from_authorization_header(headers: Mapping[str, str]) -> Optional[str]:
    """Return user email from Authorization header if token is valid."""
    authorization = headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    return verify_token(token)
