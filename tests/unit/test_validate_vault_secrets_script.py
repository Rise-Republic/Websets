import unittest
from unittest.mock import MagicMock, patch, mock_open

import scripts.validate_vault_secrets as vvs


class TestValidateVaultSecretsScript(unittest.TestCase):
    @patch("scripts.validate_vault_secrets.VaultClient")
    def test_main_success(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client
        mock_client.get_secret.return_value = "val"
        data = '{"A": "x", "B": "y"}'
        with patch("scripts.validate_vault_secrets.open", mock_open(read_data=data)):
            with patch("scripts.validate_vault_secrets.print") as mock_print:
                vvs.main()
        mock_print.assert_called_with("All required secrets are present in Vault.")
        self.assertEqual(mock_client.get_secret.call_count, 2)

    @patch("scripts.validate_vault_secrets.VaultClient")
    def test_main_missing(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client
        mock_client.get_secret.side_effect = ["1", None]
        data = '{"A": "x", "B": "y"}'
        with patch("scripts.validate_vault_secrets.open", mock_open(read_data=data)):
            with patch("scripts.validate_vault_secrets.print") as mock_print:
                with self.assertRaises(SystemExit):
                    vvs.main()
        mock_print.assert_any_call("Missing or empty secrets in 'secret/websets': B")
