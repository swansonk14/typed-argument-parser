import unittest
from typing import Annotated
from tap import Tap, TapIgnore


class TapIgnoreTests(unittest.TestCase):
    def test_tap_ignore(self):
        class Args(Tap):
            a: int
            b: TapIgnore[int] = 2
            c: Annotated[int, "metadata"] = 3
            d: Annotated[TapIgnore[int], "metadata"] = 4
            e: TapIgnore[Annotated[int, "metadata"]] = 5

        args = Args().parse_args(["--a", "1"])

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 2)
        self.assertEqual(args.c, 3)
        self.assertEqual(args.d, 4)
        self.assertEqual(args.e, 5)

        # Check that b is not in the help message (indirectly checking it's not an argument)
        # Or check _actions

        actions = {a.dest for a in args._actions}
        self.assertIn("a", actions)
        self.assertNotIn("b", actions)
        self.assertIn("c", actions)
        self.assertNotIn("d", actions)
        self.assertNotIn("e", actions)
        self.assertNotIn("b", args.class_variables)
        self.assertNotIn("d", args.class_variables)
        self.assertNotIn("e", args.class_variables)

    def test_tap_ignore_no_default(self):
        class Args(Tap):
            a: int
            b: TapIgnore[int]

        # If b is ignored, it shouldn't be required by argparse
        # But if it has no default, accessing it might raise AttributeError if not set?
        # Tap doesn't set it if it's not in arguments.

        args = Args().parse_args(["--a", "1"])
        self.assertEqual(args.a, 1)

        # b should not be set
        with self.assertRaises(AttributeError):
            _ = args.b

    def test_tap_ignore_annotated_unwrapping(self):
        class Args(Tap):
            a: Annotated[int, "some metadata"]

        args = Args().parse_args(["--a", "1"])
        self.assertEqual(args.a, 1)

    def test_tap_ignore_subclass(self):
        class BaseArgs(Tap):
            base_keep: int
            base_ignore: TapIgnore[str] = "ignore_me"

        class SubArgs(BaseArgs):
            sub_keep: float
            sub_ignore: TapIgnore[bool] = True

        args = SubArgs().parse_args(["--base_keep", "1", "--sub_keep", "2.5"])

        self.assertEqual(args.base_keep, 1)
        self.assertEqual(args.base_ignore, "ignore_me")
        self.assertEqual(args.sub_keep, 2.5)
        self.assertEqual(args.sub_ignore, True)

        actions = {a.dest for a in args._actions}
        self.assertIn("base_keep", actions)
        self.assertNotIn("base_ignore", actions)
        self.assertIn("sub_keep", actions)
        self.assertNotIn("sub_ignore", actions)
        self.assertNotIn("b", args.class_variables)
        self.assertNotIn("d", args.class_variables)
        self.assertNotIn("e", args.class_variables)

    def test_tap_ignore_subclass_override(self):
        # Case 1: Override ignored with argument
        class Base1(Tap):
            a: TapIgnore[int] = 1

        class Sub1(Base1):
            a: int = 2

        args1 = Sub1().parse_args([])
        self.assertEqual(args1.a, 2)
        self.assertIn("a", {a.dest for a in args1._actions})

        # Case 2: Override argument with ignored
        class Base2(Tap):
            b: int = 3

        class Sub2(Base2):
            b: TapIgnore[int] = 4

        args2 = Sub2().parse_args([])
        self.assertEqual(args2.b, 4)
        self.assertNotIn("b", {a.dest for a in args2._actions})


if __name__ == "__main__":
    unittest.main()
