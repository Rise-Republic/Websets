import unittest
from unittest.mock import MagicMock, patch

from app.secrets import vault


class TestVaultSecretRotation(unittest.TestCase):
    @patch("app.secrets.vault.hvac.Client")
    def test_rotate_secret(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        vc = vault.VaultClient(url="http://vault", token="t")

        new_value = vc.rotate_secret("secret/websets", "KEY", length=8)

        self.assertEqual(len(new_value), 16)
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_with(
            path="secret/websets", secret={"KEY": new_value}
        )

    @patch("app.secrets.vault.hvac.Client")
    def test_verify_secret_path_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"A": "1", "B": "2"}}
        }

        vc = vault.VaultClient(url="http://vault", token="t")
        keys = vc.verify_secret_path("secret/websets")

        self.assertEqual(set(keys), {"A", "B"})
        mock_client.secrets.kv.v2.read_secret_version.assert_called_with(
            path="secret/websets"
        )

    @patch("app.secrets.vault.hvac.Client")
    def test_get_secret_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"PASS": "secret-pass"}}
        }

        vc = vault.VaultClient(url="http://vault", token="t")
        value = vc.get_secret("secret/websets", "PASS")

        self.assertEqual(value, "secret-pass")
        mock_client.secrets.kv.v2.read_secret_version.assert_called_with(
            path="secret/websets"
        )

    @patch("app.secrets.vault.hvac.Client")
    def test_fetch_all(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"A": "1", "B": "2"}}
        }

        vc = vault.VaultClient(url="http://vault", token="t")
        all_data = vc.fetch_all("secret/websets")

        self.assertEqual(all_data, {"A": "1", "B": "2"})
        mock_client.secrets.kv.v2.read_secret_version.assert_called_with(
            path="secret/websets"
        )

    @patch("app.secrets.vault.hvac.Client")
    def test_cli_test_connection_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"A": "1"}}
        }

        with patch.dict(
            "os.environ",
            {
                "VAULT_ADDR": "http://vault",
                "VAULT_TOKEN": "t",
                "VAULT_SECRET_PATH": "secret/app",
            },
            clear=False,
        ):
            with patch("builtins.print") as mock_print:
                vault.cli_test_connection()

        mock_print.assert_called_with(
            "Vault OK at http://vault. Secrets at 'secret/app': ['A']"
        )

    @patch("app.secrets.vault.hvac.Client")
    def test_cli_test_connection_failure(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("boom")

        with patch.dict(
            "os.environ",
            {
                "VAULT_ADDR": "http://vault",
                "VAULT_TOKEN": "t",
                "VAULT_SECRET_PATH": "secret/app",
            },
            clear=False,
        ):
            with patch("builtins.print") as mock_print:
                with self.assertRaises(SystemExit):
                    vault.cli_test_connection()

        mock_print.assert_called_with("Vault connectivity test failed: boom")
