import sys
from typing import Any, Optional, Tuple
import unittest
from unittest import TestCase

from tap import tapify


class Person:
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return f'Person({self.name})'


class Problems:
    def __init__(self, problem_1: str, problem_2):
        self.problem_1 = problem_1
        self.problem_2 = problem_2

    def __str__(self) -> str:
        return f'Problems({self.problem_1}, {self.problem_2})'


class TapifyTests(TestCase):
    def setUp(self) -> None:
        # Suppress prints from SystemExit
        class DevNull:
            def write(self, msg):
                pass
        self.dev_null = DevNull()

    def test_tapify_empty(self):
        def pie() -> float:
            return 3.14

        self.assertEqual(tapify(pie, args=[]), 3.14)

    def test_tapify_simple_types(self):
        def concat(a: int, simple: str, test: float, of: float, types: bool) -> str:
            return f'{a} {simple} {test} {of} {types}'

        output = tapify(concat, args=[
            '--a', '1',
            '--simple', 'simple',
            '--test', '3.14',
            '--of', '2.718',
            '--types'
        ])

        self.assertEqual(output, '1 simple 3.14 2.718 True')

    def test_tapify_simple_types_defaults(self):
        def concat(a: int, simple: str, test: float, of: float = -.3, types: bool = False, wow: str = 'abc') -> str:
            return f'{a} {simple} {test} {of} {types} {wow}'

        output = tapify(concat, args=[
            '--a', '1',
            '--simple', 'simple',
            '--test', '3.14',
            '--types',
            '--wow', 'wee'
        ])

        self.assertEqual(output, '1 simple 3.14 -0.3 True wee')

    def test_tapify_complex_types(self):
        def concat(complexity: list[str], requires: tuple[int, int], intelligence: Person) -> str:
            return f'{" ".join(complexity)} {requires[0]} {requires[1]} {intelligence}'

        output = tapify(concat, args=[
            '--complexity', 'complex', 'things', 'require',
            '--requires', '1', '0',
            '--intelligence', 'jesse',
        ])

        self.assertEqual(output, 'complex things require 1 0 Person(jesse)')

    def test_tapify_complex_types_defaults(self):
        def concat(complexity: list[str],
                   requires: Tuple[int, int] = (2, 5),
                   intelligence: Person = Person('kyle'),
                   maybe: Optional[str] = None,
                   possibly: Optional[str] = None) -> str:
            return f'{" ".join(complexity)} {requires[0]} {requires[1]} {intelligence} {maybe} {possibly}'

        output = tapify(concat, args=[
            '--complexity', 'complex', 'things', 'require',
            '--requires', '-3', '12',
            '--possibly', 'huh?'
        ])

        self.assertEqual(output, 'complex things require -3 12 Person(kyle) None huh?')

    def test_tapify_too_few_args(self):
        def concat(so: int, many: float, args: str) -> str:
            return f'{so} {many} {args}'

        with self.assertRaises(SystemExit):
            sys.stderr = self.dev_null

            tapify(concat, args=[
                '--so', '23',
                '--many', '9.3'
            ])

    def test_tapify_too_many_args(self):
        def concat(so: int, few: float) -> str:
            return f'{so} {few}'

        with self.assertRaises(SystemExit):
            sys.stderr = self.dev_null

            tapify(concat, args=[
                '--so', '23',
                '--few', '9.3',
                '--args', 'wow'
            ])

    def test_tapify_too_many_args_known_only(self):
        def concat(so: int, few: float) -> str:
            return f'{so} {few}'

        output = tapify(concat, args=[
            '--so', '23',
            '--few', '9.3',
            '--args', 'wow'
        ], known_only=True)

        self.assertEqual(output, '23 9.3')

    def test_tapify_kwargs(self):
        def concat(i: int, like: float, k: int, w: str = 'w', args: str = 'argy', always: bool = False) -> str:
            return f'{i} {like} {k} {w} {args} {always}'

        output = tapify(concat, args=[
            '--i', '23',
            '--args', 'wow',
            '--mis', 'direction',
            '--like', '3.03',
        ], known_only=True, w='hello', k=5, like=3.4, extra='arg')

        self.assertEqual(output, '23 3.03 5 hello wow False')

    def test_tapify_kwargs_extra(self):
        def concat(i: int, like: float, k: int, w: str = 'w', args: str = 'argy', always: bool = False) -> str:
            return f'{i} {like} {k} {w} {args} {always}'

        with self.assertRaises(ValueError):
            sys.stderr = self.dev_null

            tapify(concat, args=[
                '--i', '23',
                '--args', 'wow',
                '--like', '3.03',
            ], w='hello', k=5, like=3.4, mis='direction')

    def test_tapify_unsupported_type(self):
        def concat(problems: Problems) -> str:
            return f'{problems}'

        output = tapify(concat, args=[], problems=Problems('oh', 'no!'))

        self.assertEqual(output, 'Problems(oh, no!)')

        with self.assertRaises(SystemExit):
            sys.stderr = self.dev_null

            tapify(concat, args=['--problems', '1', '2'])

    def test_tapify_untyped(self):
        def concat(untyped_1, typed_1: int,
                   untyped_2=5, typed_2: str = 'now',
                   untyped_3='hi', typed_3: bool = False) -> str:
            return f'{untyped_1} {typed_1} {untyped_2} {typed_2} {untyped_3} {typed_3}'

        output = tapify(concat, args=[
            '--untyped_1', 'why not type?',
            '--typed_1', '1',
            '--typed_2', 'typing is great!',
            '--untyped_3', 'bye'
        ])

        self.assertEqual(output, 'why not type? 1 5 typing is great! bye False')

# Supported argument types
# Unsupported types
# Too many arguments
# Not enough arguments
# Some from command line and some from code providing it to the function
# All arguments from code providing it to the function (just enough, too many, too few)
# With and without defaults
# Untyped

# Help string


if __name__ == '__main__':
    unittest.main()
