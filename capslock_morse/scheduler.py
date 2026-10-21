"""Blink scheduler: drives an :class:`~capslock_morse.led.LED` through a
sequence of :class:`~capslock_morse.morse.Signal` steps with real-world
timing, and a small daemon loop that keeps doing that for whatever sequences
get submitted to it.

The timing unit is one "dot" of Morse code. Everything else (dashes, gaps)
is expressed as a multiple of it in :mod:`capslock_morse.morse`, so this
module's only job is to turn ``units`` into ``units * unit_seconds`` and feed
that to the LED and a sleep function in order.
"""

import queue
import time
from typing import Callable, Iterable, Optional

from .led import LED
from .morse import Signal

# 0.1s per unit is a brisk but readable rate (a dash is 0.3s, a letter gap is
# 0.3s, a word gap is 0.7s) -- comfortably glanceable without feeling laggy.
DEFAULT_UNIT_SECONDS = 0.1


def play(
    led: LED,
    signals: Iterable[Signal],
    unit_seconds: float = DEFAULT_UNIT_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Drive ``led`` through ``signals``, holding each state for its duration.

    ``sleep`` is injectable so tests can run this without real wall-clock
    delays. The LED is left in whatever state the last signal set it to; most
    encoded sequences end with the LED off, but this function does not force
    that itself.
    """
    for signal in signals:
        led.set(signal.on)
        duration = signal.units * unit_seconds
        if duration > 0:
            sleep(duration)


class BlinkScheduler:
    """A tiny daemon loop: submit signal sequences, and it blinks them out.

    Sequences are played strictly in submission order on a single LED. This
    is deliberately not threaded -- the daemon process is expected to call
    :meth:`run_forever` (or :meth:`run_pending` for a single drain) from its
    own main loop after submitting the next event's signals.
    """

    _STOP = object()

    def __init__(
        self,
        led: LED,
        unit_seconds: float = DEFAULT_UNIT_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.led = led
        self.unit_seconds = unit_seconds
        self.sleep = sleep
        self._queue: "queue.Queue" = queue.Queue()

    def submit(self, signals: Iterable[Signal]) -> None:
        """Queue a signal sequence to be blinked out."""
        self._queue.put(list(signals))

    def stop(self) -> None:
        """Queue a request to stop :meth:`run_forever` once it is reached."""
        self._queue.put(self._STOP)

    def pending_count(self) -> int:
        return self._queue.qsize()

    def run_pending(self) -> int:
        """Play every sequence currently queued, without blocking for more.

        Returns the number of sequences played. A queued :meth:`stop` request
        is consumed and stops the drain early.
        """
        played = 0
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if item is self._STOP:
                break
            play(self.led, item, unit_seconds=self.unit_seconds, sleep=self.sleep)
            played += 1
        return played

    def run_forever(self, timeout: Optional[float] = None) -> int:
        """Block, playing sequences as they're submitted, until :meth:`stop`.

        Returns the number of sequences played. ``timeout`` bounds each wait
        for the next item (passed straight to the underlying queue); leave it
        ``None`` for a real daemon loop that waits indefinitely.
        """
        played = 0
        while True:
            item = self._queue.get(timeout=timeout)
            if item is self._STOP:
                break
            play(self.led, item, unit_seconds=self.unit_seconds, sleep=self.sleep)
            played += 1
        return played
