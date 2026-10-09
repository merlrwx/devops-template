from pathlib import Path
import shutil
import tempfile
import unittest

from copier import run_copy


ROOT = Path(__file__).resolve().parents[1]


class KubernetesTemplateTests(unittest.TestCase):
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

    def test_kubernetes_and_flux_are_omitted_by_default(self) -> None:
        target = self.render(project_type="python-api")
        self.assertFalse((target / "kubernetes/base").exists())
        self.assertFalse((target / "kubernetes/flux").exists())

    def test_api_manifests_use_namespace_and_selected_port(self) -> None:
        target = self.render(
            project_type="python-api",
            include_containers=True,
            include_kubernetes=True,
            kubernetes_namespace="team-app",
            api_port=9000,
        )
        base = target / "kubernetes/base"
        self.assertTrue((base / "namespace.yaml").is_file())
        self.assertTrue((base / "api.yaml").is_file())
        self.assertFalse((base / "ui.yaml").exists())
        kustomization = (base / "kustomization.yaml").read_text()
        api = (base / "api.yaml").read_text()
        namespace = (base / "namespace.yaml").read_text()
        self.assertIn("namespace: team-app", kustomization)
        self.assertIn("name: team-app", namespace)
        self.assertIn("sample-app-api", api)
        self.assertIn("containerPort: 9000", api)
        self.assertIn("port: 9000", api)
        self.assertIn("path: /health", api)

    def test_api_ui_manifests_use_selected_ports_and_service_discovery(self) -> None:
        target = self.render(
            project_type="python-api-with-ui",
            include_containers=True,
            include_kubernetes=True,
            api_port=9000,
            ui_port=8600,
        )
        base = target / "kubernetes/base"
        self.assertTrue((base / "ui.yaml").is_file())
        self.assertIn("ui.yaml", (base / "kustomization.yaml").read_text())
        ui = (base / "ui.yaml").read_text()
        self.assertIn("sample-app-ui", ui)
        self.assertIn("containerPort: 8600", ui)
        self.assertIn("port: 8600", ui)
        self.assertIn("value: http://sample-app-api:9000", ui)

    def test_flux_bundle_targets_kubernetes_base_without_pruning(self) -> None:
        target = self.render(
            project_type="python-api",
            include_containers=True,
            include_kubernetes=True,
            include_flux=True,
            git_repository_url="https://github.com/example/sample-app.git",
        )
        flux = target / "kubernetes/flux"
        source = (flux / "gitrepository.yaml").read_text()
        reconciliation = (flux / "kustomization.yaml").read_text()
        docs = (flux / "README.md").read_text()
        self.assertIn("url: https://github.com/example/sample-app.git", source)
        self.assertIn("path: ./kubernetes/base", reconciliation)
        self.assertIn("prune: false", reconciliation)
        self.assertIn("existing Flux controller", docs)
        self.assertIn("reconciliation root", docs)

    def test_kubernetes_requires_python_and_containers(self) -> None:
        with self.assertRaisesRegex(ValueError, "supported only for Python"):
            self.render(project_type="generic", include_containers=True, include_kubernetes=True)
        with self.assertRaisesRegex(ValueError, "Kubernetes requires container packaging"):
            self.render(project_type="python-api", include_kubernetes=True)

    def test_flux_requires_kubernetes_and_a_valid_explicit_repository_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "Flux requires Kubernetes"):
            self.render(project_type="python-api", include_flux=True)
        with self.assertRaisesRegex(ValueError, "explicitly provided HTTPS or SSH"):
            self.render(
                project_type="python-api",
                include_containers=True,
                include_kubernetes=True,
                include_flux=True,
            )
        with self.assertRaisesRegex(ValueError, "explicitly provided HTTPS or SSH"):
            self.render(
                project_type="python-api",
                include_containers=True,
                include_kubernetes=True,
                include_flux=True,
                git_repository_url="not-a-repository-url",
            )


if __name__ == "__main__":
    unittest.main()
