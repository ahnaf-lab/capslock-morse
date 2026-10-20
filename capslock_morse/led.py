"""Abstraction over an LED brightness file.

A Linux keyboard LED (CapsLock, NumLock, ScrollLock) is controlled by writing
an integer to a sysfs brightness file, e.g.
``/sys/class/leds/input0::capslock/brightness``. This module wraps that file
path behind a small class so the rest of the daemon never has to know
whether it is poking a real LED or a throwaway file used in tests.
"""

from pathlib import Path

ON_VALUE = "1"
OFF_VALUE = "0"


class LED:
    """Turns a single LED on/off by writing to its brightness file."""

    def __init__(self, path):
        self.path = Path(path)

    def on(self):
        self._write(ON_VALUE)

    def off(self):
        self._write(OFF_VALUE)

    def set(self, state):
        self.on() if state else self.off()

    def is_on(self):
        return self._read() != OFF_VALUE

    def _write(self, value):
        self.path.write_text(value)

    def _read(self):
        if not self.path.exists():
            return OFF_VALUE
        return self.path.read_text().strip()
