import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add app path to allow importing config
# This is a common pattern in testing to resolve module paths.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'app')))

class TestConfigLoading(unittest.TestCase):

    def setUp(self):
        """Backup and clear relevant environment variables before each test."""
        self.backup_environ = os.environ.copy()
        # Unload the config module to ensure it's re-evaluated in each test
        if 'app.config' in sys.modules:
            del sys.modules['app.config']
        if 'app.secrets.vault' in sys.modules:
            del sys.modules['app.secrets.vault']

    def tearDown(self):
        """Restore environment variables after each test."""
        os.environ.clear()
        os.environ.update(self.backup_environ)
        # Unload the config module to ensure it's re-evaluated in each test
        if 'app.config' in sys.modules:
            del sys.modules['app.config']
        if 'app.secrets.vault' in sys.modules:
            del sys.modules['app.secrets.vault']

    @patch('app.secrets.vault.hvac.Client')
    def test_load_secrets_from_vault_success(self, mock_hvac_client):
        """Test that secrets are loaded from Vault when configured."""
        # Arrange
        mock_vault_instance = MagicMock()
        mock_vault_instance.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {
                    'OPENAI_API_KEY': 'vault_openai_key',
                    'DATABASE_URL': 'vault_db_url',
                    'JWT_SECRET_KEY': 'a-very-secure-jwt-secret-key-from-vault',
                    'REDIS_URL': 'redis://localhost:6379',
                    'CELERY_BROKER_URL': 'redis://localhost:6379',
                    'CELERY_RESULT_BACKEND': 'redis://localhost:6379'
                }
            }
        }
        mock_hvac_client.return_value = mock_vault_instance

        os.environ['VAULT_ADDR'] = 'http://fake-vault:8200'
        os.environ['VAULT_TOKEN'] = 'fake-token'

        # Act
        from app.config import settings

        # Assert
        self.assertEqual(settings.openai_api_key, 'vault_openai_key')
        self.assertEqual(settings.database_url, 'vault_db_url')
        self.assertEqual(settings.jwt_secret_key, 'a-very-secure-jwt-secret-key-from-vault')
        mock_hvac_client.assert_called_with(url='http://fake-vault:8200', token='fake-token')

    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'env-openai',
        'DATABASE_URL': 'env-db-url',
        'JWT_SECRET_KEY': 'a-very-secure-jwt-key-from-env',
    }, clear=True)
    def test_missing_vault_config_uses_env(self):
        """Should fall back to environment variables when Vault config missing."""
        from app.config import validate_settings
        settings = validate_settings()
        self.assertEqual(settings.openai_api_key, 'env-openai')
        self.assertEqual(settings.database_url, 'env-db-url')
        self.assertEqual(settings.jwt_secret_key, 'a-very-secure-jwt-key-from-env')

    @patch('app.secrets.vault.hvac.Client')
    def test_vault_connection_failure_falls_back(self, mock_hvac_client):
        """Should use env vars if Vault connection fails."""
        mock_hvac_client.side_effect = Exception("Vault connection failed")
        os.environ['VAULT_ADDR'] = 'http://fake-vault:8200'
        os.environ['VAULT_TOKEN'] = 'fake-token'
        os.environ['OPENAI_API_KEY'] = 'env-openai'
        os.environ['DATABASE_URL'] = 'env-db-url'
        os.environ['JWT_SECRET_KEY'] = 'a-very-secure-jwt-key-from-env'

        from app.config import validate_settings
        settings = validate_settings()
        self.assertEqual(settings.openai_api_key, 'env-openai')
        self.assertEqual(settings.database_url, 'env-db-url')
        self.assertEqual(settings.jwt_secret_key, 'a-very-secure-jwt-key-from-env')

if __name__ == '__main__':
    unittest.main()
