"""Verify module combinations and observable generated behaviour, not just file names."""

import ast
import importlib.util
import json
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from copier import run_copy
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULES = [
    "include_containers",
    "include_compose",
    "include_devcontainer",
    "include_github_actions",
    "include_kubernetes",
    "include_flux",
    "include_coverage",
    "include_pre_commit",
    "include_persistence",
    "include_security_scanning",
    "include_release_automation",
    "include_image_publishing",
    "include_gitops_promotion",
    "include_k3d",
]
FULL = {
    **dict.fromkeys(MODULES, True),
    "git_repository_url": "https://github.com/example/sample-gitops.git",
    "gitops_repository": "example/sample-gitops",
    "image_registry_namespace": "example",
}


class DeliveryTests(unittest.TestCase):
    def render(self, **data):
        temp = Path(tempfile.mkdtemp(prefix="template-delivery-"))
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        dest = temp / "project"
        run_copy(
            str(ROOT),
            str(dest),
            data={"project_name": "sample-app", **data},
            vcs_ref="HEAD",
            defaults=True,
            overwrite=True,
            quiet=True,
        )
        return dest

    def command(self, dest, *args):
        result = subprocess.run(args, cwd=dest, text=True, capture_output=True)
        self.assertEqual(
            result.returncode, 0, f"{args}:\n{result.stdout}\n{result.stderr}"
        )
        return result.stdout

    def test_full_layouts_have_valid_configs_and_gated_scans(self):
        for split in (False, True):
            with self.subTest(split=split):
                dest = self.render(
                    project_type="python-api-with-ui", separate_packages=split, **FULL
                )
                for file in dest.rglob("*"):
                    if not file.is_file():
                        continue
                    if file.suffix in (".yaml", ".yml"):
                        list(yaml.safe_load_all(file.read_text()))
                    elif file.suffix == ".json":
                        json.loads(file.read_text())
                    elif file.suffix == ".toml":
                        tomllib.loads(file.read_text())
                    elif file.suffix == ".py":
                        ast.parse(file.read_text())
                answers = yaml.safe_load((dest / ".copier-answers.yml").read_text())
                for module in MODULES:
                    self.assertTrue(answers[module])
                self.assertIn("_commit", answers)
                ci = (dest / ".github/workflows/ci.yml").read_text()
                self.assertIn("exit-code: '1'", ci)
                self.assertIn("ignore-unfixed: false", ci)
                self.assertIn("pip-audit", ci)
                self.assertIn("bandit", ci)
                self.assertIn("gitleaks", ci)
                self.assertIn("--cov-fail-under=80", ci)
                for env in ("dev", "prod"):
                    if shutil.which("kubectl"):
                        rendered = self.command(
                            dest, "kubectl", "kustomize", f"kubernetes/overlays/{env}"
                        )
                        self.assertIn(f"namespace: sample-app-{env}", rendered)
                        self.assertIn("persistentVolumeClaim:", rendered)
                        self.assertIn(f"http://{env}-sample-app-api:8000", rendered)
                        self.command(dest, "kubectl", "kustomize", f"gitops/apps/{env}")
                container = json.loads(
                    (dest / ".devcontainer/devcontainer.json").read_text()
                )
                self.assertEqual(container["forwardPorts"], [8000, 8501])
                self.assertIn(
                    "ghcr.io/devcontainers/features/docker-in-docker:2.17.0",
                    container["features"],
                )
                if split:
                    self.assertFalse((dest / "src").exists())
                    self.assertTrue(
                        (dest / "services/api/src/sample_app/main.py").exists()
                    )
                    self.assertTrue(
                        (dest / "services/ui/src/sample_app_ui/ui.py").exists()
                    )

    def test_minimal_and_generic_exclude_optional_modules(self):
        for typ in ("python-api", "generic"):
            dest = self.render(project_type=typ)
            for path in (
                "services",
                ".devcontainer",
                "gitops",
                "scripts/cluster.py",
                ".pre-commit-config.yaml",
                ".github/workflows/publish.yml",
                ".github/workflows/release.yml",
                ".github/workflows/promote.yml",
            ):
                self.assertFalse((dest / path).exists(), path)

    def test_dependencies_and_invalid_inputs_are_rejected(self):
        invalid = [
            {"include_security_scanning": True},
            {"include_release_automation": True},
            {"include_image_publishing": True},
            {"include_gitops_promotion": True},
            {"include_k3d": True},
            {"separate_packages": True},
            {"coverage_threshold": 101},
            {"include_containers": True, "api_port": 0},
            {
                "include_containers": True,
                "include_github_actions": True,
                "include_image_publishing": True,
            },
            {"project_type": "generic", "include_coverage": True},
            {"project_type": "generic", "include_pre_commit": True},
            {"project_type": "generic", "include_persistence": True},
        ]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.render(**data)

    def load(self, path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_promotion_updates_only_matching_images_and_validates_tag(self):
        dest = self.render(project_type="python-api-with-ui", **FULL)
        module = self.load(dest / "scripts/promote.py", "promotion")
        manifest = dest / "gitops/apps/dev/kustomization.yaml"
        module.update(manifest, "api-v1.2.3")
        text = manifest.read_text()
        self.assertIn("newTag: api-v1.2.3", text)
        self.assertEqual(text.count("newTag: v0.1.0"), 1)
        module.update(manifest, "v2.0.0")
        self.assertEqual(manifest.read_text().count("newTag: v2.0.0"), 2)
        before = manifest.read_text()
        for bad in ("latest", "v1.2.3\nmalicious: injected", "$(id)"):
            with self.assertRaises(ValueError):
                module.update(manifest, bad)
        self.assertEqual(manifest.read_text(), before)
        manifest.write_text("unrelated: value\n")
        with self.assertRaises(ValueError):
            module.update(manifest, "v1.2.3")
        self.assertEqual(manifest.read_text(), "unrelated: value\n")

    def test_cluster_refuses_foreign_teardown_and_flux_sync(self):
        dest = self.render(
            **{k: v for k, v in FULL.items() if k != "separate_packages"}
        )
        module = self.load(dest / "scripts/cluster.py", "cluster_test")
        with patch.object(module, "run") as run:
            with self.assertRaises(ValueError):
                module.operate("down", "foreign-cluster", yes=True)
            with self.assertRaises(ValueError):
                module.operate("down", "sample-app-local")
            run.assert_not_called()
        with patch.object(module, "kube") as kube, patch.object(module, "run") as run:
            kube.return_value.returncode = 0
            with self.assertRaisesRegex(ValueError, "Flux-managed"):
                module.sync("sample-app-local")
            run.assert_not_called()

    def test_generated_runtime_lint_format_and_coverage(self):
        profiles = [
            {"project_type": "python-api"},
            {
                "project_type": "python-api",
                "include_persistence": True,
                "include_coverage": True,
            },
            {"project_type": "python-api-with-ui", **FULL},
            {"project_type": "python-api-with-ui", "separate_packages": True, **FULL},
        ]
        for data in profiles:
            with self.subTest(data=data):
                dest = self.render(**data)
                self.command(dest, "uv", "sync")
                self.command(dest, "uv", "run", "ruff", "check", ".")
                self.command(dest, "uv", "run", "ruff", "format", "--check", ".")
                args = ["uv", "run", "pytest"]
                if data.get("include_coverage"):
                    args += ["--cov", "--cov-report=xml"]
                self.command(dest, *args)


class DeliveryMigrationTests(unittest.TestCase):
    def test_real_template_update_retains_application_and_records_new_options(self):
        from copier import run_update

        with tempfile.TemporaryDirectory(prefix="template-migration-") as directory:
            dest = Path(directory) / "project"
            run_copy(
                str(ROOT),
                str(dest),
                vcs_ref="9d2fcc7c0495c0ec5406229a5fd46124ae7f25e5",
                defaults=True,
                quiet=True,
                data={"project_name": "migrated-app"},
            )
            subprocess.run(["git", "init", str(dest)], check=True, capture_output=True)
            (dest / "user-notes.txt").write_text("Keep project-owned notes.\n")
            for args in (
                ["add", "."],
                [
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-m",
                    "chore: initial scaffold",
                ],
            ):
                subprocess.run(
                    ["git", "-C", str(dest), *args], check=True, capture_output=True
                )
            run_update(
                str(dest),
                vcs_ref="HEAD",
                overwrite=True,
                defaults=True,
                quiet=True,
                data={"include_coverage": True, "include_pre_commit": True},
            )
            self.assertEqual(
                (dest / "user-notes.txt").read_text(), "Keep project-owned notes.\n"
            )
            answers = yaml.safe_load((dest / ".copier-answers.yml").read_text())
            self.assertTrue(answers["include_coverage"])
            self.assertTrue(answers["include_pre_commit"])
            self.assertFalse(answers["separate_packages"])
            self.assertFalse(list(dest.rglob("*.rej")))
            self.assertIn("/live", (dest / "src/migrated_app/main.py").read_text())
            self.assertTrue((dest / ".pre-commit-config.yaml").exists())
