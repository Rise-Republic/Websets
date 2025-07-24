# Logging Policy

This service uses **loguru** for structured logging. A custom configuration in `app.logging_utils` redacts sensitive values before log messages are emitted.

## Redaction Strategy

- Fields containing `password`, `secret`, `token`, `api_key`, `jwt`, `email`, or `prompt` are replaced with `<redacted>`.
- Redaction is applied via a loguru patcher so all log statements pass through the filter automatically.
- Developers should avoid logging full user prompts or credentials directly; rely on the built‑in redaction to sanitize accidental leaks.

## Usage Example
```python
from app.logging_utils import configure_logging
configure_logging("INFO", json=True)
```

JSON output makes it easier for log aggregation platforms to parse events. The
application enables this mode by default when started via `app.main`.

Tests under `tests/unit/test_logging_redaction.py` verify that sensitive data is not written to logs.
