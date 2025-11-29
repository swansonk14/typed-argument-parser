"""
Typed Argument Parser
"""

__version__ = "1.11.0"

from argparse import ArgumentError, ArgumentTypeError

from tap.tap import Tap
from tap.tapify import tapify, to_tap_class
from tap.utils import TapIgnore

__all__ = [
    "ArgumentError",
    "ArgumentTypeError",
    "Tap",
    "TapIgnore",
    "tapify",
    "to_tap_class",
    "__version__",
]
