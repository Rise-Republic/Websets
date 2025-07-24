import unittest
from pathlib import Path
import tempfile
from cryptography import x509

import scripts.generate_mtls_certs as gmc


class TestGenerateMtlsCertsScript(unittest.TestCase):
    def test_generate_creates_valid_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            gmc.generate(str(out))

            ca_crt = out / "ca.crt"
            ca_key = out / "ca.key"
            self.assertTrue(ca_crt.exists())
            self.assertTrue(ca_key.exists())
            ca = x509.load_pem_x509_certificate(ca_crt.read_bytes())

            for svc in gmc.SERVICES:
                crt = out / f"{svc}.crt"
                key = out / f"{svc}.key"
                self.assertTrue(crt.exists())
                self.assertTrue(key.exists())
                cert = x509.load_pem_x509_certificate(crt.read_bytes())
                self.assertEqual(cert.issuer, ca.subject)

    def test_main_prints_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with unittest.mock.patch("builtins.print") as mock_print:
                gmc.main([tmpdir])
            mock_print.assert_called_with(f"mTLS certificates generated in {tmpdir}")

