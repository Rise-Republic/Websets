#!/usr/bin/env python3
"""Seed a Vault instance with secrets from vault_secrets_template.json."""
import os
import json
import time
import hvac

addr = os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
token = os.environ.get("VAULT_TOKEN", "root")
path = os.environ.get("VAULT_SECRET_PATH", "secret/websets")

client = hvac.Client(url=addr, token=token)
for _ in range(10):
    try:
        if client.is_authenticated():
            break
    except Exception:
        pass
    time.sleep(1)
else:
    raise RuntimeError("Vault did not start")

with open("vault_secrets_template.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)

if "/" in path:
    mount, secret_path = path.split("/", 1)
else:
    mount, secret_path = "secret", path

client.secrets.kv.v2.create_or_update_secret(
    mount_point=mount,
    path=secret_path,
    secret=secrets,
)
print(f"Seeded Vault secrets at {mount}/{secret_path}")
