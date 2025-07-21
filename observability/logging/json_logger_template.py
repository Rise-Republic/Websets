"""
JSON logger template for Python services with trace ID support
"""
import logging
import json
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'trace_id': getattr(record, 'trace_id', None),
            'service': 'your-service-name',
            'tenant': 'your-tenant-id'
        }
        return json.dumps(log_record)
