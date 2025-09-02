"""
API Contract Tests using Pact
Consumer-driven contract testing for WebSet Miner API
"""

import pytest
import json
from pact import Consumer, Provider, Like, EachLike, Term
from unittest.mock import patch
import httpx


# Pact setup
pact = Consumer('webset-miner-frontend').has_pact_with(
    Provider('webset-miner-api'),
    host_name='localhost',
    port=1234,
    pact_dir='./pacts'
)


class TestWebSetMinerAPIContract:
    """Contract tests for WebSet Miner API endpoints"""

    def setup_method(self):
        """Setup for each test method"""
        pact.start()

    def teardown_method(self):
        """Cleanup after each test method"""
        pact.stop()

    @pytest.fixture(scope='session', autouse=True)
    def setup_pact(self):
        """Setup Pact mock service"""
        pact.start()
        yield
        pact.stop()

    def test_health_endpoint_contract(self):
        """Test health endpoint contract"""
        expected_response = {
            'status': Like('healthy'),
            'timestamp': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*', '2024-01-01T12:00:00Z'),
            'version': Like('1.0.0')
        }

        (pact
         .given('API is healthy')
         .upon_receiving('a request for health status')
         .with_request(
             method='GET',
             path='/health'
         )
         .will_respond_with(
             status=200,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))

        with pact:
            response = httpx.get('http://localhost:1234/health')
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert 'timestamp' in data

    def test_datasets_list_contract(self):
        """Test datasets listing endpoint contract"""
        expected_response = {
            'datasets': EachLike({
                'id': Like(1),
                'name': Like('Sample Dataset'),
                'description': Like('A sample dataset for testing'),
                'status': Term(r'(active|inactive|processing)', 'active'),
                'created_at': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*', '2024-01-01T12:00:00Z'),
                'updated_at': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*', '2024-01-01T12:00:00Z'),
                'record_count': Like(1000),
                'tags': EachLike('web-scraping')
            }),
            'total': Like(10),
            'page': Like(1),
            'per_page': Like(20)
        }

        (pact
         .given('datasets exist')
         .upon_receiving('a request for datasets list')
         .with_request(
             method='GET',
             path='/v1/datasets',
             headers={'Authorization': Term(r'Bearer .+', 'Bearer valid-token')}
         )
         .will_respond_with(
             status=200,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))

        with pact:
            headers = {'Authorization': 'Bearer valid-token'}
            response = httpx.get('http://localhost:1234/v1/datasets', headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert 'datasets' in data
            assert isinstance(data['datasets'], list)
            if data['datasets']:
                dataset = data['datasets'][0]
                assert 'id' in dataset
                assert 'name' in dataset
                assert 'status' in dataset

    def test_dataset_creation_contract(self):
        """Test dataset creation endpoint contract"""
        request_body = {
            'name': 'New Dataset',
            'description': 'A new dataset for testing',
            'source_urls': ['https://example.com'],
            'tags': ['test', 'automation']
        }

        expected_response = {
            'id': Like(123),
            'name': Like('New Dataset'),
            'description': Like('A new dataset for testing'),
            'status': Like('processing'),
            'created_at': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*', '2024-01-01T12:00:00Z'),
            'source_urls': EachLike('https://example.com'),
            'tags': EachLike('test')
        }

        (pact
         .given('user has permission to create datasets')
         .upon_receiving('a request to create a dataset')
         .with_request(
             method='POST',
             path='/v1/datasets',
             headers={
                 'Authorization': Term(r'Bearer .+', 'Bearer valid-token'),
                 'Content-Type': 'application/json'
             },
             body=request_body
         )
         .will_respond_with(
             status=201,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))

        with pact:
            headers = {
                'Authorization': 'Bearer valid-token',
                'Content-Type': 'application/json'
            }
            response = httpx.post(
                'http://localhost:1234/v1/datasets',
                headers=headers,
                json=request_body
            )
            assert response.status_code == 201
            data = response.json()
            assert data['name'] == 'New Dataset'
            assert data['status'] == 'processing'

    def test_search_endpoint_contract(self):
        """Test search endpoint contract"""
        request_body = {
            'query': 'web scraping tools',
            'filters': {
                'status': 'active',
                'tags': ['automation']
            },
            'limit': 10,
            'offset': 0
        }

        expected_response = {
            'results': EachLike({
                'id': Like(1),
                'title': Like('Web Scraping Guide'),
                'content': Like('A comprehensive guide to web scraping...'),
                'url': Like('https://example.com/guide'),
                'score': Like(0.95),
                'dataset_id': Like(123),
                'metadata': {
                    'extracted_at': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*', '2024-01-01T12:00:00Z'),
                    'content_type': Like('article')
                }
            }),
            'total': Like(50),
            'query_time_ms': Like(125)
        }

        (pact
         .given('search index contains data')
         .upon_receiving('a search request')
         .with_request(
             method='POST',
             path='/v1/search',
             headers={
                 'Authorization': Term(r'Bearer .+', 'Bearer valid-token'),
                 'Content-Type': 'application/json'
             },
             body=request_body
         )
         .will_respond_with(
             status=200,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))

        with pact:
            headers = {
                'Authorization': 'Bearer valid-token',
                'Content-Type': 'application/json'
            }
            response = httpx.post(
                'http://localhost:1234/v1/search',
                headers=headers,
                json=request_body
            )
            assert response.status_code == 200
            data = response.json()
            assert 'results' in data
            assert 'total' in data
            assert isinstance(data['results'], list)

    def test_analytics_endpoint_contract(self):
        """Test analytics endpoint contract"""
        expected_response = {
            'metrics': {
                'total_datasets': Like(25),
                'active_datasets': Like(20),
                'total_records': Like(1000000),
                'crawl_success_rate': Like(0.95),
                'avg_processing_time_minutes': Like(15.5)
            },
            'trends': {
                'datasets_created_last_30_days': Like(5),
                'records_processed_last_24_hours': Like(50000)
            },
            'top_domains': EachLike({
                'domain': Like('example.com'),
                'record_count': Like(10000),
                'success_rate': Like(0.98)
            })
        }

        (pact
         .given('analytics data is available')
         .upon_receiving('a request for analytics')
         .with_request(
             method='GET',
             path='/v1/analytics',
             headers={'Authorization': Term(r'Bearer .+', 'Bearer admin-token')}
         )
         .will_respond_with(
             status=200,
             headers={'Content-Type': 'application/json'},
             body=expected_response
         ))

        with pact:
            headers = {'Authorization': 'Bearer admin-token'}
            response = httpx.get('http://localhost:1234/v1/analytics', headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert 'metrics' in data
            assert 'trends' in data
            assert data['metrics']['total_datasets'] > 0

    def test_error_response_contract(self):
        """Test error response contract"""
        expected_error = {
            'error': {
                'code': Like('UNAUTHORIZED'),
                'message': Like('Invalid or expired token'),
                'details': Like('The provided authentication token is invalid')
            },
            'timestamp': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*', '2024-01-01T12:00:00Z')
        }

        (pact
         .given('user is not authenticated')
         .upon_receiving('a request without valid authentication')
         .with_request(
             method='GET',
             path='/v1/datasets',
             headers={'Authorization': 'Bearer invalid-token'}
         )
         .will_respond_with(
             status=401,
             headers={'Content-Type': 'application/json'},
             body=expected_error
         ))

        with pact:
            headers = {'Authorization': 'Bearer invalid-token'}
            response = httpx.get('http://localhost:1234/v1/datasets', headers=headers)
            assert response.status_code == 401
            data = response.json()
            assert 'error' in data
            assert data['error']['code'] == 'UNAUTHORIZED'


class TestOpenAPIValidation:
    """Validate API responses against OpenAPI schema"""

    def test_openapi_schema_validation(self):
        """Test that API responses match OpenAPI schema"""
        # This would typically use a library like openapi-core
        # to validate responses against the OpenAPI spec
        pass

    def test_schema_backwards_compatibility(self):
        """Test that schema changes are backwards compatible"""
        # This would compare current schema with previous version
        # to ensure no breaking changes
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
