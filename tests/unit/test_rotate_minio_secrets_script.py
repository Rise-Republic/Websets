import unittest
from unittest.mock import MagicMock, patch

import scripts.rotate_minio_secrets as rms


class TestRotateMinioSecretsScript(unittest.TestCase):
    @patch('scripts.rotate_minio_secrets.VaultClient')
    def test_rotate_minio(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client
        mock_client.rotate_secret.side_effect = ["a1", "b2"]

        access, secret = rms.rotate_minio()

        self.assertEqual(access, "a1")
        self.assertEqual(secret, "b2")
        mock_client.rotate_secret.assert_any_call('secret/websets', 'MINIO_ACCESS_KEY', length=16)
        mock_client.rotate_secret.assert_any_call('secret/websets', 'MINIO_SECRET_KEY', length=32)

    @patch('scripts.rotate_minio_secrets.print')
    @patch('scripts.rotate_minio_secrets.VaultClient')
    def test_main_outputs(self, mock_vault_cls, mock_print):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client
        mock_client.rotate_secret.side_effect = ["x1", "y2"]

        rms.main()

        mock_print.assert_any_call("export MINIO_ACCESS_KEY=x1")
        mock_print.assert_any_call("export MINIO_SECRET_KEY=y2")
