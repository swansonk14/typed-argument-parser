import contextlib
from dataclasses import dataclass
import io
import sys
from typing import Dict, List, Optional, Tuple, Any
import unittest
from unittest import TestCase

from tap import tapify


# Suppress prints from SystemExit
class DevNull:
    def write(self, msg):
        pass


sys.stderr = DevNull()


class Person:
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return f"Person({self.name})"


class Problems:
    def __init__(self, problem_1: str, problem_2):
        self.problem_1 = problem_1
        self.problem_2 = problem_2

    def __str__(self) -> str:
        return f"Problems({self.problem_1}, {self.problem_2})"


class TapifyTests(TestCase):
    def test_tapify_empty(self):
        def pie() -> float:
            return 3.14

        class Pie:
            def __eq__(self, other: float) -> bool:
                return other == pie()

        @dataclass
        class PieDataclass:
            def __eq__(self, other: float) -> bool:
                return other == pie()

        for class_or_function in [pie, Pie, PieDataclass]:
            self.assertEqual(tapify(class_or_function, command_line_args=[]), 3.14)

    def test_tapify_simple_types(self):
        def concat(a: int, simple: str, test: float, of: float, types: bool) -> str:
            return f"{a} {simple} {test} {of} {types}"

        class Concat:
            def __init__(self, a: int, simple: str, test: float, of: float, types: bool):
                self.kwargs = {"a": a, "simple": simple, "test": test, "of": of, "types": types}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            a: int
            simple: str
            test: float
            of: float
            types: bool

            def __eq__(self, other: str) -> bool:
                return other == concat(self.a, self.simple, self.test, self.of, self.types)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output = tapify(
                class_or_function,
                command_line_args=["--a", "1", "--simple", "simple", "--test", "3.14", "--of", "2.718", "--types"],
            )

            self.assertEqual(output, "1 simple 3.14 2.718 True")

    def test_tapify_simple_types_defaults(self):
        def concat(a: int, simple: str, test: float, of: float = -0.3, types: bool = False, wow: str = "abc") -> str:
            return f"{a} {simple} {test} {of} {types} {wow}"

        class Concat:
            def __init__(
                self, a: int, simple: str, test: float, of: float = -0.3, types: bool = False, wow: str = "abc"
            ):
                self.kwargs = {"a": a, "simple": simple, "test": test, "of": of, "types": types, "wow": wow}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            a: int
            simple: str
            test: float
            of: float = -0.3
            types: bool = False
            wow: str = "abc"

            def __eq__(self, other: str) -> bool:
                return other == concat(self.a, self.simple, self.test, self.of, self.types, self.wow)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output = tapify(
                class_or_function,
                command_line_args=["--a", "1", "--simple", "simple", "--test", "3.14", "--types", "--wow", "wee"],
            )

            self.assertEqual(output, "1 simple 3.14 -0.3 True wee")

    def test_tapify_complex_types(self):
        def concat(complexity: List[str], requires: Tuple[int, int], intelligence: Person) -> str:
            return f'{" ".join(complexity)} {requires[0]} {requires[1]} {intelligence}'

        class Concat:
            def __init__(self, complexity: List[str], requires: Tuple[int, int], intelligence: Person):
                self.kwargs = {"complexity": complexity, "requires": requires, "intelligence": intelligence}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            complexity: List[str]
            requires: Tuple[int, int]
            intelligence: Person

            def __eq__(self, other: str) -> bool:
                return other == concat(self.complexity, self.requires, self.intelligence)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output = tapify(
                class_or_function,
                command_line_args=[
                    "--complexity",
                    "complex",
                    "things",
                    "require",
                    "--requires",
                    "1",
                    "0",
                    "--intelligence",
                    "jesse",
                ],
            )

            self.assertEqual(output, "complex things require 1 0 Person(jesse)")

    @unittest.skipIf(
        sys.version_info < (3, 9), "Parameterized standard collections (e.g., list[int]) introduced in Python 3.9"
    )
    def test_tapify_complex_types_parameterized_standard(self):
        def concat(complexity: list[int], requires: tuple[int, int], intelligence: Person) -> str:
            return f'{" ".join(map(str, complexity))} {requires[0]} {requires[1]} {intelligence}'

        class Concat:
            def __init__(self, complexity: list[int], requires: tuple[int, int], intelligence: Person):
                self.kwargs = {"complexity": complexity, "requires": requires, "intelligence": intelligence}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            complexity: list[int]
            requires: tuple[int, int]
            intelligence: Person

            def __eq__(self, other: str) -> bool:
                return other == concat(self.complexity, self.requires, self.intelligence)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output = tapify(
                class_or_function,
                command_line_args=["--complexity", "1", "2", "3", "--requires", "1", "0", "--intelligence", "jesse",],
            )

            self.assertEqual(output, "1 2 3 1 0 Person(jesse)")

    def test_tapify_complex_types_defaults(self):
        def concat(
            complexity: List[str],
            requires: Tuple[int, int] = (2, 5),
            intelligence: Person = Person("kyle"),
            maybe: Optional[str] = None,
            possibly: Optional[str] = None,
        ) -> str:
            return f'{" ".join(complexity)} {requires[0]} {requires[1]} {intelligence} {maybe} {possibly}'

        class Concat:
            def __init__(
                self,
                complexity: List[str],
                requires: Tuple[int, int] = (2, 5),
                intelligence: Person = Person("kyle"),
                maybe: Optional[str] = None,
                possibly: Optional[str] = None,
            ):
                self.kwargs = {
                    "complexity": complexity,
                    "requires": requires,
                    "intelligence": intelligence,
                    "maybe": maybe,
                    "possibly": possibly,
                }

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            complexity: List[str]
            requires: Tuple[int, int] = (2, 5)
            intelligence: Person = Person("kyle")
            maybe: Optional[str] = None
            possibly: Optional[str] = None

            def __eq__(self, other: str) -> bool:
                return other == concat(self.complexity, self.requires, self.intelligence, self.maybe, self.possibly)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output = tapify(
                class_or_function,
                command_line_args=[
                    "--complexity",
                    "complex",
                    "things",
                    "require",
                    "--requires",
                    "-3",
                    "12",
                    "--possibly",
                    "huh?",
                ],
            )

            self.assertEqual(output, "complex things require -3 12 Person(kyle) None huh?")

    def test_tapify_too_few_args(self):
        def concat(so: int, many: float, args: str) -> str:
            return f"{so} {many} {args}"

        class Concat:
            def __init__(self, so: int, many: float, args: str):
                self.kwargs = {"so": so, "many": many, "args": args}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            so: int
            many: float
            args: str

            def __eq__(self, other: str) -> bool:
                return other == concat(self.so, self.many, self.args)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            with self.assertRaises(SystemExit):
                tapify(class_or_function, command_line_args=["--so", "23", "--many", "9.3"])

    def test_tapify_too_many_args(self):
        def concat(so: int, few: float) -> str:
            return f"{so} {few}"

        class Concat:
            def __init__(self, so: int, few: float):
                self.kwargs = {"so": so, "few": few}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            so: int
            few: float

            def __eq__(self, other: str) -> bool:
                return other == concat(self.so, self.few)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            with self.assertRaises(SystemExit):
                tapify(class_or_function, command_line_args=["--so", "23", "--few", "9.3", "--args", "wow"])

    def test_tapify_too_many_args_known_only(self):
        def concat(so: int, few: float) -> str:
            return f"{so} {few}"

        class Concat:
            def __init__(self, so: int, few: float):
                self.kwargs = {"so": so, "few": few}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            so: int
            few: float

            def __eq__(self, other: str) -> bool:
                return other == concat(self.so, self.few)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output = tapify(
                class_or_function, command_line_args=["--so", "23", "--few", "9.3", "--args", "wow"], known_only=True
            )

            self.assertEqual(output, "23 9.3")

    def test_tapify_kwargs(self):
        def concat(i: int, like: float, k: int, w: str = "w", args: str = "argy", always: bool = False) -> str:
            return f"{i} {like} {k} {w} {args} {always}"

        class Concat:
            def __init__(self, i: int, like: float, k: int, w: str = "w", args: str = "argy", always: bool = False):
                self.kwargs = {"i": i, "like": like, "k": k, "w": w, "args": args, "always": always}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            i: int
            like: float
            k: int
            w: str = "w"
            args: str = "argy"
            always: bool = False

            def __eq__(self, other: str) -> bool:
                return other == concat(self.i, self.like, self.k, self.w, self.args, self.always)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output = tapify(
                class_or_function,
                command_line_args=["--i", "23", "--args", "wow", "--like", "3.03",],
                known_only=True,
                w="hello",
                k=5,
                like=3.4,
                extra="arg",
            )

            self.assertEqual(output, "23 3.03 5 hello wow False")

    def test_tapify_kwargs_extra(self):
        def concat(i: int, like: float, k: int, w: str = "w", args: str = "argy", always: bool = False) -> str:
            return f"{i} {like} {k} {w} {args} {always}"

        class Concat:
            def __init__(self, i: int, like: float, k: int, w: str = "w", args: str = "argy", always: bool = False):
                self.kwargs = {"i": i, "like": like, "k": k, "w": w, "args": args, "always": always}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            i: int
            like: float
            k: int
            w: str = "w"
            args: str = "argy"
            always: bool = False

            def __eq__(self, other: str) -> bool:
                return other == concat(self.i, self.like, self.k, self.w, self.args, self.always)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            with self.assertRaises(ValueError):
                tapify(
                    class_or_function,
                    command_line_args=["--i", "23", "--args", "wow", "--like", "3.03",],
                    w="hello",
                    k=5,
                    like=3.4,
                    mis="direction",
                )

    def test_tapify_unsupported_type(self):
        def concat(problems: Problems) -> str:
            return f"{problems}"

        class Concat:
            def __init__(self, problems: Problems):
                self.problems = problems

            def __eq__(self, other: str) -> bool:
                return other == concat(self.problems)

        @dataclass
        class ConcatDataclass:
            problems: Problems

            def __eq__(self, other: str) -> bool:
                return other == concat(self.problems)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output = tapify(class_or_function, command_line_args=[], problems=Problems("oh", "no!"))

            self.assertEqual(output, "Problems(oh, no!)")

            with self.assertRaises(SystemExit):
                tapify(class_or_function, command_line_args=["--problems", "1", "2"])

    def test_tapify_untyped(self):
        def concat(
            untyped_1, typed_1: int, untyped_2=5, typed_2: str = "now", untyped_3="hi", typed_3: bool = False
        ) -> str:
            return f"{untyped_1} {typed_1} {untyped_2} {typed_2} {untyped_3} {typed_3}"

        class Concat:
            def __init__(
                self, untyped_1, typed_1: int, untyped_2=5, typed_2: str = "now", untyped_3="hi", typed_3: bool = False
            ):
                self.kwargs = {
                    "untyped_1": untyped_1,
                    "typed_1": typed_1,
                    "untyped_2": untyped_2,
                    "typed_2": typed_2,
                    "untyped_3": untyped_3,
                    "typed_3": typed_3,
                }

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            untyped_1: Any
            typed_1: int
            untyped_2: Any = 5
            typed_2: str = "now"
            untyped_3: Any = "hi"
            typed_3: bool = False

            def __eq__(self, other: str) -> bool:
                return other == concat(
                    self.untyped_1, self.typed_1, self.untyped_2, self.typed_2, self.untyped_3, self.typed_3
                )

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output = tapify(
                class_or_function,
                command_line_args=[
                    "--untyped_1",
                    "why not type?",
                    "--typed_1",
                    "1",
                    "--typed_2",
                    "typing is great!",
                    "--untyped_3",
                    "bye",
                ],
            )

            self.assertEqual(output, "why not type? 1 5 typing is great! bye False")

    def test_double_tapify(self):
        def concat(a: int, b: int, c: int) -> str:
            """Concatenate three numbers."""
            return f"{a} {b} {c}"

        class Concat:
            """Concatenate three numbers."""

            def __init__(self, a: int, b: int, c: int):
                """Concatenate three numbers."""
                self.kwargs = {"a": a, "b": b, "c": c}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            """Concatenate three numbers."""

            a: int
            b: int
            c: int

            def __eq__(self, other: str) -> bool:
                return other == concat(self.a, self.b, self.c)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            output_1 = tapify(class_or_function, command_line_args=["--a", "1", "--b", "2", "--c", "3"])
            output_2 = tapify(class_or_function, command_line_args=["--a", "4", "--b", "5", "--c", "6"])

            self.assertEqual(output_1, "1 2 3")
            self.assertEqual(output_2, "4 5 6")

    def test_tapify_args_kwargs(self):
        def concat(a: int, *args, b: int, **kwargs) -> str:
            return f"{a} {args} {b} {kwargs}"

        class Concat:
            def __init__(self, a: int, *args, b: int, **kwargs):
                self.a = a
                self.args = args
                self.b = b
                self.kwargs = kwargs

            def __eq__(self, other: str) -> bool:
                return other == concat(a=self.a, *self.args, b=self.b, **self.kwargs)

        for class_or_function in [concat, Concat]:
            with self.assertRaises(SystemExit):
                tapify(class_or_function, command_line_args=["--a", "1", "--b", "2"])

    def test_tapify_help(self):
        def concat(a: int, b: int, c: int) -> str:
            """Concatenate three numbers.

            :param a: The first number.
            :param b: The second number.
            :param c: The third number.
            """
            return f"{a} {b} {c}"

        class Concat:
            def __init__(self, a: int, b: int, c: int):
                """Concatenate three numbers.

                :param a: The first number.
                :param b: The second number.
                :param c: The third number.
                """
                self.kwargs = {"a": a, "b": b, "c": c}

            def __eq__(self, other: str) -> bool:
                return other == concat(**self.kwargs)

        @dataclass
        class ConcatDataclass:
            """Concatenate three numbers.

            :param a: The first number.
            :param b: The second number.
            :param c: The third number.
            """

            a: int
            b: int
            c: int

            def __eq__(self, other: str) -> bool:
                return other == concat(self.a, self.b, self.c)

        for class_or_function in [concat, Concat, ConcatDataclass]:
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                with self.assertRaises(SystemExit):
                    tapify(class_or_function, command_line_args=["-h"])

            self.assertIn("Concatenate three numbers.", f.getvalue())
            self.assertIn("--a A       (int, required) The first number.", f.getvalue())
            self.assertIn("--b B       (int, required) The second number.", f.getvalue())
            self.assertIn("--c C       (int, required) The third number.", f.getvalue())


class TestTapifyKwargs(unittest.TestCase):
    def setUp(self) -> None:
        def concat(a: int, b: int = 2, **kwargs) -> str:
            """Concatenate three numbers.

            :param a: The first number.
            :param b: The second number.
            """
            return f'{a}_{b}_{"-".join(f"{k}={v}" for k, v in kwargs.items())}'

        self.concat_function = concat

        class Concat:
            def __init__(self, a: int, b: int = 2, **kwargs: Dict[str, str]):
                """Concatenate three numbers.

                :param a: The first number.
                :param b: The second number.
                """
                self.a = a
                self.b = b
                self.kwargs = kwargs

            def __eq__(self, other: str) -> bool:
                return other == concat(self.a, self.b, **self.kwargs)

        self.concat_class = Concat

    def test_tapify_empty_kwargs(self) -> None:
        for class_or_function in [self.concat_function, self.concat_class]:
            output = tapify(class_or_function, command_line_args=["--a", "1"])

            self.assertEqual(output, "1_2_")

    def test_tapify_has_kwargs(self) -> None:
        for class_or_function in [self.concat_function, self.concat_class]:
            output = tapify(class_or_function, command_line_args=["--a", "1", "--c", "3", "--d", "4"])

            self.assertEqual(output, "1_2_c=3-d=4")

    def test_tapify_has_kwargs_replace_default(self) -> None:
        for class_or_function in [self.concat_function, self.concat_class]:
            output = tapify(class_or_function, command_line_args=["--a", "1", "--c", "3", "--b", "5", "--d", "4"])

            self.assertEqual(output, "1_5_c=3-d=4")


if __name__ == "__main__":
    unittest.main()
