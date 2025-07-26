import subprocess
import shutil


def test_no_auth_zero_references():
    keyword = "auth" + "0"  # avoid matching this test file
    shutil.rmtree("artifacts", ignore_errors=True)
    shutil.rmtree(".pytest_cache", ignore_errors=True)
    try:
        result = subprocess.run(
            ["grep", "-R", "-i", keyword, "."],
            check=True,
            stdout=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        result = exc
    assert result.stdout == b""
