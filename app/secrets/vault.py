"""
HashiCorp Vault integration for secure secret management
"""
import os
import hvac

class VaultClient:
    def __init__(self, url=None, token=None):
        self.url = url or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.client = hvac.Client(url=self.url, token=self.token)

    def get_secret(self, path, key):
        """Retrieve a secret from Vault at the given path and key."""
        secret = self.client.secrets.kv.v2.read_secret_version(path=path)
        return secret["data"]["data"].get(key)

# Example usage:
# vault = VaultClient()
# db_password = vault.get_secret("secret/data/websets", "db_password")
