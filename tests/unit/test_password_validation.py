import pytest

from app.utils.password import validate_password

@pytest.mark.unit
def test_validate_password_success():
    pw = "Str0ngP@ss1"
    assert validate_password(pw) == pw

@pytest.mark.unit
@pytest.mark.parametrize(
    "password",
    [
        "short",
        "nouppercase1!",
        "NOLOWERCASE1!",
        "NoNumber!",
        "NoSpecial1",
    ],
)
def test_validate_password_errors(password):
    with pytest.raises(ValueError):
        validate_password(password)
