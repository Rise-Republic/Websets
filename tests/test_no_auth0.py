import subprocess


def test_no_auth0():
    result = subprocess.run(
        ["grep", "-R", "-i", "auth0", "."], check=True, stdout=subprocess.PIPE
    )
    assert result.stdout == b""
