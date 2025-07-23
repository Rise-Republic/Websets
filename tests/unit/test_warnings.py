import warnings
import pytest

@pytest.mark.unit
def test_deprecation_warning():
    """This test exists solely to check if pytest is capturing warnings."""
    warnings.warn("This is a test deprecation warning.", DeprecationWarning)
    assert True
