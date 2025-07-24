import pytest
from app.utils.password_validation import validate_password


@pytest.mark.unit
@pytest.mark.parametrize("pwd", ["GoodPass1!", "Another1@"])
def test_validate_password_accepts_valid(pwd):
    assert validate_password(pwd) == pwd


@pytest.mark.unit
@pytest.mark.parametrize(
    "pwd",
    [
        "short",
        "nocaps1!",
        "NOLOWER1!",
        "NoDigit!",
        "NoSpecial1",
    ],
)
def test_validate_password_rejects_invalid(pwd):
    with pytest.raises(ValueError):
        validate_password(pwd)
