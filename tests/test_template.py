from pathlib import Path
import shutil
import tempfile
import tomllib
import unittest

from copier import run_copy


ROOT = Path(__file__).resolve().parents[1]


class CopierTemplateTests(unittest.TestCase):
    def render(
        self, project_type: str | None = None, project_name: str | None = "sample-app"
    ) -> Path:
        target = Path(tempfile.mkdtemp()) / "project"
        self.addCleanup(shutil.rmtree, target.parent, ignore_errors=True)
        data = {}
        if project_name is not None:
            data["project_name"] = project_name
        if project_type is not None:
            data["project_type"] = project_type
        run_copy(
            str(ROOT),
            str(target),
            data=data,
            vcs_ref="HEAD",
            defaults=True,
            overwrite=True,
            unsafe=True,
        )
        return target

    def test_python_api_renders_application_and_foundation(self) -> None:
        target = self.render("python-api")
        self.assertTrue((target / "README.md").is_file())
        self.assertTrue((target / "AGENTS.md").is_file())
        self.assertTrue((target / ".copier-answers.yml").is_file())
        answers = (target / ".copier-answers.yml").read_text()
        self.assertRegex(answers, r"(?m)^_src_path: .+$")
        self.assertRegex(answers, r"(?m)^_commit: .+$")
        self.assertIn("project_name: sample-app", answers)
        self.assertIn("project_type: python-api", answers)
        self.assertTrue((target / "mise.toml").is_file())
        self.assertTrue((target / "mise.lock").is_file())
        tools = tomllib.loads((target / "mise.toml").read_text())["tools"]
        self.assertEqual(tools, {"python": "3.14.8", "uv": "0.12.22"})
        self.assertTrue((target / "src/sample_app/main.py").is_file())
        self.assertTrue((target / "tests/test_app.py").is_file())
        self.assertFalse((target / "src/sample_app/ui.py").exists())
        project = tomllib.loads((target / "pyproject.toml").read_text())
        self.assertEqual(project["build-system"]["build-backend"], "hatchling.build")
        self.assertEqual(
            project["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"],
            ["src/sample_app"],
        )
        self.assertEqual(project["project"]["scripts"]["sample-app"], "sample_app.main:main")

    def test_python_api_with_ui_renders_ui(self) -> None:
        target = self.render("python-api-with-ui")
        self.assertTrue((target / "src/sample_app/ui.py").is_file())
        self.assertIn("streamlit", (target / "pyproject.toml").read_text())
        self.assertIn("API_URL", (target / "src/sample_app/ui.py").read_text())

    def test_generic_has_no_python_application(self) -> None:
        target = self.render("generic")
        self.assertTrue((target / "mise.toml").is_file())
        self.assertFalse((target / "mise.lock").exists())
        self.assertFalse((target / "pyproject.toml").exists())
        self.assertFalse((target / "src").exists())
        self.assertFalse((target / "tests/test_app.py").exists())
        self.assertIn("language-neutral", (target / "README.md").read_text())

    def test_defaults_render_a_python_api_with_default_name(self) -> None:
        target = self.render(project_name=None)
        self.assertTrue((target / "src/my_project/main.py").is_file())

    def test_invalid_project_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Validation error for question 'project_name'"):
            self.render("python-api", "Bad_Name")


if __name__ == "__main__":
    unittest.main()
