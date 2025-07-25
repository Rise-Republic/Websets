import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.security import SecurityMiddleware


@pytest.mark.integration
def test_security_headers_present():
    app = FastAPI()
    app.add_middleware(SecurityMiddleware)

    @app.get('/')
    def root():
        return {'ok': True}

    with TestClient(app) as client:
        response = client.get('/')
        assert response.headers['Strict-Transport-Security'].startswith('max-age=')
        assert response.headers['X-Frame-Options'] == 'DENY'
