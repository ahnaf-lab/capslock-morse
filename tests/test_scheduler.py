import unittest

from capslock_morse.led import LED
from capslock_morse.morse import Signal, encode
from capslock_morse.scheduler import BlinkScheduler, play


class FakeLED:
    """Records every state it is set to, without touching the filesystem."""

    def __init__(self):
        self.states = []

    def set(self, state):
        self.states.append(state)


class FakeClock:
    """Records every sleep duration it is asked for, instead of sleeping."""

    def __init__(self):
        self.durations = []

    def sleep(self, duration):
        self.durations.append(duration)


class PlayTests(unittest.TestCase):
    def test_sets_led_state_for_each_signal_in_order(self):
        led = FakeLED()
        clock = FakeClock()
        signals = [Signal(True, 1), Signal(False, 1), Signal(True, 3)]
        play(led, signals, unit_seconds=0.05, sleep=clock.sleep)
        self.assertEqual(led.states, [True, False, True])

    def test_sleeps_for_units_times_unit_seconds(self):
        led = FakeLED()
        clock = FakeClock()
        signals = [Signal(True, 1), Signal(False, 3), Signal(True, 7)]
        play(led, signals, unit_seconds=0.1, sleep=clock.sleep)
        for actual, expected in zip(clock.durations, [0.1, 0.3, 0.7]):
            self.assertAlmostEqual(actual, expected)

    def test_full_letter_has_correct_relative_timing(self):
        # "A" = .-  -> dot, 1-unit symbol gap, dash
        led = FakeLED()
        clock = FakeClock()
        play(led, encode("A"), unit_seconds=1, sleep=clock.sleep)
        self.assertEqual(led.states, [True, False, True])
        self.assertEqual(clock.durations, [1, 1, 3])

    def test_zero_duration_signal_does_not_call_sleep(self):
        led = FakeLED()
        clock = FakeClock()
        play(led, [Signal(True, 0)], unit_seconds=1, sleep=clock.sleep)
        self.assertEqual(clock.durations, [])

    def test_works_against_real_led_file(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brightness"
            led = LED(path)
            clock = FakeClock()
            play(led, [Signal(True, 1), Signal(False, 1)], unit_seconds=0.01, sleep=clock.sleep)
            self.assertEqual(path.read_text(), "0")


class BlinkSchedulerTests(unittest.TestCase):
    def test_run_pending_plays_all_queued_sequences_in_order(self):
        led = FakeLED()
        clock = FakeClock()
        scheduler = BlinkScheduler(led, unit_seconds=1, sleep=clock.sleep)
        scheduler.submit([Signal(True, 1)])
        scheduler.submit([Signal(False, 2)])
        played = scheduler.run_pending()
        self.assertEqual(played, 2)
        self.assertEqual(led.states, [True, False])
        self.assertEqual(clock.durations, [1, 2])

    def test_run_pending_returns_zero_when_queue_empty(self):
        led = FakeLED()
        scheduler = BlinkScheduler(led, unit_seconds=1, sleep=lambda d: None)
        self.assertEqual(scheduler.run_pending(), 0)

    def test_run_forever_stops_on_stop_request(self):
        led = FakeLED()
        clock = FakeClock()
        scheduler = BlinkScheduler(led, unit_seconds=1, sleep=clock.sleep)
        scheduler.submit([Signal(True, 1)])
        scheduler.submit([Signal(True, 3)])
        scheduler.stop()
        played = scheduler.run_forever()
        self.assertEqual(played, 2)
        self.assertEqual(led.states, [True, True])
        self.assertEqual(clock.durations, [1, 3])

    def test_pending_count_reflects_queued_work(self):
        led = FakeLED()
        scheduler = BlinkScheduler(led, unit_seconds=1, sleep=lambda d: None)
        self.assertEqual(scheduler.pending_count(), 0)
        scheduler.submit([Signal(True, 1)])
        scheduler.submit([Signal(True, 1)])
        self.assertEqual(scheduler.pending_count(), 2)

    def test_stop_without_prior_submit_runs_forever_zero_times(self):
        led = FakeLED()
        scheduler = BlinkScheduler(led, unit_seconds=1, sleep=lambda d: None)
        scheduler.stop()
        self.assertEqual(scheduler.run_forever(), 0)
        self.assertEqual(led.states, [])


if __name__ == "__main__":
    unittest.main()
