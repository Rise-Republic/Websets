import json
import sys
from pathlib import Path
import difflib
from loguru import logger


def check_file(path: Path) -> bool:
    original = path.read_text()
    try:
        data = json.loads(original)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", path, e)
        return False
    formatted = json.dumps(data, indent=2) + "\n"
    if original != formatted:
        logger.warning("Dashboard %s is not normalized. Diff:", path)
        for line in difflib.unified_diff(
            original.splitlines(),
            formatted.splitlines(),
            fromfile=str(path),
            tofile=str(path),
        ):
            logger.info(line)
        return False
    return True


def main(directory: str) -> int:
    ok = True
    for file in Path(directory).glob("*.json"):
        if not check_file(file):
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    dir_path = sys.argv[1] if len(sys.argv) > 1 else "monitoring/grafana/dashboards"
    sys.exit(main(dir_path))
