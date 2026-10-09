from pathlib import Path
import shutil
import tempfile
import unittest

from copier import run_copy


ROOT = Path(__file__).resolve().parents[1]


class ContainerTemplateTests(unittest.TestCase):
    def render(self, **answers: object) -> Path:
        target = Path(tempfile.mkdtemp()) / "project"
        self.addCleanup(shutil.rmtree, target.parent, ignore_errors=True)
        run_copy(
            str(ROOT),
            str(target),
            data={"project_name": "sample-app", **answers},
            defaults=True,
            overwrite=True,
            unsafe=True,
        )
        return target

    def test_containers_are_omitted_by_default(self) -> None:
        target = self.render(project_type="python-api")
        for name in ("Dockerfile.api", "Dockerfile.ui", ".dockerignore", "compose.yaml"):
            self.assertFalse((target / name).exists(), name)

    def test_api_container_uses_project_name_and_selected_port(self) -> None:
        target = self.render(project_type="python-api", include_containers=True, api_port=9000)
        dockerfile = (target / "Dockerfile.api").read_text()
        self.assertIn("FROM python:3.14.8-slim", dockerfile)
        self.assertIn("EXPOSE 9000", dockerfile)
        self.assertIn("sample_app.main:app", dockerfile)
        self.assertTrue((target / ".dockerignore").is_file())
        self.assertFalse((target / "Dockerfile.ui").exists())
        self.assertFalse((target / "compose.yaml").exists())

    def test_ui_compose_builds_both_services_with_discovery_and_ports(self) -> None:
        target = self.render(
            project_type="python-api-with-ui",
            include_containers=True,
            include_compose=True,
            api_port=9000,
            ui_port=8600,
        )
        compose = (target / "compose.yaml").read_text()
        self.assertTrue((target / "Dockerfile.api").is_file())
        self.assertTrue((target / "Dockerfile.ui").is_file())
        self.assertIn("sample-app-api:local", compose)
        self.assertIn("sample-app-ui:local", compose)
        self.assertIn('"9000:9000"', compose)
        self.assertIn('"8600:8600"', compose)
        self.assertIn("API_URL: http://api:9000", compose)
        self.assertIn("condition: service_healthy", compose)

    def test_generic_container_selection_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Container packaging is supported only for Python"):
            self.render(project_type="generic", include_containers=True)

    def test_compose_without_containers_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Compose requires container packaging"):
            self.render(project_type="python-api", include_compose=True)


if __name__ == "__main__":
    unittest.main()
