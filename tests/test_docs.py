import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UsageGuideTests(unittest.TestCase):
    def test_readme_links_usage_guide(self) -> None:
        readme = (ROOT / "README.md").read_text()

        self.assertIn("[usage guide](docs/usage.md)", readme)

    def test_guide_documents_pinned_generation_and_safe_update(self) -> None:
        guide = (ROOT / "docs" / "usage.md").read_text()

        self.assertIn("copier==9.18.2", guide)
        self.assertIn("include_devcontainer: true", guide)
        self.assertIn("mise install --locked", guide)
        self.assertIn("--vcs-ref v1.1.0", guide)
        self.assertIn("--data-file /tmp/answers.yml", guide)
        self.assertIn("does not provision infrastructure", guide)
        self.assertIn("production secrets", guide)
        self.assertIn("git switch -c template-update", guide)
        self.assertIn("copier update", guide)
        self.assertIn("GitHub Actions CI is available as an optional feature", guide)
        self.assertIn("Kustomize manifests are optional", guide)
        self.assertIn("kubectl kustomize kubernetes/base", guide)
        self.assertIn("Kubernetes", guide)
        self.assertIn("Flux bundle", guide)


if __name__ == "__main__":
    unittest.main()
