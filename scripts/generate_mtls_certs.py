#!/usr/bin/env python3
"""Generate a self-signed CA and service certificates for mTLS."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def write_key(path: Path, key: rsa.RSAPrivateKey) -> None:
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )


def write_cert(path: Path, cert: x509.Certificate) -> None:
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def generate_ca(cert_dir: Path) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "websets-ca")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    write_key(cert_dir / "ca.key", key)
    write_cert(cert_dir / "ca.crt", cert)
    return key, cert


def generate_service_cert(
    name: str, cert_dir: Path, ca_key: rsa.RSAPrivateKey, ca_cert: x509.Certificate
) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)]))
        .sign(key, hashes.SHA256())
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .sign(ca_key, hashes.SHA256())
    )
    write_key(cert_dir / f"{name}.key", key)
    write_cert(cert_dir / f"{name}.crt", cert)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mTLS certificates")
    parser.add_argument("cert_dir", nargs="?", default="certs", help="output directory")
    args = parser.parse_args()

    cert_dir = Path(args.cert_dir)
    cert_dir.mkdir(parents=True, exist_ok=True)

    ca_key, ca_cert = generate_ca(cert_dir)
    for svc in ["app", "minio", "vault", "redis", "qdrant", "weaviate"]:
        generate_service_cert(svc, cert_dir, ca_key, ca_cert)

    print(f"mTLS certificates generated in {cert_dir}")


if __name__ == "__main__":
    main()
