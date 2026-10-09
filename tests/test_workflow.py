import re
import unittest
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "validate.yml"


class WorkflowTests(unittest.TestCase):
    def test_validation_workflow_triggers_with_read_only_permissions(self) -> None:
        workflow = WORKFLOW.read_text()

        self.assertRegex(workflow, r"(?m)^on:\s*$")
        self.assertRegex(workflow, r"(?m)^  pull_request:\s*$")
        self.assertRegex(workflow, r"(?m)^  push:\s*$")
        self.assertRegex(workflow, r"(?m)^    branches: \[main\]$")
        self.assertRegex(workflow, r"(?m)^  workflow_dispatch:\s*$")
        self.assertRegex(workflow, r"(?m)^permissions:\s*\n  contents: read\s*$")
        self.assertNotRegex(workflow, r"(?m)^\s+(?:write-all|contents: write|actions: write)\s*$")

    def test_validation_workflow_uses_pinned_tools_and_locked_verifier(self) -> None:
        workflow = WORKFLOW.read_text()

        self.assertRegex(workflow, r"uses: actions/checkout@[0-9a-f]{40} # v")
        self.assertRegex(workflow, r"uses: astral-sh/setup-uv@[0-9a-f]{40} # v")
        self.assertIn("version: 0.12.22", workflow)
        self.assertIn("python-version: 3.14.8", workflow)
        self.assertIn("run: uv sync --locked", workflow)
        self.assertIn("run: ./scripts/verify", workflow)
        self.assertRegex(workflow, r"(?m)^    timeout-minutes: [1-9][0-9]*$")


if __name__ == "__main__":
    unittest.main()
