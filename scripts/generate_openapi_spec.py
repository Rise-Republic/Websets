from app.main import app
import json
from pathlib import Path
from loguru import logger

"""Generate OpenAPI specification for the WebSet Miner API."""

spec = app.openapi()
Path("openapi.json").write_text(json.dumps(spec, indent=2))
logger.info("OpenAPI spec generated at openapi.json")
