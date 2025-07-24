"""
HashiCorp Vault integration for secure secret management
"""
import os
import hvac


def _require_env(var: str) -> str:
    """Helper to fetch a required environment variable."""
    value = os.getenv(var)
    if not value:
        raise EnvironmentError(f"{var} environment variable is not set")
    return value

class VaultClient:
    """Simple wrapper around hvac.Client with extra helpers."""

    def __init__(self, url: str | None = None, token: str | None = None) -> None:
        self.url = url or _require_env("VAULT_ADDR")
        self.token = token or _require_env("VAULT_TOKEN")
        self.client = hvac.Client(url=self.url, token=self.token)

    def verify_secret_path(self, path: str) -> list[str]:
        """Ensure secrets exist at the given path and return their keys."""
        secret = self.client.secrets.kv.v2.read_secret_version(path=path)
        return list(secret["data"]["data"].keys())

    def get_secret(self, path: str, key: str) -> str | None:
        """Retrieve a secret from Vault at the given path and key."""
        secret = self.client.secrets.kv.v2.read_secret_version(path=path)
        return secret["data"]["data"].get(key)

    def fetch_all(self, path: str) -> dict[str, str]:
        """Return all secrets stored at the given path."""
        secret = self.client.secrets.kv.v2.read_secret_version(path=path)
        return secret["data"]["data"]

    def rotate_secret(self, path: str, key: str, length: int = 32) -> str:
        """Generate a new random secret, store it in Vault, and return it."""
        import secrets

        new_value = secrets.token_hex(length)
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path, secret={key: new_value}
        )
        return new_value


def cli_test_connection() -> None:
    """CLI helper to verify Vault connectivity and secret availability."""
    vault_path = os.getenv("VAULT_SECRET_PATH", "secret/websets")
    try:
        client = VaultClient()
        keys = client.verify_secret_path(vault_path)
        print(f"Vault OK at {client.url}. Secrets at '{vault_path}': {keys}")
    except Exception as exc:
        print(f"Vault connectivity test failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    cli_test_connection()

# Example usage:
# vault = VaultClient()
# db_password = vault.get_secret("secret/data/websets", "db_password")
