import unittest
from unittest.mock import MagicMock, patch

import fetch_vault_env as fve


class TestFetchVaultEnvScript(unittest.TestCase):
    @patch("fetch_vault_env.VaultClient")
    def test_main_outputs_env_lines(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client
        mock_client.fetch_all.return_value = {"A": "1", "B": "2"}

        with patch("builtins.print") as mock_print:
            fve.main()

        mock_client.fetch_all.assert_called_with("secret/websets")
        mock_print.assert_any_call("A=1")
        mock_print.assert_any_call("B=2")

