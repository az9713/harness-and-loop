from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from harness import HarnessRuntime  # noqa: E402


def main() -> int:
    task = " ".join(sys.argv[1:]).strip() or "Build me a harness based on the blueprint"
    runtime = HarnessRuntime(ROOT)
    result = runtime.run(task)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    if not result["gate"]["release_allowed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

