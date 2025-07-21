"""
Prometheus metrics template for Python services
"""
from prometheus_client import start_http_server, Summary, Counter
REQUEST_LATENCY = Summary('request_latency_seconds', 'Request latency')
REQUEST_ERRORS = Counter('request_errors_total', 'Total request errors')
REQUEST_VOLUME = Counter('request_volume_total', 'Total request volume')
if __name__ == '__main__':
    start_http_server(8000)
