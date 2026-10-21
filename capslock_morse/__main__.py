"""Command-line entry point: blink one build/test/git event out on an LED.

Usage is split into two subcommands -- ``exit-code`` for a build/test
result, and ``commit`` for the last commit's subject -- both of which end up
encoded into :class:`~capslock_morse.morse.Signal` steps and played out on a
real LED brightness file via :class:`~capslock_morse.scheduler.BlinkScheduler`.
"""

import argparse
import sys
from typing import List, Optional

from .events import encode_commit_subject, encode_exit_code
from .led import LED
from .scheduler import DEFAULT_UNIT_SECONDS, BlinkScheduler

DEFAULT_LED_PATH = "/sys/class/leds/input0::capslock/brightness"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="capslock-morse",
        description="Blink a build/test/git event out in Morse on a keyboard LED.",
    )
    parser.add_argument(
        "--led",
        default=DEFAULT_LED_PATH,
        help="path to the LED brightness file to blink (default: %(default)s)",
    )
    parser.add_argument(
        "--unit-seconds",
        type=float,
        default=DEFAULT_UNIT_SECONDS,
        help="duration of one Morse unit in seconds (default: %(default)s)",
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    exit_code_parser = subparsers.add_parser(
        "exit-code", help="blink PASS/FAIL for a build/test process exit code"
    )
    exit_code_parser.add_argument("code", type=int, help="process exit code")

    commit_parser = subparsers.add_parser(
        "commit", help="blink the first words of the last git commit subject"
    )
    commit_parser.add_argument(
        "--repo", default=".", help="path to the git repository (default: %(default)s)"
    )
    commit_parser.add_argument(
        "--max-words",
        type=int,
        default=3,
        help="number of leading words to blink (default: %(default)s)",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.mode == "exit-code":
        signals = encode_exit_code(args.code)
    else:
        signals = encode_commit_subject(repo_path=args.repo, max_words=args.max_words)

    led = LED(args.led)
    scheduler = BlinkScheduler(led, unit_seconds=args.unit_seconds)
    scheduler.submit(signals)
    scheduler.stop()
    scheduler.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
