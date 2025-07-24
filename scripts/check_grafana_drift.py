import json
import sys
from pathlib import Path
import difflib


def check_file(path: Path) -> bool:
    original = path.read_text()
    try:
        data = json.loads(original)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {path}: {e}")
        return False
    formatted = json.dumps(data, indent=2) + "\n"
    if original != formatted:
        print(f"Dashboard {path} is not normalized. Diff:")
        for line in difflib.unified_diff(
            original.splitlines(),
            formatted.splitlines(),
            fromfile=str(path),
            tofile=str(path),
        ):
            print(line)
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
