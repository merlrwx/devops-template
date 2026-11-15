"""The generated quality gate: one check task and a suppression guard."""

import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

from copier import run_copy

ROOT = Path(__file__).resolve().parents[1]


class QualityGateTests(unittest.TestCase):
    def render(self, **data) -> Path:
        temp = Path(tempfile.mkdtemp(prefix="template-quality-"))
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

    def guard(self, dest: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", "scripts/check-suppressions"], cwd=dest, text=True, capture_output=True
        )

    def test_python_check_runs_every_gate(self) -> None:
        dest = self.render(project_type="python-api", include_github_actions=True)
        tasks = tomllib.loads((dest / "mise.toml").read_text())["tasks"]
        self.assertEqual(
            tasks["check"]["depends"], ["lint", "format-check", "test", "suppressions"]
        )
        project = tomllib.loads((dest / "pyproject.toml").read_text())
        self.assertLessEqual(
            {"PGH004", "RUF100"}, set(project["tool"]["ruff"]["lint"]["select"])
        )
        hooks = (dest / ".pre-commit-config.yaml").read_text()
        self.assertIn("entry: sh scripts/check-suppressions", hooks)
        self.assertIn("commitizen", hooks)
        workflow = (dest / ".github/workflows/ci.yml").read_text()
        self.assertIn("run: sh scripts/check-suppressions", workflow)
        self.assertIn("mise run check", (dest / "AGENTS.md").read_text())

    def test_pre_commit_can_still_be_declined(self) -> None:
        dest = self.render(project_type="python-api", include_pre_commit=False)
        self.assertFalse((dest / ".pre-commit-config.yaml").exists())

    def test_generic_check_is_not_a_no_op(self) -> None:
        dest = self.render(project_type="generic")
        tasks = tomllib.loads((dest / "mise.toml").read_text())["tasks"]
        self.assertEqual(tasks["check"]["depends"], ["suppressions"])
        self.assertIn("add the language's lint", (dest / "AGENTS.md").read_text())

    def test_guard_rejects_suppressions_until_a_reviewer_allows_them(self) -> None:
        dest = self.render(project_type="generic")
        for git in (False, True):
            with self.subTest(git=git):
                if git:
                    subprocess.run(["git", "init", "-q"], cwd=dest, check=True)
                self.assertEqual(self.guard(dest).returncode, 0)
                for text in (
                    "value = call()  # noqa: E501\n",
                    "value = call()  # type: ignore\n",
                    "@pytest.mark.skip\n",
                    "// eslint-disable-next-line no-console\n",
                    "it.only('focus', () => {})\n",
                ):
                    (dest / "app.py").write_text(text)
                    if git:
                        subprocess.run(["git", "add", "app.py"], cwd=dest, check=True)
                    result = self.guard(dest)
                    self.assertEqual(result.returncode, 1, text)
                    self.assertIn("app.py:1:", result.stderr)
                    self.assertIn("Fix the root cause", result.stderr)
                (dest / ".suppressions-allow").write_text(
                    "# vendored client cannot be typed\n^app\\.py:1:\n"
                )
                self.assertEqual(self.guard(dest).returncode, 0)
                (dest / "app.py").unlink()
                (dest / ".suppressions-allow").unlink()
                if git:
                    subprocess.run(["git", "add", "-A"], cwd=dest, check=True)

    def test_guard_ignores_markdown(self) -> None:
        dest = self.render(project_type="generic")
        (dest / "notes.md").write_text("Never add `# noqa` comments.\n")
        self.assertEqual(self.guard(dest).returncode, 0)


if __name__ == "__main__":
    unittest.main()
