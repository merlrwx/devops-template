from pathlib import Path
import shutil
import tempfile
import unittest

from copier import run_copy


ROOT = Path(__file__).resolve().parents[1]


class ProjectCiTemplateTests(unittest.TestCase):
    def render(self, **answers: object) -> Path:
        target = Path(tempfile.mkdtemp()) / "project"
        self.addCleanup(shutil.rmtree, target.parent, ignore_errors=True)
        run_copy(
            str(ROOT),
            str(target),
            data={"project_name": "sample-app", **answers},
            vcs_ref="HEAD",
            defaults=True,
            overwrite=True,
            unsafe=True,
        )
        return target

    def test_github_actions_are_omitted_by_default(self) -> None:
        target = self.render(project_type="python-api")

        self.assertFalse((target / ".github/workflows/ci.yml").exists())

    def test_python_api_renders_github_actions_ci(self) -> None:
        target = self.render(project_type="python-api", include_github_actions=True)

        workflow = (target / ".github/workflows/ci.yml").read_text()
        self.assertIn("pull_request:", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("timeout-minutes: 15", workflow)
        self.assertIn("uv lock; fi", workflow)
        self.assertIn("run: uv sync --locked", workflow)
        self.assertIn("run: uv run ruff check .", workflow)
        self.assertIn("run: uv run pytest", workflow)
        self.assertRegex(workflow, r"uses: actions/checkout@[0-9a-f]{40} # v")
        self.assertRegex(workflow, r"uses: astral-sh/setup-uv@[0-9a-f]{40} # v")

    def test_python_api_with_ui_renders_github_actions_ci(self) -> None:
        target = self.render(
            project_type="python-api-with-ui", include_github_actions=True
        )

        self.assertTrue((target / ".github/workflows/ci.yml").is_file())
        self.assertIn("streamlit", (target / "pyproject.toml").read_text())

    def test_generic_github_actions_selection_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "GitHub Actions CI is supported only for Python"
        ):
            self.render(project_type="generic", include_github_actions=True)


if __name__ == "__main__":
    unittest.main()
