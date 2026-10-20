"""Event adapter: turns build/test exit codes and git commit subjects into
encodable messages for the Morse signal pipeline.

This module is the only place that shells out (to ``git``), and it only ever
does so with a fixed argument list — never through a shell, and never with a
ref string that has not been validated against :data:`_REF_PATTERN` — so a
hostile branch name or commit subject cannot inject extra git options or
commands.
"""

import re
import subprocess
from pathlib import Path
from typing import List

from .morse import Signal, encode, encode_status

DEFAULT_MAX_WORDS = 3

# Git refs/revisions we accept: letters, digits, and the handful of
# punctuation characters git itself allows in ref names. Anything else
# (spaces, shell metacharacters, a leading "-" that could be parsed as an
# option) is rejected before it ever reaches subprocess.
_REF_PATTERN = re.compile(r"^[A-Za-z0-9_./-]+$")


def exit_code_to_status(code: int) -> str:
    """Map a process exit code to a daemon status code.

    Follows standard POSIX convention: ``0`` means success (``PASS``), any
    other code means failure (``FAIL``).
    """
    return "PASS" if code == 0 else "FAIL"


def encode_exit_code(code: int) -> List[Signal]:
    """Encode a build/test process exit code directly into Morse signals."""
    return encode_status(exit_code_to_status(code))


def _validate_ref(ref: str) -> None:
    if not ref or ref.startswith("-") or not _REF_PATTERN.match(ref):
        raise ValueError(f"unsafe or malformed git ref: {ref!r}")


def read_commit_subject(repo_path=".", ref: str = "HEAD") -> str:
    """Return the subject line (first line) of a git commit message.

    ``repo_path`` is passed to ``git -C`` so the lookup can target any
    checkout without changing the process's working directory. ``ref`` is
    validated with :func:`_validate_ref` before use.
    """
    _validate_ref(ref)
    result = subprocess.run(
        ["git", "-C", str(repo_path), "log", "-1", "--format=%s", ref],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def summarize_commit_subject(subject: str, max_words: int = DEFAULT_MAX_WORDS) -> str:
    """Trim a commit subject down to its first ``max_words`` words.

    Full commit subjects can be far too long to blink out comfortably, so the
    daemon only ever signals the first few words.
    """
    words = subject.split()
    return " ".join(words[:max_words])


def encode_commit_subject(
    repo_path=".", ref: str = "HEAD", max_words: int = DEFAULT_MAX_WORDS
) -> List[Signal]:
    """Read the last commit's subject and encode its first words as Morse."""
    subject = read_commit_subject(repo_path=repo_path, ref=ref)
    return encode(summarize_commit_subject(subject, max_words=max_words))
