from copy import deepcopy
import sys
from tempfile import NamedTemporaryFile
from typing import Any, List, Optional, Set, Tuple
from typing_extensions import Literal
import unittest
from unittest import TestCase

from tap import Tap


class LoadConfigFilesTests(TestCase):
    def test_file_does_not_exist(self) -> None:
        class EmptyTap(Tap):
            pass

        with self.assertRaises(FileNotFoundError):
            EmptyTap(config_files=['nope']).parse_args([])

    def test_single_config_file(self) -> None:
        class SimpleTap(Tap):
            a: int
            b: str = 'b'

        with NamedTemporaryFile() as f:
            f.write(b'--a 1')
            f.flush()
            args = SimpleTap(config_files=[f.name]).parse_args([])

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 'b')

    def test_single_config_file_overwriting(self) -> None:
        pass

    def test_multiple_config_files(self) -> None:
        pass

    def test_multiple_config_files_overwriting(self) -> None:
        pass
    #     hi = 'yo'
    #     args = EmptyAddArgument().parse_args(['--hi', hi])
    #     self.assertEqual(args.hi, hi)


if __name__ == '__main__':
    unittest.main()
