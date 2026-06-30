from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from harness import HarnessRuntime  # noqa: E402
from harness.config import HarnessConfig  # noqa: E402
from harness.permissions import PermissionPolicy  # noqa: E402
from harness.types import Action  # noqa: E402


class HarnessRuntimeTest(unittest.TestCase):
    def test_harness_run_passes_gate(self) -> None:
        runtime = HarnessRuntime(ROOT)
        result = runtime.run("Build me a harness based on the blueprint")
        self.assertEqual(result["blocked_reason"], "")
        self.assertTrue(result["eval"]["passed"])
        self.assertTrue(result["gate"]["release_allowed"])
        self.assertIn("trace", result["final_answer"].lower())

    def test_irreversible_tool_action_requires_approval(self) -> None:
        policy = PermissionPolicy(HarnessConfig(root=ROOT))
        action = Action(kind="tool", name="retrieve_memory", args={"irreversible": True})
        allowed, reason = policy.authorize(action)
        self.assertFalse(allowed)
        self.assertIn("approval", reason)


if __name__ == "__main__":
    unittest.main()
