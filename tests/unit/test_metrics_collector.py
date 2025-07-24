import re
import pytest

from app.monitoring.metrics import MetricsCollector


@pytest.fixture
def collector(monkeypatch):
    # Disable background task creation during tests
    monkeypatch.setattr(MetricsCollector, "_start_system_metrics_collection", lambda self: None)
    return MetricsCollector()


@pytest.mark.unit
def test_record_and_retrieve_metrics(collector):
    collector.record_http_request("GET", "/items", 200, 0.1)
    collector.record_job_started()
    collector.record_job_completed(duration=0.2)
    collector.record_job_failed(duration=0.3)
    collector.record_url_crawled("success", duration=0.4)
    collector.record_crawler_error("timeout")
    collector.record_vector_operation("search", "success", 0.5)
    collector.update_vectors_stored(7)
    collector.update_db_connections(2)
    collector.record_db_query("select", 0.05)
    collector.record_cache_operation("get", "hit")
    collector.update_cache_hit_ratio(0.9)
    collector.update_celery_queue_length(4)
    collector.update_websocket_connections(1)
    collector.record_websocket_message("ping")

    metrics = collector.get_metrics()

    assert 'websets_http_requests_total{endpoint="/items",method="GET",status_code="200"} 1.0' in metrics
    assert 'websets_jobs_total{status="started"} 1.0' in metrics
    assert 'websets_jobs_total{status="completed"} 1.0' in metrics
    assert 'websets_jobs_total{status="failed"} 1.0' in metrics
    assert 'websets_crawl_duration_seconds_count 1.0' in metrics
    assert 'websets_celery_queue_length 4.0' in metrics
    assert 'websets_vectors_stored_total 7.0' in metrics
    assert 'websets_websocket_messages_total{message_type="ping"} 1.0' in metrics

    summary = collector.get_metrics_summary()
    assert summary["metrics_available"] is True
    assert summary["registry_size"] > 0
    assert re.match(r"\d{4}-\d{2}-\d{2}T", summary["timestamp"])
