import os
import sys
from tempfile import TemporaryDirectory
import unittest
from typing import List
from unittest import TestCase

from tap import Tap
from tap.config_file import ConfigFile


class LoadConfigFilesTests(TestCase):

    def setUp(self) -> None:
        class DevNull:
            def write(self, msg):
                pass
        self.dev_null = DevNull()

    def test_simple(self) -> None:
        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.json')

            class SimpleTap(Tap):
                a: float
                b: str = 'b'
                conf: ConfigFile = None

            with open(fname, 'w') as f:
                f.write('{"a": 1.1}')

            args = SimpleTap().parse_args(f'--conf {fname}'.split(' '))

        self.assertEqual(args.a, 1.1)
        self.assertEqual(args.b, 'b')

    def test_lists(self) -> None:
        class SimpleTap(Tap):
            a: List[int]
            b: List[str]
            c: List[float]
            conf: ConfigFile = None

        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.json')

            with open(fname, 'w') as f:
                f.write('{"a": [7, 8, 9], "b": ["foo", "bar"], "c": [2.34, 5.67]}')

            args = SimpleTap().parse_args(f'--conf {fname}'.split(' '))

        self.assertEqual(args.a, [7, 8, 9])
        self.assertEqual(args.b, ["foo", "bar"])
        self.assertEqual(args.c, [2.34, 5.67])

    def test_strings_with_spaces(self) -> None:
        class SimpleTap(Tap):
            a: int
            b: str
            c: str = 'c'
            conf: ConfigFile = None

        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.json')

            with open(fname, 'w') as f:
                f.write('{"a": 1, "b": "value for b"}')

            args = SimpleTap().parse_args(f'--conf {fname}'.split(' '))

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 'value for b')
        self.assertEqual(args.c, 'c')

    def test_single_config_overwriting(self) -> None:
        class SimpleOverwritingTap(Tap):
            a: int
            b: str = 'b'
            conf: ConfigFile = None

        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.json')

            with open(fname, 'w') as f:
                f.write('{"a": 1, "b": "b two"}')

            args = SimpleOverwritingTap().parse_args(f'--conf {fname} --a 2'.split())

        self.assertEqual(args.a, 2)
        self.assertEqual(args.b, 'b two')

    def test_single_config_known_only(self) -> None:
        class KnownOnlyTap(Tap):
            a: int
            b: str = 'b'
            conf: ConfigFile = None

        with TemporaryDirectory() as temp_dir:
            fname = os.path.join(temp_dir, 'config.json')

            with open(fname, 'w') as f:
                f.write('{"a": 1, "c": "seeNothing"}')

            # in this case allow_abbrev=False stops "--c" being interpreted
            # as an abbreviation for "--conf"
            args = KnownOnlyTap(allow_abbrev=False).parse_args(f'--conf {fname}'.split(), known_only=True)

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 'b')
        self.assertEqual(args.extra_args, ['--c', 'seeNothing'])

    def test_single_config_required_still_required(self) -> None:
        class KnownOnlyTap(Tap):
            a: int
            b: str = 'b'
            conf: ConfigFile = None

        with TemporaryDirectory() as temp_dir, self.assertRaises(SystemExit):
            sys.stderr = self.dev_null
            fname = os.path.join(temp_dir, 'config.json')

            with open(fname, 'w') as f:
                f.write('{"b": "fore"}')

            KnownOnlyTap().parse_args(f'--conf {fname}'.split()).parse_args([])

    def test_multiple_configs(self) -> None:
        class MultipleTap(Tap):
            a: List[int]
            b: str = 'b'
            conf: List[ConfigFile] = []

        with TemporaryDirectory() as temp_dir:
            fname1, fname2 = os.path.join(temp_dir, 'config1.json'), os.path.join(temp_dir, 'config2.json')

            with open(fname1, 'w') as f1, open(fname2, 'w') as f2:
                f1.write('{"b": "two"}')
                f2.write('{"a": [1, 2]}')

            args = MultipleTap().parse_args(f"--conf {fname1} {fname2}".split())

        self.assertEqual(args.a, [1, 2])
        self.assertEqual(args.b, 'two')

    def test_multiple_configs_overwriting(self) -> None:
        class MultipleOverwritingTap(Tap):
            a: int
            b: str = 'b'
            c: str = 'c'
            conf: List[ConfigFile] = []

        with TemporaryDirectory() as temp_dir:
            fname1, fname2 = os.path.join(temp_dir, 'config1.json'), os.path.join(temp_dir, 'config2.json')

            with open(fname1, 'w') as f1, open(fname2, 'w') as f2:
                f1.write('{"a": 1, "b": "two"}')
                f2.write('{"a": 2, "c": "see"}')

            args = MultipleOverwritingTap().parse_args(f"--conf {fname1} {fname2} --b four".split())

        self.assertEqual(args.a, 2)
        self.assertEqual(args.b, 'four')
        self.assertEqual(args.c, 'see')

    def test_json_and_text_configs_overwriting(self) -> None:
        class MultipleOverwritingTap(Tap):
            a: int
            b: str = 'b'
            c: str = 'c'
            conf: List[ConfigFile] = []

        with TemporaryDirectory() as temp_dir:
            fname1, fname2 = os.path.join(temp_dir, 'config1.json'), os.path.join(temp_dir, 'config2.txt')

            with open(fname1, 'w') as f1, open(fname2, 'w') as f2:
                f1.write('{"a": 1, "b": "two"}')
                f2.write('--a 2 --c see')

            args = MultipleOverwritingTap().parse_args(f"--conf {fname1} {fname2} --b four".split())

        self.assertEqual(args.a, 2)
        self.assertEqual(args.b, 'four')
        self.assertEqual(args.c, 'see')

    def test_junk_config(self) -> None:
        class JunkConfigTap(Tap):
            a: int
            b: str = 'b'

        with TemporaryDirectory() as temp_dir, self.assertRaises(SystemExit):
            sys.stderr = self.dev_null
            fname = os.path.join(temp_dir, 'config.json')

            with open(fname, 'w') as f:
                f.write('is not a file that can reasonably be parsed')

            JunkConfigTap().parse_args(f'--conf {fname}'.split()).parse_args([])


if __name__ == '__main__':
    unittest.main()
