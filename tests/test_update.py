from pathlib import Path
import os
import subprocess
import tempfile
import unittest


class CopierUpdateTests(unittest.TestCase):
    def run_command(self, *command: str, cwd: Path | None = None) -> str:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
        )
        if result.returncode:
            raise AssertionError(f"{command!r} failed:\n{result.stderr}")
        return result.stdout

    def test_update_uses_local_template_and_preserves_user_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            template = root / "template"
            project = root / "project"
            template.mkdir()

            (template / "copier.yml").write_text(
                "_min_copier_version: '9.0.0'\n"
                "_answers_file: .copier-answers.yml\n"
                "project_name:\n"
                "  type: str\n"
                "  default: example\n"
            )
            readme_template = template / "README.md.jinja"
            readme_template.write_text("Generated from the initial template.\n")
            (template / ".copier-answers.yml.jinja").write_text(
                f"_src_path: {template}\n"
                "_commit: {{ _copier_conf.vcs_ref }}\n"
                "project_name: {{ project_name }}\n"
            )

            self.run_command("git", "init", str(template))
            self.run_command("git", "-C", str(template), "config", "user.name", "Test User")
            self.run_command(
                "git", "-C", str(template), "config", "user.email", "test@example.invalid"
            )
            self.run_command("git", "-C", str(template), "add", ".")
            self.run_command("git", "-C", str(template), "commit", "-m", "initial template")
            self.run_command("git", "-C", str(template), "tag", "v1.0.0")

            copy_output = self.run_command(
                "copier",
                "copy",
                "--defaults",
                "--trust",
                "--answers-file",
                ".copier-answers.yml",
                "--vcs-ref",
                "v1.0.0",
                str(template),
                str(project),
            )
            self.assertTrue((project / ".copier-answers.yml").exists(), copy_output)
            (project / "user-notes.txt").write_text("Keep this user-owned file.\n")
            self.run_command("git", "init", str(project))
            self.run_command("git", "-C", str(project), "config", "user.name", "Test User")
            self.run_command(
                "git", "-C", str(project), "config", "user.email", "test@example.invalid"
            )
            self.run_command("git", "-C", str(project), "add", ".")
            self.run_command("git", "-C", str(project), "commit", "-m", "rendered project")

            readme_template.write_text("Generated from the updated template.\n")
            self.run_command("git", "-C", str(template), "add", ".")
            self.run_command("git", "-C", str(template), "commit", "-m", "update template")
            self.run_command("git", "-C", str(template), "tag", "v2.0.0")
            answers_before_update = (project / ".copier-answers.yml").read_text()
            self.assertIn(f"_src_path: {template}", answers_before_update)
            self.assertIn("_commit:", answers_before_update, answers_before_update)

            self.run_command(
                "copier",
                "update",
                "--defaults",
                "--trust",
                "--answers-file",
                ".copier-answers.yml",
                "--vcs-ref",
                "v2.0.0",
                str(project),
            )

            self.assertEqual(
                (project / "README.md").read_text(), "Generated from the updated template.\n"
            )
            self.assertEqual(
                (project / "user-notes.txt").read_text(), "Keep this user-owned file.\n"
            )
            answers = (project / ".copier-answers.yml").read_text()
            self.assertIn(f"_src_path: {template}", answers)
            self.assertIn("_commit: v2.0.0", answers)


if __name__ == "__main__":
    unittest.main()
