import sys
from typing_extensions import Literal
import unittest
from unittest import TestCase

from tap import Tap


class TestSubparser(TestCase):

    def setUp(self) -> None:
        """
        Sets the terminal.

        Args:
            self: (todo): write your description
        """
        # Suppress prints from SystemExit
        class DevNull:
            def write(self, msg):
                """
                Write a message

                Args:
                    self: (todo): write your description
                    msg: (str): write your description
                """
                pass
        self.dev_null = DevNull()

    def test_subparser_documentation_example(self):
        """
        Sets the argument parser.

        Args:
            self: (todo): write your description
        """
        class SubparserA(Tap):
            bar: int  # bar help

        class SubparserB(Tap):
            baz: Literal['X', 'Y', 'Z']  # baz help

        class Args(Tap):
            foo: bool = False  # foo help

            def configure(self):
                """
                Configure the subcommand.

                Args:
                    self: (todo): write your description
                """
                self.add_subparsers(help='sub-command help')
                self.add_subparser('a', SubparserA, help='a help')
                self.add_subparser('b', SubparserB, help='b help')

        args = Args().parse_args([])
        self.assertFalse(args.foo)
        self.assertFalse(hasattr(args, 'bar'))
        self.assertFalse(hasattr(args, 'baz'))

        args = Args().parse_args(['--foo'])
        self.assertTrue(args.foo)
        self.assertFalse(hasattr(args, 'bar'))
        self.assertFalse(hasattr(args, 'baz'))

        args = Args().parse_args('a --bar 1'.split())
        self.assertFalse(args.foo)
        self.assertEqual(args.bar, 1)
        self.assertFalse(hasattr(args, 'baz'))

        args = Args().parse_args('--foo b --baz X'.split())
        self.assertTrue(args.foo)
        self.assertFalse(hasattr(args, 'bar'))
        self.assertEqual(args.baz, 'X')

        sys.stderr = self.dev_null

        with self.assertRaises(SystemExit):
            Args().parse_args('--baz X --foo b'.split())

        with self.assertRaises(SystemExit):
            Args().parse_args('b --baz X --foo'.split())

        with self.assertRaises(SystemExit):
            Args().parse_args('--foo a --bar 1 b --baz X'.split())

    def test_name_collision(self):
        """
        Configure the argument parser.

        Args:
            self: (todo): write your description
        """
        class SubparserA(Tap):
            a: int

        class Args(Tap):
            foo: bool = False

            def configure(self):
                """
                Configure the subparser.

                Args:
                    self: (todo): write your description
                """
                self.add_subparsers(help='sub-command help')
                self.add_subparser('a', SubparserA, help='a help')

        args = Args().parse_args('a --a 1'.split())
        self.assertFalse(args.foo)
        self.assertEqual(args.a, 1)

    def test_name_overriding(self):
        """
        Configure command line options.

        Args:
            self: (todo): write your description
        """
        class SubparserA(Tap):
            foo: int

        class Args(Tap):
            foo: bool = False

            def configure(self):
                """
                Configure the subparser.

                Args:
                    self: (todo): write your description
                """
                self.add_subparsers(help='sub-command help')
                self.add_subparser('a', SubparserA)

        args = Args().parse_args(['--foo'])
        self.assertTrue(args.foo)

        args = Args().parse_args('a --foo 2'.split())
        self.assertEqual(args.foo, 2)

        args = Args().parse_args('--foo a --foo 2'.split())
        self.assertEqual(args.foo, 2)

    def test_add_subparser_twice(self):
        """
        Configure subparser parser.

        Args:
            self: (todo): write your description
        """
        class SubparserA(Tap):
            bar: int

        class SubparserB(Tap):
            baz: int

        class Args(Tap):
            foo: bool = False

            def configure(self):
                """
                Configure the subparser.

                Args:
                    self: (todo): write your description
                """
                self.add_subparser('a', SubparserB)
                self.add_subparser('a', SubparserA)

        args = Args().parse_args('a --bar 2'.split())
        self.assertFalse(args.foo)
        self.assertEqual(args.bar, 2)
        self.assertFalse(hasattr(args, 'baz'))

        sys.stderr = self.dev_null
        with self.assertRaises(SystemExit):
            Args().parse_args('a --baz 2'.split())

    def test_add_subparsers_twice(self):
        """
        Sets up the subparser.

        Args:
            self: (todo): write your description
        """
        class SubparserA(Tap):
            a: int

        class Args(Tap):
            foo: bool = False

            def configure(self):
                """
                Configure the subparser.

                Args:
                    self: (todo): write your description
                """
                self.add_subparser('a', SubparserA)
                self.add_subparsers(help='sub-command1 help')
                self.add_subparsers(help='sub-command2 help')

        sys.stderr = self.dev_null
        with self.assertRaises(SystemExit):
            Args().parse_args([])

    def test_add_subparsers_with_add_argument(self):
        """
        Add the argument parser.

        Args:
            self: (todo): write your description
        """
        class SubparserA(Tap):
            for_sure: bool = False

        class Args(Tap):
            foo: bool = False
            bar: int = 1

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--bar', '-ib')
                self.add_subparser('is_terrible', SubparserA)
                self.add_argument('--foo', '-m')

        args = Args().parse_args('-ib 0 -m is_terrible --for_sure'.split())
        self.assertTrue(args.foo)
        self.assertEqual(args.bar, 0)
        self.assertTrue(args.for_sure)

    def test_add_subsubparsers(self):
        """
        Configure subcommands.

        Args:
            self: (todo): write your description
        """

        class SubSubparserB(Tap):
            baz: bool = False

        class SubparserA(Tap):
            biz: bool = False

            def configure(self):
                """
                Configure the sub - command.

                Args:
                    self: (todo): write your description
                """
                self.add_subparser('b', SubSubparserB)

        class SubparserB(Tap):
            blaz: bool = False

        class Args(Tap):
            foo: bool = False

            def configure(self):
                """
                Configure the subparser.

                Args:
                    self: (todo): write your description
                """
                self.add_subparser('a', SubparserA)
                self.add_subparser('b', SubparserB)

        args = Args().parse_args('b --blaz'.split())
        self.assertFalse(args.foo)
        self.assertFalse(hasattr(args, 'baz'))
        self.assertFalse(hasattr(args, 'biz'))
        self.assertTrue(args.blaz)

        args = Args().parse_args('a --biz'.split())
        self.assertFalse(args.foo)
        self.assertTrue(args.biz)
        self.assertFalse(hasattr(args, 'baz'))
        self.assertFalse(hasattr(args, 'blaz'))

        args = Args().parse_args('a --biz b --baz'.split())
        self.assertFalse(args.foo)
        self.assertTrue(args.biz)
        self.assertFalse(hasattr(args, 'blaz'))
        self.assertTrue(args.baz)

        with self.assertRaises(SystemExit):
            Args().parse_args('b a'.split())


if __name__ == '__main__':
    unittest.main()
