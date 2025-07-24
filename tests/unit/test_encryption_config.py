import yaml
import pytest


@pytest.mark.unit
def test_encryption_config_in_docker_compose():
    with open("docker-compose.yml") as f:
        compose = yaml.safe_load(f)

    db_env = compose["services"]["db"]["environment"]
    if isinstance(db_env, list):
        db_keys = [item.split("=")[0] for item in db_env]
    else:
        db_keys = list(db_env.keys())
    assert "POSTGRES_ENCRYPTION_KEY_FILE" in db_keys

    minio_env = compose["services"]["minio"]["environment"]
    if isinstance(minio_env, list):
        minio_keys = [item.split("=")[0] for item in minio_env]
    else:
        minio_keys = list(minio_env.keys())
    assert "MINIO_KMS_SECRET_KEY_FILE" in minio_keys
    assert "MINIO_SSE_MASTER_KEY" in minio_keys
