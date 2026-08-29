"""
Typed Argument Parser
"""

__version__ = "1.12.0"

from argparse import ArgumentError, ArgumentTypeError

from tap.tap import Tap
from tap.tapify import tapify, to_tap_class
from tap.to_argv import to_argv
from tap.utils import Positional, TapIgnore

__all__ = [
    "ArgumentError",
    "ArgumentTypeError",
    "Positional",
    "Tap",
    "TapIgnore",
    "tapify",
    "to_argv",
    "to_tap_class",
    "__version__",
]
