import io
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch
import unittest

from scripts.rotate_minio_secrets import main


class TestRotateMinioSecretsScript(unittest.TestCase):
    @patch("scripts.rotate_minio_secrets.VaultClient")
    def test_script_rotates_secrets(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_client.rotate_secret.side_effect = ["access", "secret"]
        mock_vault_cls.return_value = mock_client
        buf = io.StringIO()
        with redirect_stdout(buf):
            main()
        output = buf.getvalue()
        self.assertIn("MINIO_ACCESS_KEY=access", output)
        self.assertIn("MINIO_SECRET_KEY=secret", output)
        mock_client.rotate_secret.assert_any_call(
            "secret/websets", "MINIO_ACCESS_KEY", length=16
        )
        mock_client.rotate_secret.assert_any_call(
            "secret/websets", "MINIO_SECRET_KEY", length=32
        )


if __name__ == "__main__":
    unittest.main()
