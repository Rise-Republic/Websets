import os
import sys
from unittest import mock
import pytest
from schemathesis import openapi

# Ensure the project root is on the path so ``app`` can be imported when this
# test is executed in isolation.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

with mock.patch("app.middleware.rate_limiting.limiter.limit", lambda *a, **k: (lambda f: f)), \
     mock.patch("app.middleware.rate_limiting.user_limiter.limit", lambda *a, **k: (lambda f: f)):
    from app.main import app

# Schemathesis 4.x exposes helpers under the ``openapi`` module
schema = openapi.from_asgi('/openapi.json', app)

@pytest.mark.contract
@schema.parametrize()
def test_api_contract(case):
    response = case.call()
    case.validate_response(response)
