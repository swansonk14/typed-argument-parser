"""
Typed Argument Parser
"""

__version__ = "1.10.1"

from argparse import ArgumentError, ArgumentTypeError
from tap.tap import Tap
from tap.tapify import tapify, to_tap_class

__all__ = [
    "ArgumentError",
    "ArgumentTypeError",
    "Tap",
    "tapify",
    "to_tap_class",
    "__version__",
]
