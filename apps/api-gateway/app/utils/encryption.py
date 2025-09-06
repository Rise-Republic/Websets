import base64
import os
import hashlib
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.types import TypeDecorator, String, Text

# Prefix used to mark encrypted values so we don't double encrypt
_PREFIX = "enc:"

# Load key from environment or use a deterministic fallback for tests
_default_key = base64.urlsafe_b64encode(b"0" * 32).decode()
_key_b64 = os.getenv("ENCRYPTION_KEY", _default_key)
_ENCRYPTION_KEY = base64.urlsafe_b64decode(_key_b64)


def _deterministic_nonce(data: bytes) -> bytes:
    """Return a deterministic nonce based on the data."""
    return hashlib.sha256(data).digest()[:12]


def encrypt(value: str) -> str:
    """Encrypt a string using AES-GCM with a deterministic nonce."""
    if value is None:
        return value
    if value.startswith(_PREFIX):
        return value
    data = value.encode("utf-8")
    nonce = _deterministic_nonce(data)
    aesgcm = AESGCM(_ENCRYPTION_KEY)
    ct = aesgcm.encrypt(nonce, data, None)
    return _PREFIX + base64.urlsafe_b64encode(nonce + ct).decode("utf-8")


def decrypt(value: str) -> str:
    """Decrypt a value produced by :func:`encrypt`."""
    if value is None:
        return value
    if not value.startswith(_PREFIX):
        return value
    raw = base64.urlsafe_b64decode(value[len(_PREFIX) :])
    nonce = raw[:12]
    ct = raw[12:]
    aesgcm = AESGCM(_ENCRYPTION_KEY)
    data = aesgcm.decrypt(nonce, ct, None)
    return data.decode("utf-8")


class _EncryptedType(TypeDecorator):
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect):
        if value is None:
            return value
        return encrypt(value)

    def process_result_value(self, value: Optional[str], dialect):
        if value is None:
            return value
        return decrypt(value)


class EncryptedString(_EncryptedType):
    impl = String

    def __init__(self, length: Optional[int] = None, **kwargs):
        super().__init__(length=length, **kwargs)


class EncryptedText(_EncryptedType):
    impl = Text
