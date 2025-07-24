import subprocess
from pathlib import Path
import unittest


class TestGenerateMtlsCerts(unittest.TestCase):
    def test_script_creates_expected_files(self):
        tmp_dir = Path("tmp_certs")
        subprocess.run(
            ["python3", "scripts/generate_mtls_certs.py", str(tmp_dir)], check=True
        )

        expected = [
            "ca.crt",
            "ca.key",
            "app.crt",
            "app.key",
            "minio.crt",
            "minio.key",
            "vault.crt",
            "vault.key",
            "redis.crt",
            "redis.key",
            "qdrant.crt",
            "qdrant.key",
            "weaviate.crt",
            "weaviate.key",
        ]
        for name in expected:
            self.assertTrue((tmp_dir / name).exists(), f"missing {name}")

        # cleanup
        for f in tmp_dir.iterdir():
            f.unlink()
        tmp_dir.rmdir()
