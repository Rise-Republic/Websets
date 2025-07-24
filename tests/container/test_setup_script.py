import os
import subprocess
from pathlib import Path

import pytest

@pytest.mark.integration
def test_setup_script_creates_required_files(tmp_path):
    env = os.environ.copy()
    cwd = tmp_path
    # Copy repo files into tmp path to avoid modifying repo
    subprocess.run(['cp', '-r', '.', str(cwd)], check=True)
    os.chdir(cwd)

    subprocess.run(['bash', 'scripts/setup.sh'], check=True, env=env)

    assert Path('.env').exists()
    assert Path('data').is_dir()
    assert Path('certs').is_dir()
