"""End-to-end "fake hardware" tests for milestone 5.

Unlike the unit tests elsewhere (which use an in-memory FakeLED, or check
morse encoding and LED file writes in isolation), these tests run the real
pipeline -- event adapter -> morse encoder -> BlinkScheduler -> LED -- against
a real throwaway LED brightness file, and assert the exact sequence of
(timestamp, on/off) writes produced for fixed, known events. A FakeClock
supplies virtual time so the assertions are exact and the suite runs
instantly instead of for real wall-clock seconds.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from capslock_morse.events import encode_commit_subject, encode_exit_code
from capslock_morse.led import LED
from capslock_morse.morse import Signal, encode_status
from capslock_morse.scheduler import BlinkScheduler

UNIT_SECONDS = 0.1


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


def _expected_timeline(
    signals: List[Signal], unit_seconds: float
) -> List[Tuple[float, bool]]:
    """Independently reconstruct the (timestamp, state) writes `play()`
    should produce: each signal is written at the virtual clock time all
    *previous* signals' durations add up to."""
    timeline = []
    now = 0.0
    for signal in signals:
        timeline.append((now, signal.on))
        now += signal.units * unit_seconds
    return timeline


class FakeClock:
    """A virtual clock: advances on `sleep()` instead of blocking for real."""

    def __init__(self):
        self.now = 0.0

    def sleep(self, duration):
        self.now += duration


class RecordingLED(LED):
    """A real LED file wrapper that also timestamps every write against a
    FakeClock, standing in for a physical keyboard LED in these tests."""

    def __init__(self, path, clock: FakeClock):
        super().__init__(path)
        self.clock = clock
        self.events: List[Tuple[float, bool]] = []

    def on(self):
        super().on()
        self.events.append((self.clock.now, True))

    def off(self):
        super().off()
        self.events.append((self.clock.now, False))


class FakeHardwareTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmpdir = Path(self._tmpdir.name)
        self.led_path = self.tmpdir / "brightness"
        self.clock = FakeClock()
        self.led = RecordingLED(self.led_path, self.clock)
        self.scheduler = BlinkScheduler(
            self.led, unit_seconds=UNIT_SECONDS, sleep=self.clock.sleep
        )

    def _play(self, signals: List[Signal]) -> int:
        self.scheduler.submit(signals)
        self.scheduler.stop()
        return self.scheduler.run_forever()

    def test_pass_exit_code_produces_exact_on_off_timeline(self):
        signals = encode_exit_code(0)
        played = self._play(signals)
        self.assertEqual(played, 1)
        self.assertEqual(
            self.led.events, _expected_timeline(signals, UNIT_SECONDS)
        )
        # "PASS" ends on an "S", whose last symbol is a dot -> LED left on.
        self.assertEqual(self.led_path.read_text(), "1")

    def test_fail_exit_code_produces_exact_on_off_timeline(self):
        signals = encode_exit_code(1)
        played = self._play(signals)
        self.assertEqual(played, 1)
        self.assertEqual(
            self.led.events, _expected_timeline(signals, UNIT_SECONDS)
        )
        self.assertEqual(self.led_path.read_text(), "1")

    def test_known_short_status_has_hand_verified_timeline(self):
        # "OK": O = "---", K = "-.-", with a 3-unit gap between them.
        # At 0.1s/unit this is a fully hand-computed, literal timeline.
        signals = encode_status("OK")
        self._play(signals)
        expected = [
            (0.0, True),
            (0.3, False),
            (0.4, True),
            (0.7, False),
            (0.8, True),
            (1.1, False),
            (1.4, True),
            (1.7, False),
            (1.8, True),
            (1.9, False),
            (2.0, True),
        ]
        self.assertEqual(len(self.led.events), len(expected))
        for (actual_t, actual_on), (expected_t, expected_on) in zip(
            self.led.events, expected
        ):
            self.assertAlmostEqual(actual_t, expected_t)
            self.assertEqual(actual_on, expected_on)

    def test_commit_subject_event_produces_exact_on_off_timeline(self):
        repo = _make_repo(self.tmpdir, "fix the flaky build pipeline")
        signals = encode_commit_subject(repo_path=repo, max_words=2)
        played = self._play(signals)
        self.assertEqual(played, 1)
        self.assertEqual(
            self.led.events, _expected_timeline(signals, UNIT_SECONDS)
        )
        # "fix the" starts with "F" = "..-.", a dot -> first write is on.
        self.assertEqual(self.led.events[0], (0.0, True))

    def test_multiple_fixed_events_play_back_to_back_in_order(self):
        pass_signals = encode_exit_code(0)
        fail_signals = encode_exit_code(1)
        self.scheduler.submit(pass_signals)
        self.scheduler.submit(fail_signals)
        self.scheduler.stop()
        played = self.scheduler.run_forever()

        self.assertEqual(played, 2)
        # The second sequence's clock keeps running from where the first
        # left off -- no real-world gap is inserted between submissions --
        # so the expected timeline is one continuous accumulation across
        # both sequences, not two independent ones stitched together.
        combined_expected = _expected_timeline(
            pass_signals + fail_signals, UNIT_SECONDS
        )
        self.assertEqual(self.led.events, combined_expected)


if __name__ == "__main__":
    unittest.main()
