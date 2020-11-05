import sys
from typing import List
import unittest
from unittest import TestCase

from tap import Tap


class TestArgparseActions(TestCase):

    def test_actions_store_const(self):
        """
        Stores actions of the actions.

        Args:
            self: (todo): write your description
        """
        class StoreConstTap(Tap):

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--sum',
                                  dest='accumulate',
                                  action='store_const',
                                  const=sum,
                                  default=max)

        args = StoreConstTap().parse_args([])
        self.assertFalse(hasattr(args, 'sum'))
        self.assertEqual(args.accumulate, max)
        self.assertEqual(args.as_dict(), {'accumulate': max})

        args = StoreConstTap().parse_args(['--sum'])
        self.assertFalse(hasattr(args, 'sum'))
        self.assertEqual(args.accumulate, sum)
        self.assertEqual(args.as_dict(), {'accumulate': sum})

    def test_actions_store_true_default_true(self):
        """
        Sets up the action actions.

        Args:
            self: (todo): write your description
        """
        class StoreTrueDefaultTrueTap(Tap):
            foobar: bool = True

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--foobar', action='store_true')
        args = StoreTrueDefaultTrueTap().parse_args([])
        self.assertTrue(args.foobar)

        args = StoreTrueDefaultTrueTap().parse_args(['--foobar'])
        self.assertTrue(args.foobar)

    def test_actions_store_true_default_false(self):
        """
        Sets up the true actions.

        Args:
            self: (todo): write your description
        """
        class StoreTrueDefaultFalseTap(Tap):
            foobar: bool = False

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--foobar', action='store_true')
        args = StoreTrueDefaultFalseTap().parse_args([])
        self.assertFalse(args.foobar)

        args = StoreTrueDefaultFalseTap().parse_args(['--foobar'])
        self.assertTrue(args.foobar)

    def test_actions_store_false_default_true(self):
        """
        Sets up the action actions.

        Args:
            self: (todo): write your description
        """
        class StoreFalseDefaultTrueTap(Tap):
            foobar: bool = True

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--foobar', action='store_false')
        args = StoreFalseDefaultTrueTap().parse_args([])
        self.assertTrue(args.foobar)

        args = StoreFalseDefaultTrueTap().parse_args(['--foobar'])
        self.assertFalse(args.foobar)

    def test_actions_store_false_default_false(self):
        """
        Sets default test actions that will be set.

        Args:
            self: (todo): write your description
        """
        class StoreFalseDefaultFalseTap(Tap):
            foobar: bool = False

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--foobar', action='store_false')
        args = StoreFalseDefaultFalseTap().parse_args([])
        self.assertFalse(args.foobar)

        args = StoreFalseDefaultFalseTap().parse_args(['--foobar'])
        self.assertFalse(args.foobar)

    def test_actions_append_list(self):
        """
        Append an ordered list of the test.

        Args:
            self: (todo): write your description
        """
        class AppendListTap(Tap):
            arg: List = ['what', 'is']

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--arg', action='append')

        args = AppendListTap().parse_args([])
        self.assertEqual(args.arg, ['what', 'is'])

        args = AppendListTap().parse_args('--arg up --arg today'.split())
        self.assertEqual(args.arg, 'what is up today'.split())

    def test_actions_append_list_int(self):
        """
        Appends a list of integers.

        Args:
            self: (todo): write your description
        """
        class AppendListIntTap(Tap):
            arg: List[int] = [1, 2]

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--arg', action='append')

        args = AppendListIntTap().parse_args('--arg 3 --arg 4'.split())
        self.assertEqual(args.arg, [1, 2, 3, 4])

    def test_actions_append_untyped(self):
        """
        Append the actions to the actions.

        Args:
            self: (todo): write your description
        """
        class AppendListStrTap(Tap):
            arg = ['what', 'is']

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--arg', action='append')

        args = AppendListStrTap().parse_args([])
        self.assertEqual(args.arg, ['what', 'is'])

        args = AppendListStrTap().parse_args('--arg up --arg today'.split())
        self.assertEqual(args.arg, 'what is up today'.split())

    def test_actions_append_const(self):
        """
        Append a list of the actions.

        Args:
            self: (todo): write your description
        """
        class AppendConstTap(Tap):
            arg: List[int] = [1, 2, 3]

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--arg', action='append_const', const=7)

        args = AppendConstTap().parse_args([])
        self.assertEqual(args.arg, [1, 2, 3])

        args = AppendConstTap().parse_args('--arg --arg'.split())
        self.assertEqual(args.arg, [1, 2, 3, 7, 7])

    def test_actions_count(self):
        """
        Sets the number of actions.

        Args:
            self: (todo): write your description
        """
        class CountTap(Tap):
            arg = 7

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--arg', '-a', action='count')

        args = CountTap().parse_args([])
        self.assertEqual(args.arg, 7)

        args = CountTap().parse_args('-aaa --arg'.split())
        self.assertEqual(args.arg, 11)

    def test_actions_int_count(self):
        """
        Sets the number of actions in the test.

        Args:
            self: (todo): write your description
        """
        class CountIntTap(Tap):
            arg: int = 7

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--arg', '-a', action='count')

        args = CountIntTap().parse_args([])
        self.assertEqual(args.arg, 7)

        args = CountIntTap().parse_args('-aaa --arg'.split())
        self.assertEqual(args.arg, 11)

    def test_actions_version(self):
        """
        Configure actions actions.

        Args:
            self: (todo): write your description
        """
        class VersionTap(Tap):

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--version', action='version', version='2.0')

        # Ensure that nothing breaks without version flag
        VersionTap().parse_args([])

        # TODO: With version flag testing fails, but manual tests work
        # tried redirecting stderr using unittest.mock.patch
        # VersionTap().parse_args(['--version'])

    @unittest.skipIf(sys.version_info < (3, 8), 'action="extend" introduced in argparse in Python 3.8')
    def test_actions_extend(self):
        """
        The test actions of test actions.

        Args:
            self: (todo): write your description
        """
        class ExtendTap(Tap):
            arg = [1, 2]

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--arg', nargs="+", action='extend')

        args = ExtendTap().parse_args([])
        self.assertEqual(args.arg, [1, 2])

        args = ExtendTap().parse_args('--arg a b --arg a --arg c d'.split())
        self.assertEqual(args.arg, [1, 2] + 'a b a c d'.split())

    @unittest.skipIf(sys.version_info < (3, 8), 'action="extend" introduced in argparse in Python 3.8')
    def test_actions_extend_list(self):
        """
        Extend actions to an ordered list of actions.

        Args:
            self: (todo): write your description
        """
        class ExtendListTap(Tap):
            arg: List = ['hi']

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--arg', action='extend')

        args = ExtendListTap().parse_args('--arg yo yo --arg yoyo --arg yo yo'.split())
        self.assertEqual(args.arg, 'hi yo yo yoyo yo yo'.split())

    @unittest.skipIf(sys.version_info < (3, 8), 'action="extend" introduced in argparse in Python 3.8')
    def test_actions_extend_list_int(self):
        """
        Return a list of integers in the integers.

        Args:
            self: (todo): write your description
        """
        class ExtendListIntTap(Tap):
            arg: List[int] = [0]

            def configure(self):
                """
                Configure the argument parser.

                Args:
                    self: (todo): write your description
                """
                self.add_argument('--arg', action='extend')

        args = ExtendListIntTap().parse_args('--arg 1 2 --arg 3 --arg 4 5'.split())
        self.assertEqual(args.arg, [0, 1, 2, 3, 4, 5])


if __name__ == '__main__':
    unittest.main()
