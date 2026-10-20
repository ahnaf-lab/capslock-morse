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

Run the test suite with:

```
python3 -m unittest discover -v
```

## Status

This project is built autonomously, one milestone at a time, and every
change is gated on its automated tests passing before it is accepted.
