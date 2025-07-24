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

    @patch("app.tasks.secret_rotation.VaultClient")
    def test_rotate_database_password(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client

        result = secret_rotation.rotate_database_password()

        self.assertTrue(result)
        mock_client.rotate_secret.assert_called_with(
            secret_rotation.VAULT_PATH, "POSTGRES_PASSWORD", length=32
        )

    @patch("app.tasks.secret_rotation.VaultClient")
    def test_rotate_jwt_secret(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client

        result = secret_rotation.rotate_jwt_secret()

        self.assertTrue(result)
        mock_client.rotate_secret.assert_called_with(
            secret_rotation.VAULT_PATH, "JWT_SECRET_KEY", length=64
        )

    @patch("app.tasks.secret_rotation.VaultClient")
    def test_rotate_api_keys(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client

        result = secret_rotation.rotate_api_keys()

        self.assertTrue(result)
        mock_client.rotate_secret.assert_any_call(
            secret_rotation.VAULT_PATH, "OPENAI_API_KEY", length=48
        )
        mock_client.rotate_secret.assert_any_call(
            secret_rotation.VAULT_PATH, "ANTHROPIC_API_KEY", length=48
        )
