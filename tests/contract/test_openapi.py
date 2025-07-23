import pytest
from schemathesis import openapi
from app.main import app

# Schemathesis 4.x exposes helpers under the ``openapi`` module
schema = openapi.from_asgi('/openapi.json', app)

@pytest.mark.contract
@schema.parametrize()
def test_api_contract(case):
    response = case.call()
    case.validate_response(response)
