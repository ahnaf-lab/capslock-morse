# capslock-morse

A zero-dependency daemon that watches your build/test/git events and blinks
the result out in actual Morse code on your keyboard's CapsLock, NumLock and
ScrollLock LEDs — no screen required, just three lights telling you PASS,
FAIL, or the first words of your last commit message.

## Install

Requires Python 3.9+ and nothing else — the project has no third-party
dependencies, by design. Clone the repository and run it with the system
Python interpreter:

```
git clone <repo-url>
cd capslock-morse
```

## Usage

So far the project provides `capslock_morse.led.LED`, a small wrapper around
an LED brightness file. On Linux, keyboard LEDs are controlled by writing an
integer to a sysfs file such as
`/sys/class/leds/input0::capslock/brightness`. `LED` wraps any such path
(real or, in tests, a throwaway file) behind `on()` / `off()` / `set()` /
`is_on()`:

```python
from capslock_morse.led import LED

caps = LED("/sys/class/leds/input0::capslock/brightness")
caps.on()
caps.off()
caps.set(True)
print(caps.is_on())
```

The project also provides `capslock_morse.morse`, a deterministic encoder
that turns text or daemon status codes (`PASS`, `FAIL`, `OK`, `ERROR`) into
a sequence of `Signal(on, units)` timing steps using standard dot/dash
timing (dot = 1 unit, dash = 3 units, with 1/3/7-unit gaps between symbols,
characters, and words):

```python
from capslock_morse.morse import encode, encode_status

encode("SOS")      # -> list of Signal(on, units) steps spelling S-O-S
encode_status("PASS")  # same, for a well-known status code
```

Run the test suite with:

```
python3 -m unittest discover -v
```

## Status

This project is built autonomously, one milestone at a time, and every
change is gated on its automated tests passing before it is accepted.
