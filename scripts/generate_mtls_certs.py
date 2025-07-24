#!/usr/bin/env python3
"""Generate self-signed CA and service certificates for mTLS."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

SERVICES = [
    "app",
    "minio",
    "vault",
    "redis",
    "qdrant",
    "weaviate",
    "prometheus",
]


def _write_key(path: Path, key: rsa.RSAPrivateKey) -> None:
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    os.chmod(path, 0o600)


def _write_cert(path: Path, cert: x509.Certificate) -> None:
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def generate(cert_dir: str) -> None:
    """Generate CA and service certificates into ``cert_dir``."""
    out = Path(cert_dir)
    out.mkdir(parents=True, exist_ok=True)

    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    ca_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "websets-ca")])
    now = datetime.utcnow()
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_subject)
        .issuer_name(ca_subject)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    _write_key(out / "ca.key", ca_key)
    _write_cert(out / "ca.crt", ca_cert)

    for svc in SERVICES:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, svc)])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subj)
            .issuer_name(ca_cert.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=365))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )
            .sign(ca_key, hashes.SHA256())
        )
        _write_key(out / f"{svc}.key", key)
        _write_cert(out / f"{svc}.crt", cert)


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]
    cert_dir = os.getenv("CERT_DIR") or (args[0] if args else "certs")
    generate(cert_dir)
    print(f"mTLS certificates generated in {cert_dir}")


if __name__ == "__main__":
    main()
