import unittest
from pathlib import Path


PLAN = Path(__file__).parents[1] / "plans" / "initial-plan-draft.md"


class PlanTests(unittest.TestCase):
    def test_plan_records_confirmed_scope_and_existing_project_follow_up(self) -> None:
        plan = PLAN.read_text()
        self.assertIn("### Phase 0 — Confirm scope and prove the first path", plan)
        self.assertIn("The first release targets **new repositories**", plan)
        self.assertIn("`python-api`, `python-api-with-ui`", plan)
        self.assertIn("local development, tests, CI and containers", plan)
        self.assertIn("### Phase 8 — Adapt existing applications", plan)
