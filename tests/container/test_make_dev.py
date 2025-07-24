import json
import os
import subprocess
import time
import shutil

import pytest

@pytest.mark.integration
@pytest.mark.skipif(shutil.which("docker") is None, reason="Docker not available")
def test_make_dev_starts_all_services(tmp_path):
    """Run `make dev` and verify all services become healthy."""
    env = os.environ.copy()
    env.setdefault("SEED_USER_EMAIL", "test@example.com")
    env.setdefault("SEED_USER_PASSWORD", "changeme123!")

    subprocess.run(["make", "dev"], check=True, env=env)

    ps = subprocess.check_output(["docker", "compose", "ps", "--format", "json"], text=True)
    services = json.loads(ps)

    for svc in services:
        name = svc["Name"]
        for _ in range(60):
            status = subprocess.check_output(
                ["docker", "inspect", "-f", "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}", name],
                text=True,
            ).strip()
            if status == "healthy" or status == "running":
                break
            time.sleep(5)
        assert status == "healthy" or status == "running", f"{name} unhealthy"
