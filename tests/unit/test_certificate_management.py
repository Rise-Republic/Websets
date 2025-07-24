import unittest
from pathlib import Path
import subprocess

from app.tasks import cert_management


class TestCertificateManagement(unittest.TestCase):
    def test_check_certificate_expiration_detects_near_expiry(self):
        tmp_dir = Path("/tmp/testcerts")
        tmp_dir.mkdir(exist_ok=True)
        crt = tmp_dir / "temp.crt"
        key = tmp_dir / "temp.key"
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-days",
                "1",
                "-nodes",
                "-keyout",
                str(key),
                "-out",
                str(crt),
                "-subj",
                "/CN=temp",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        result = cert_management._check(str(tmp_dir), warn_days=2)
        self.assertIn("temp.crt", result)
        crt.unlink()
        key.unlink()
        tmp_dir.rmdir()
