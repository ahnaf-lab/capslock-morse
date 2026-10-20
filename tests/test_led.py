import tempfile
import unittest
from pathlib import Path

from capslock_morse.led import LED


class LEDTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.path = Path(self._tmpdir.name) / "brightness"

    def test_on_writes_one_and_reports_on(self):
        led = LED(self.path)
        led.on()
        self.assertEqual(self.path.read_text(), "1")
        self.assertTrue(led.is_on())

    def test_off_writes_zero_and_reports_off(self):
        led = LED(self.path)
        led.on()
        led.off()
        self.assertEqual(self.path.read_text(), "0")
        self.assertFalse(led.is_on())

    def test_set_true_turns_on_set_false_turns_off(self):
        led = LED(self.path)
        led.set(True)
        self.assertTrue(led.is_on())
        led.set(False)
        self.assertFalse(led.is_on())

    def test_accepts_plain_string_path(self):
        led = LED(str(self.path))
        led.on()
        self.assertTrue(led.is_on())

    def test_is_on_false_when_file_does_not_exist_yet(self):
        led = LED(self.path)
        self.assertFalse(self.path.exists())
        self.assertFalse(led.is_on())


if __name__ == "__main__":
    unittest.main()
