import subprocess
import tempfile
import unittest
from pathlib import Path

from capslock_morse.events import (
    encode_commit_subject,
    encode_exit_code,
    exit_code_to_status,
    read_commit_subject,
    summarize_commit_subject,
)
from capslock_morse.morse import encode, encode_status


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


class ExitCodeTests(unittest.TestCase):
    def test_zero_is_pass(self):
        self.assertEqual(exit_code_to_status(0), "PASS")

    def test_nonzero_is_fail(self):
        self.assertEqual(exit_code_to_status(1), "FAIL")
        self.assertEqual(exit_code_to_status(127), "FAIL")

    def test_negative_is_fail(self):
        self.assertEqual(exit_code_to_status(-1), "FAIL")

    def test_encode_exit_code_matches_status_encoding(self):
        self.assertEqual(encode_exit_code(0), encode_status("PASS"))
        self.assertEqual(encode_exit_code(1), encode_status("FAIL"))


class SummarizeCommitSubjectTests(unittest.TestCase):
    def test_trims_to_max_words(self):
        self.assertEqual(
            summarize_commit_subject("fix the flaky build pipeline", max_words=3),
            "fix the flaky",
        )

    def test_short_subject_is_unchanged(self):
        self.assertEqual(summarize_commit_subject("fix bug", max_words=3), "fix bug")

    def test_default_max_words_is_three(self):
        self.assertEqual(
            summarize_commit_subject("one two three four five"), "one two three"
        )


class ReadCommitSubjectTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmpdir = Path(self._tmpdir.name)

    def test_reads_last_commit_subject(self):
        repo = _make_repo(self.tmpdir, "add deterministic morse timing encoder")
        subject = read_commit_subject(repo_path=repo)
        self.assertEqual(subject, "add deterministic morse timing encoder")

    def test_accepts_string_repo_path(self):
        repo = _make_repo(self.tmpdir, "add led wrapper")
        subject = read_commit_subject(repo_path=str(repo))
        self.assertEqual(subject, "add led wrapper")

    def test_rejects_unsafe_ref(self):
        repo = _make_repo(self.tmpdir, "add feature")
        with self.assertRaises(ValueError):
            read_commit_subject(repo_path=repo, ref="--upload-pack=evil")

    def test_rejects_ref_with_shell_metacharacters(self):
        repo = _make_repo(self.tmpdir, "add feature")
        with self.assertRaises(ValueError):
            read_commit_subject(repo_path=repo, ref="HEAD; rm -rf /")


class EncodeCommitSubjectTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmpdir = Path(self._tmpdir.name)

    def test_encodes_first_words_of_commit_subject(self):
        repo = _make_repo(self.tmpdir, "fix the flaky build pipeline")
        signals = encode_commit_subject(repo_path=repo, max_words=3)
        self.assertEqual(signals, encode("fix the flaky"))

    def test_respects_custom_word_count(self):
        repo = _make_repo(self.tmpdir, "fix the flaky build pipeline")
        signals = encode_commit_subject(repo_path=repo, max_words=2)
        self.assertEqual(signals, encode("fix the"))


if __name__ == "__main__":
    unittest.main()
