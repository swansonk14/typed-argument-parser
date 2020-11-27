import sys
from tempfile import NamedTemporaryFile
import unittest
from unittest import TestCase

from tap import Tap


class LoadConfigFilesTests(TestCase):

    def setUp(self) -> None:
        class DevNull:
            def write(self, msg):
                pass
        self.dev_null = DevNull()

    def test_file_does_not_exist(self) -> None:
        class EmptyTap(Tap):
            pass

        with self.assertRaises(FileNotFoundError):
            EmptyTap(config_files=['nope']).parse_args([])

    def test_single_config(self) -> None:
        class SimpleTap(Tap):
            a: int
            b: str = 'b'

        with NamedTemporaryFile() as f:
            f.write(b'--a 1')
            f.flush()
            args = SimpleTap(config_files=[f.name]).parse_args([])

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 'b')

    def test_single_config_overwriting(self) -> None:
        class SimpleOverwritingTap(Tap):
            a: int
            b: str = 'b'

        with NamedTemporaryFile() as f:
            f.write(b'--a 1 --b two')
            f.flush()
            args = SimpleOverwritingTap(config_files=[f.name]).parse_args('--a 2'.split())

        self.assertEqual(args.a, 2)
        self.assertEqual(args.b, 'two')

    def test_single_config_known_only(self) -> None:
        class KnownOnlyTap(Tap):
            a: int
            b: str = 'b'

        with NamedTemporaryFile() as f:
            f.write(b'--a 1 --c seeNothing')
            f.flush()
            args = KnownOnlyTap(config_files=[f.name]).parse_args([], known_only=True)

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 'b')
        self.assertEqual(args.extra_args, ['--c', 'seeNothing'])

    def test_single_config_required_still_required(self) -> None:
        class KnownOnlyTap(Tap):
            a: int
            b: str = 'b'

        with NamedTemporaryFile() as f, self.assertRaises(SystemExit):
            sys.stderr = self.dev_null
            f.write(b'--b fore')
            f.flush()
            KnownOnlyTap(config_files=[f.name]).parse_args([])

    def test_multiple_configs(self) -> None:
        class MultipleTap(Tap):
            a: int
            b: str = 'b'

        with NamedTemporaryFile() as f1, NamedTemporaryFile() as f2:
            f1.write(b'--b two')
            f1.flush()
            f2.write(b'--a 1')
            f2.flush()
            args = MultipleTap(config_files=[f1.name, f2.name]).parse_args([])

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 'two')

    def test_multiple_configs_overwriting(self) -> None:
        class MultipleOverwritingTap(Tap):
            a: int
            b: str = 'b'
            c: str = 'c'

        with NamedTemporaryFile() as f1, NamedTemporaryFile() as f2:
            f1.write(b'--a 1 --b two')
            f1.flush()
            f2.write(b'--a 2 --c see')
            f2.flush()
            args = MultipleOverwritingTap(config_files=[f1.name, f2.name]).parse_args('--b four'.split())

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 'four')
        self.assertEqual(args.c, 'see')

    def test_junk_config(self) -> None:
        class JunkConfigTap(Tap):
            a: int
            b: str = 'b'

        with NamedTemporaryFile() as f1, self.assertRaises(SystemExit):
            sys.stderr = self.dev_null
            f1.write(b'is not a file that can reasonably be parsed')
            f1.flush()
            JunkConfigTap(config_files=[f1.name]).parse_args()


if __name__ == '__main__':
    unittest.main()
