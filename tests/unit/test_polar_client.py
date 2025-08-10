import hashlib
import hmac
from unittest.mock import MagicMock

import pytest

from app.polar.client import PolarClient


@pytest.mark.unit
def test_verify_webhook_signature():
    client = PolarClient(api_key="key", org_id="org", webhook_secret="secret")
    payload = b"{}"
    signature = hmac.new(b"secret", payload, hashlib.sha256).hexdigest()
    assert client.verify_webhook(payload, signature) is True
    assert client.verify_webhook(payload, "bad") is False


@pytest.mark.unit
def test_get_subscription(mocker):
    mock_http_client = MagicMock()
    response = MagicMock()
    response.json.return_value = {"id": "sub_1"}
    response.raise_for_status.return_value = None
    mock_http_client.get.return_value = response
    mocker.patch("app.polar.client.httpx.Client", return_value=mock_http_client)

    client = PolarClient(api_key="key", org_id="org")
    data = client.get_subscription("sub_1")

    mock_http_client.get.assert_called_with("/subscriptions/sub_1")
    assert data["id"] == "sub_1"
