import sys
import unittest
from typing import Annotated
from tap import Tap, TapIgnore, tapify


# Suppress prints from SystemExit
class DevNull:
    def write(self, msg):
        pass


sys.stderr = DevNull()


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

        args.b = 99
        self.assertEqual(args.b, 99)

        with self.assertRaises(SystemExit):
            Args().parse_args(["--a", "1", "--b", "99"])

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

    def test_tap_ignore_all_arguments(self):
        """All arguments are in TapIgnore, so no CLI arguments exist."""
        class Args(Tap):
            a: TapIgnore[int] = 1
            b: TapIgnore[str] = "ignored"
            c: TapIgnore[float] = 2.5

        # Should parse with no arguments since all are ignored
        args = Args().parse_args([])

        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, "ignored")
        self.assertEqual(args.c, 2.5)

        # Only "help" should be in actions, not our fields
        actions = {a.dest for a in args._actions}
        self.assertNotIn("a", actions)
        self.assertNotIn("b", actions)
        self.assertNotIn("c", actions)
        self.assertNotIn("a", args.class_variables)
        self.assertNotIn("b", args.class_variables)
        self.assertNotIn("c", args.class_variables)

    def test_tap_ignore_generic_types(self):
        """TapIgnore wraps generic/boxed types like list[int], dict[str, int]."""
        class Args(Tap):
            a: int
            b: TapIgnore[list[int]] = [1, 2, 3]
            c: TapIgnore[dict[str, int]] = {"x": 10}
            d: TapIgnore[set[str]] = {"foo", "bar"}
            e: TapIgnore[tuple[int, str]] = (42, "hello")

        args = Args().parse_args(["--a", "5"])

        self.assertEqual(args.a, 5)
        self.assertEqual(args.b, [1, 2, 3])
        self.assertEqual(args.c, {"x": 10})
        self.assertEqual(args.d, {"foo", "bar"})
        self.assertEqual(args.e, (42, "hello"))

        actions = {a.dest for a in args._actions}
        self.assertIn("a", actions)
        self.assertNotIn("b", actions)
        self.assertNotIn("c", actions)
        self.assertNotIn("d", actions)
        self.assertNotIn("e", actions)
        self.assertNotIn("b", args.class_variables)
        self.assertNotIn("c", args.class_variables)
        self.assertNotIn("d", args.class_variables)
        self.assertNotIn("e", args.class_variables)

    def test_tap_ignore_as_dict(self):
        """Test that as_dict includes TapIgnore fields with their default values."""
        class Args(Tap):
            a: int
            b: TapIgnore[int] = 2
            c: Annotated[int, "metadata"] = 3
            d: Annotated[TapIgnore[int], "metadata"] = 4

        args = Args().parse_args(["--a", "1", "--c", "5"])
        args_dict = args.as_dict()

        # Regular args should be in as_dict
        self.assertIn("a", args_dict)
        self.assertEqual(args_dict["a"], 1)
        self.assertIn("c", args_dict)
        self.assertEqual(args_dict["c"], 5)

        # TapIgnore fields should also be in as_dict with their default values
        self.assertIn("b", args_dict)
        self.assertEqual(args_dict["b"], 2)
        self.assertIn("d", args_dict)
        self.assertEqual(args_dict["d"], 4)

    def test_tap_ignore_as_dict_then_from_dict(self):
        """Test round-trip: parse_args -> as_dict -> from_dict on a new instance."""
        class Args(Tap):
            a: int
            b: TapIgnore[int] = 2
            c: Annotated[int, "metadata"] = 3
            d: Annotated[TapIgnore[int], "metadata"] = 4

        # Parse initial args
        args1 = Args().parse_args(["--a", "1", "--c", "5"])

        # Get dict representation
        args_dict = args1.as_dict()

        # Create new instance and load from dict
        args2 = Args().from_dict(args_dict)

        # Check that all values match
        self.assertEqual(args2.a, 1)
        self.assertEqual(args2.b, 2)
        self.assertEqual(args2.c, 5)
        self.assertEqual(args2.d, 4)

        # Verify both instances have the same as_dict output
        self.assertEqual(args1.as_dict(), args2.as_dict())

    def test_tap_ignore_configure_raises_error_for_ignored_argument(self):
        """Test that configure() raises an error when trying to add a TapIgnore argument.

        If you explicitly call add_argument in configure() for a TapIgnore field,
        a ValueError is raised to alert the user of the conflicting configuration.
        """
        class Args(Tap):
            a: int
            b: TapIgnore[int] = 2  # Marked as ignored

            def configure(self):
                # Try to explicitly add the ignored argument - this should raise
                self.add_argument("--b", type=int, default=2)

        with self.assertRaises(ValueError) as context:
            Args()

        self.assertIn("b", str(context.exception))
        self.assertIn("TapIgnore", str(context.exception))

    def test_tap_ignore_configure_with_tap_ignore_type(self):
        """Test that configure() raises an error when using TapIgnore as the type argument.

        If a field is declared as a regular int, but someone tries to use TapIgnore[int]
        as the type in add_argument, a ValueError should be raised.
        """
        class Args(Tap):
            a: int
            b: int = 2  # Regular int, NOT ignored

            def configure(self):
                # Try to use TapIgnore as the type - this should raise
                self.add_argument("--b", type=TapIgnore[int], default=3)

        args = Args()
        args.parse_args(["--a", "1", "--b", "2"])
        self.assertEqual(args.a, 1)
        self.assertEqual(args.b, 2)

        args = Args().parse_args(["--a", "1"])
        self.assertEqual(args.b, 3)



    def test_tapify_function_with_tap_ignore(self):
        """Test that tapify handles TapIgnore annotations on function arguments."""

        def my_func(a: int, b: TapIgnore[int] = 2, c: str = "hello") -> str:
            return f"{a} {b} {c}"

        # b is ignored, so it shouldn't be parsed from CLI - should use default
        output = tapify(my_func, command_line_args=["--a", "1", "--c", "world"])
        self.assertEqual(output, "1 2 world")

        # Passing --b should fail because it's not a recognized argument
        with self.assertRaises(SystemExit):
            tapify(my_func, command_line_args=["--a", "1", "--b", "99", "--c", "world"])


    def test_tapify_function_with_tap_ignore_known_only(self):
        """Test tapify with TapIgnore and known_only=True."""

        def my_func(a: int, b: TapIgnore[int] = 2, c: str = "hello") -> str:
            return f"{a} {b} {c}"

        # With known_only=True, --b should be ignored (not cause an error)
        output = tapify(
            my_func,
            command_line_args=["--a", "1", "--b", "99", "--c", "world"],
            known_only=True
        )
        # b should still be 2 (the default), not 99
        self.assertEqual(output, "1 2 world")

    def test_tapify_class_with_tap_ignore(self):
        """Test that tapify handles TapIgnore annotations on class __init__ arguments."""

        class MyClass:
            def __init__(self, a: int, b: TapIgnore[int] = 2, c: str = "hello"):
                self.result = f"{a} {b} {c}"

        # Passing --b should fail because it's not a recognized argument
        with self.assertRaises(SystemExit):
            tapify(MyClass, command_line_args=["--a", "1", "--b", "99", "--c", "world"])

if __name__ == "__main__":
    unittest.main()
