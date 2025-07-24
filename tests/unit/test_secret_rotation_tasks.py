import unittest
from unittest.mock import MagicMock, patch

from app.tasks import secret_rotation


class TestSecretRotationTasks(unittest.TestCase):
    @patch("app.tasks.secret_rotation.VaultClient")
    def test_rotate_minio_root_credentials(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client

        result = secret_rotation.rotate_minio_root_credentials()

        self.assertTrue(result)
        mock_client.rotate_secret.assert_any_call(
            secret_rotation.VAULT_PATH, "MINIO_ROOT_USER", length=16
        )
        mock_client.rotate_secret.assert_any_call(
            secret_rotation.VAULT_PATH, "MINIO_ROOT_PASSWORD", length=32
        )
