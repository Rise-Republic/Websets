import unittest
from unittest.mock import MagicMock, patch

from app.secrets import vault

class TestVaultSecretRotation(unittest.TestCase):
    @patch('app.secrets.vault.hvac.Client')
    def test_rotate_secret(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        vc = vault.VaultClient(url='http://vault', token='t')

        new_value = vc.rotate_secret('secret/websets', 'KEY', length=8)

        self.assertEqual(len(new_value), 16)
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_with(
            path='secret/websets', secret={'KEY': new_value}
        )
