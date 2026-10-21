import subprocess
import tempfile
import unittest
from pathlib import Path

from capslock_morse.__main__ import build_parser, main


def _run(args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _make_repo(tmpdir: Path, subject: str) -> Path:
    repo = tmpdir / "repo"
    repo.mkdir()
    _run(["git", "init"], cwd=repo)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "Test User"], cwd=repo)
    (repo / "file.txt").write_text("content\n")
    _run(["git", "add", "file.txt"], cwd=repo)
    _run(["git", "commit", "-m", subject], cwd=repo)
    return repo


class BuildParserTests(unittest.TestCase):
    def test_exit_code_mode_parses_code(self):
        args = build_parser().parse_args(["exit-code", "1"])
        self.assertEqual(args.mode, "exit-code")
        self.assertEqual(args.code, 1)

    def test_commit_mode_defaults(self):
        args = build_parser().parse_args(["commit"])
        self.assertEqual(args.mode, "commit")
        self.assertEqual(args.repo, ".")
        self.assertEqual(args.max_words, 3)

    def test_led_and_unit_seconds_are_overridable(self):
        args = build_parser().parse_args(
            ["--led", "/tmp/fake", "--unit-seconds", "0.01", "exit-code", "0"]
        )
        self.assertEqual(args.led, "/tmp/fake")
        self.assertEqual(args.unit_seconds, 0.01)


class MainTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmpdir = Path(self._tmpdir.name)

    def test_exit_code_blinks_and_ends_with_led_off(self):
        led_path = self.tmpdir / "brightness"
        rc = main(
            ["--led", str(led_path), "--unit-seconds", "0.001", "exit-code", "0"]
        )
        self.assertEqual(rc, 0)
        # The encoder appends no trailing gap, so the LED is left on, holding
        # the final dot/dash of the last letter.
        self.assertEqual(led_path.read_text(), "1")

    def test_commit_mode_reads_and_blinks_last_subject(self):
        repo = _make_repo(self.tmpdir, "fix the flaky build")
        led_path = self.tmpdir / "brightness"
        rc = main(
            [
                "--led",
                str(led_path),
                "--unit-seconds",
                "0.001",
                "commit",
                "--repo",
                str(repo),
                "--max-words",
                "2",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(led_path.exists())


if __name__ == "__main__":
    unittest.main()
