import pytest
import schemathesis
from app.main import app

schema = schemathesis.from_asgi('/openapi.json', app)

@pytest.mark.contract
@schema.parametrize()
def test_api_contract(case):
    response = case.call()
    case.validate_response(response)
