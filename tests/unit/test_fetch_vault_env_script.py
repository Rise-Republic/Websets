import unittest
from unittest.mock import MagicMock, patch

import fetch_vault_env as fve


class TestFetchVaultEnvScript(unittest.TestCase):
    @patch("fetch_vault_env.VaultClient")
    def test_main_outputs_env_lines(self, mock_vault_cls):
        mock_client = MagicMock()
        mock_vault_cls.return_value = mock_client
        mock_client.client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"A": "1", "B": "2"}}
        }

        with patch("fetch_vault_env.logger.info") as mock_info:
            fve.main()

        mock_info.assert_any_call("Fetched secret for A")
        mock_info.assert_any_call("Fetched secret for B")
