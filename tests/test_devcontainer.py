from pathlib import Path
import shutil
import tempfile
import unittest

from copier import run_copy


ROOT = Path(__file__).resolve().parents[1]


class DevcontainerTemplateTests(unittest.TestCase):
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

    def test_devcontainer_is_omitted_by_default(self) -> None:
        target = self.render(project_type="python-api")
        self.assertFalse((target / ".devcontainer").exists())

    def test_python_api_renders_devcontainer(self) -> None:
        target = self.render(project_type="python-api", include_devcontainer=True)
        self.assertTrue((target / ".devcontainer/devcontainer.json").is_file())
        self.assertTrue((target / ".devcontainer/Dockerfile").is_file())
        config = (target / ".devcontainer/devcontainer.json").read_text()
        self.assertIn('"postCreateCommand": "mise trust && mise install --locked && mise exec -- uv sync"', config)
        dockerfile = (target / ".devcontainer/Dockerfile").read_text()
        self.assertIn("FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04", dockerfile)

    def test_python_api_with_ui_renders_devcontainer(self) -> None:
        target = self.render(project_type="python-api-with-ui", include_devcontainer=True)
        self.assertTrue((target / ".devcontainer/devcontainer.json").is_file())
        self.assertTrue((target / ".devcontainer/Dockerfile").is_file())

    def test_generic_devcontainer_selection_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Dev Containers are supported only for Python"):
            self.render(project_type="generic", include_devcontainer=True)


if __name__ == "__main__":
    unittest.main()
