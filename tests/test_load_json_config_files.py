import os
import sys
from tempfile import TemporaryDirectory
import unittest
from typing import List
from unittest import TestCase

from tap import Tap
from tap.tap_config import TapConfig


class LoadConfigFilesTests(TestCase):

    def setUp(self) -> None:
        class DevNull:
            def write(self, msg):
                pass
        self.dev_null = DevNull()

    def test_single_config(self) -> None:
        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.json')

            class SimpleTap(Tap):
                a: int
                b: str = 'b'
                conf: TapConfig = None

            with open(fname, 'w') as f:
                f.write('{"a": 1.1}')

            args = SimpleTap().parse_args(f'--conf {fname}'.split(' '))

        self.assertEqual(args.a, 1.1)
        self.assertEqual(args.b, 'b')

    def test_json_config(self) -> None:
        class SimpleTap(Tap):
            a: float
            b: str
            c: str = 'c'
            d: int
            e: List[int]

        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.json')

            with open(fname, 'w') as f:
                # note: numeric args can be quoted or not in json
                f.write('{"a": "1.1", "b": "value for b", "d": 4, "e": [7, 8, 9]}')

            args = SimpleTap(config_files=[fname]).parse_args([])

        self.assertEqual(args.a, 1.1)
        self.assertEqual(args.b, 'value for b')
        self.assertEqual(args.c, 'c')
        self.assertEqual(args.d, 4)
        self.assertEqual(args.e, [7, 8, 9])

    def test_single_config_overwriting(self) -> None:
        class SimpleOverwritingTap(Tap):
            a: int
            b: str = 'b'

        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.txt')

            with open(fname, 'w') as f:
                f.write('--a 1 --b two')

            args = SimpleOverwritingTap(config_files=[fname]).parse_args('--a 2'.split())

        self.assertEqual(args.a, 2)
        self.assertEqual(args.b, 'two')

    def test_single_json_config_overwriting(self) -> None:
        class SimpleOverwritingTap(Tap):
            a: int
            b: str = 'b'

        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.json')

            with open(fname, 'w') as f:
                f.write('{"a": 1, "b": "b two"}')

            args = SimpleOverwritingTap(config_files=[fname]).parse_args('--a 2'.split())

        self.assertEqual(args.a, 2)
        self.assertEqual(args.b, 'b two')

    def test_single_config_known_only(self) -> None:
        class KnownOnlyTap(Tap):
            a: int
            b: str = 'b'

        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.txt')

            with open(fname, 'w') as f:
                f.write('--a 1 --c seeNothing')

            args = KnownOnlyTap(config_files=[fname]).parse_args([], known_only=True)

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 'b')
        self.assertEqual(args.extra_args, ['--c', 'seeNothing'])

    def test_single_config_required_still_required(self) -> None:
        class KnownOnlyTap(Tap):
            a: int
            b: str = 'b'

        with TemporaryDirectory() as temp_dir, self.assertRaises(SystemExit):
            sys.stderr = self.dev_null
            fname = os.path.join(temp_dir, 'config.txt')

            with open(fname, 'w') as f:
                f.write('--b fore')

            KnownOnlyTap(config_files=[fname]).parse_args([])

    def test_multiple_configs(self) -> None:
        class MultipleTap(Tap):
            a: int
            b: str = 'b'

        with TemporaryDirectory() as temp_dir:
            fname1, fname2 = os.path.join(temp_dir, 'config1.txt'), os.path.join(temp_dir, 'config2.txt')

            with open(fname1, 'w') as f1, open(fname2, 'w') as f2:
                f1.write('--b two')
                f2.write('--a 1')

            args = MultipleTap(config_files=[fname1, fname2]).parse_args([])

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 'two')

    def test_multiple_configs_overwriting(self) -> None:
        class MultipleOverwritingTap(Tap):
            a: int
            b: str = 'b'
            c: str = 'c'

        with TemporaryDirectory() as temp_dir:
            fname1, fname2 = os.path.join(temp_dir, 'config1.txt'), os.path.join(temp_dir, 'config2.txt')

            with open(fname1, 'w') as f1, open(fname2, 'w') as f2:
                f1.write('--a 1 --b two')
                f2.write('--a 2 --c see')

            args = MultipleOverwritingTap(config_files=[fname1, fname2]).parse_args('--b four'.split())

        self.assertEqual(args.a, 2)
        self.assertEqual(args.b, 'four')
        self.assertEqual(args.c, 'see')

    def test_junk_config(self) -> None:
        class JunkConfigTap(Tap):
            a: int
            b: str = 'b'

        with TemporaryDirectory() as temp_dir, self.assertRaises(SystemExit):
            sys.stderr = self.dev_null
            fname = os.path.join(temp_dir, 'config.txt')

            with open(fname, 'w') as f:
                f.write('is not a file that can reasonably be parsed')

            JunkConfigTap(config_files=[fname]).parse_args([])

    def test_shlex_config(self) -> None:
        class ShlexConfigTap(Tap):
            a: int
            b: str

        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.txt')

            with open(fname, 'w') as f:
                f.write('--a 21 # Important arg value\n\n# Multi-word quoted string\n--b "two three four"')

            args = ShlexConfigTap(config_files=[fname]).parse_args([])

        self.assertEqual(args.a, 21)
        self.assertEqual(args.b, 'two three four')



if __name__ == '__main__':
    unittest.main()
