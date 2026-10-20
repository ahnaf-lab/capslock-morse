"""Deterministic text/status -> Morse timing encoder.

Maps characters (and therefore whole words, status codes like ``PASS`` or
``FAIL``, or the first words of a commit message) onto a fixed table of
dot/dash patterns, then expands that into a sequence of LED on/off timing
units the rest of the daemon can blink out.

Standard ITU timing conventions are used throughout, measured in "units":
  * dot                   = 1 unit on
  * dash                  = 3 units on
  * gap between symbols   = 1 unit off   (within one character)
  * gap between characters = 3 units off (within one word)
  * gap between words      = 7 units off
"""

from typing import List, NamedTuple

DOT = "."
DASH = "-"

UNIT_DOT = 1
UNIT_DASH = 3
GAP_SYMBOL = 1
GAP_CHAR = 3
GAP_WORD = 7

MORSE_TABLE = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
}

# Deterministic shorthand for daemon status events, resolved to plain text
# and run through the same letter table above.
STATUS_CODES = {
    "PASS": "PASS",
    "FAIL": "FAIL",
    "OK": "OK",
    "ERROR": "ERROR",
}


class Signal(NamedTuple):
    """One LED state held for a number of timing units."""

    on: bool
    units: int


def encode_char(char: str) -> List[Signal]:
    """Return the on/off signal sequence for a single character.

    Includes the 1-unit gaps between symbols *within* the character, but not
    the longer gap that follows it between characters or words.
    """
    letter = char.upper()
    if letter not in MORSE_TABLE:
        raise ValueError(f"no Morse mapping for character {char!r}")

    signals: List[Signal] = []
    pattern = MORSE_TABLE[letter]
    for index, symbol in enumerate(pattern):
        units = UNIT_DOT if symbol == DOT else UNIT_DASH
        signals.append(Signal(True, units))
        if index != len(pattern) - 1:
            signals.append(Signal(False, GAP_SYMBOL))
    return signals


def encode(text: str) -> List[Signal]:
    """Encode arbitrary text into a full sequence of on/off Signals.

    Words are split on whitespace; a run of whitespace between words becomes
    a single inter-word gap. No trailing gap is appended after the final
    character.
    """
    words = text.split()
    if not words:
        return []

    signals: List[Signal] = []
    for word_index, word in enumerate(words):
        for char_index, char in enumerate(word):
            signals.extend(encode_char(char))
            if char_index != len(word) - 1:
                signals.append(Signal(False, GAP_CHAR))
        if word_index != len(words) - 1:
            signals.append(Signal(False, GAP_WORD))
    return signals


def encode_status(status: str) -> List[Signal]:
    """Encode a known daemon status code (e.g. ``"PASS"``, ``"FAIL"``).

    Falls back to encoding the status string itself when it is not one of
    the well-known codes, so arbitrary short text still works.
    """
    text = STATUS_CODES.get(status.upper(), status)
    return encode(text)
