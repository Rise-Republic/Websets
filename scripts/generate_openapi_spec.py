from app.main import app
import json
from pathlib import Path

"""Generate OpenAPI specification for the WebSet Miner API."""

spec = app.openapi()
Path("openapi.json").write_text(json.dumps(spec, indent=2))
print("OpenAPI spec generated at openapi.json")
