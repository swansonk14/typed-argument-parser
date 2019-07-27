from typing import List
import unittest
from unittest import TestCase

from tap import Tap


class NotEnoughDocumentationTests(TestCase):

    def setUp(self):

        class NotEnoughDocumentation(Tap):
            """This is a simple argument parser.

            Arguments:
            :arg1: First argument.
            """
            arg1: str = 'hi'
            arg2: str = 'there'

        self.args = NotEnoughDocumentation().parse_args()

    def test_assignments_as_dict(self):
        self.assertEqual(self.args.as_dict(), {'arg1': 'hi',
                                               'arg2': 'there'})

    def test_docstring_parsing(self):
        self.assertEqual(self.args.description, 'This is a simple argument parser.')

        variable_descriptions = {k: v.strip() if v else v for k, v in self.args.variable_description.items()}
        self.assertEqual(variable_descriptions, {
            'arg1': 'First argument.',
            'arg2': ''})


class BadDocumentationTests(TestCase):

    def test_ignore_listing_too_many_arguments(self):

        class TooMuchDocumentation(Tap):
            """This is a simple argument parser.

            Arguments:
            :arg1: First arg.
            :arg2: Second arg.
            :arg3: Third arg.
            """
            arg1: str = "hi"
            arg2: str = "there"

        args = TooMuchDocumentation().parse_args()

        # The third argument in the documentation is ignored
        # so there should be two arguments plus the help
        self.assertEqual(len(args._actions), 3)

    def test_ignore_incorrect_arguments(self):

        class MispelledDocumentation(Tap):
            """This is a simple argument parser.

            Arguments:
            :blarg: First arg.
            """
            arg: str = "hi"

        args = MispelledDocumentation().parse_args()
        self.assertEqual(args.variable_description["arg"], '')
        self.assertRaises(TypeError, args.variable_description["blarg"])


class Person:
    def __init__(self, name: str):
        self.name = name


class IntegrationDefaultTap(Tap):
    """Documentation is boring"""
    arg_untyped = 42
    # arg_str_required: str
    arg_str: str = 'hello there'
    arg_int: int = -100
    arg_float: float = 77.3
    # TODO: how to handle untyped arguments? users might accidentally think they should behave according to the inferred type
    # arg_bool_untyped_true = True
    # arg_bool_untyped_false = False
    arg_bool_true: bool = True
    arg_bool_false: bool = False
    arg_list_str: List[str] = ['hello', 'how are you']
    arg_list_int: List[int] = [10, -11]
    arg_list_float: List[float] = [3.14, 6.28]
    arg_list_str_empty: List[str] = []
    # arg_list_str_required: List[str]
    # TODO: move these elsewhere since we don't support them as defaults
    # arg_other_type_required: Person
    # arg_other_type_default: Person = Person('tap')


# TODO: how to check for SystemExit without the system exiting???
# class RequiredClassVariableTests(TestCase):
#     def setUp(self) -> None:
#         self.tap = IntegrationTap()
#
#     def test_arg_str_required(self):
#         self.assertRaises(SystemExit, self.tap.parse_args([
#             '--arg_list_str_required', 'hi', 'there',
#             '--arg_other_type_required', 'tappy'
#         ]))
#
#
#     def test_arg_list_str_required(self):
#         self.assertRaises(SystemExit, self.tap.parse_args([
#             '--arg_str_required', 'hello',
#             '--arg_other_type_required', 'tappy'
#         ]))


class DefaultClassVariableTests(TestCase):

    def test_get_default_args(self) -> None:
        args = IntegrationDefaultTap().parse_args()

        self.assertEqual(args.arg_untyped, 42)
        self.assertEqual(args.arg_str, 'hello there')
        self.assertEqual(args.arg_int, -100)
        self.assertEqual(args.arg_float, 77.3)
        self.assertEqual(args.arg_bool_true, True)
        self.assertEqual(args.arg_bool_false, False)
        self.assertEqual(args.arg_list_str, ['hello', 'how are you'])
        self.assertEqual(args.arg_list_int, [10, -11])
        self.assertEqual(args.arg_list_float, [3.14, 6.28])
        self.assertEqual(args.arg_list_str_empty, [])

    def test_set_default_args(self) -> None:
        arg_untyped = 'yes'
        arg_str = 'goodbye'
        arg_int = '2'
        arg_float = '1e-2'
        arg_list_str = ['hi', 'there', 'how', 'are', 'you']
        arg_list_int = ['1', '2', '3', '10', '-11']
        arg_list_float = ['2.2', '-3.3', '2e20']
        arg_list_str_empty = []

        args = IntegrationDefaultTap().parse_args([
            '--arg_untyped', arg_untyped,
            '--arg_str', arg_str,
            '--arg_int', arg_int,
            '--arg_float', arg_float,
            '--arg_bool_true',
            '--arg_bool_false',
            '--arg_list_str', *arg_list_str,
            '--arg_list_int', *arg_list_int,
            '--arg_list_float', *arg_list_float,
            '--arg_list_str_empty', *arg_list_str_empty,
        ])

        arg_int = int(arg_int)
        arg_float = float(arg_float)
        arg_list_int = [int(arg) for arg in arg_list_int]
        arg_list_float = [float(arg) for arg in arg_list_float]

        self.assertEqual(args.arg_untyped, arg_untyped)
        self.assertEqual(args.arg_str, arg_str)
        self.assertEqual(args.arg_int, arg_int)
        self.assertEqual(args.arg_float, arg_float)
        # Note: setting the bools as flags results in the opposite of their default
        self.assertEqual(args.arg_bool_true, False)
        self.assertEqual(args.arg_bool_false, True)
        self.assertEqual(args.arg_list_str, arg_list_str)
        self.assertEqual(args.arg_list_int, arg_list_int)
        self.assertEqual(args.arg_list_float, arg_list_float)
        self.assertEqual(args.arg_list_str_empty, arg_list_str_empty)


class AddArgumentTests(TestCase):
    def test_positional(self):
        class IntegrationComplexTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('arg_str')

        arg_str = 'positional'
        self.args = IntegrationComplexTap().parse_args([arg_str])

        self.assertEqual(self.args.arg_str, arg_str)





"""
- option strings with two dashes
- option strings with one dash
- option strings with one dash and two dashes
- positional arguments
- required/default arguments
- default types we support: int, str, float, bool, List[str], List[int], List[bool]
- crash if default type not supported
- user providing add_arguments that are class variables
- user providing add_arguments that are not class variables (should function but won't have class variable benefits)
- user providing fancier types in add_arguments
- user contradicting default/type etc and user repeating them
- user specifying process_args
- test save args
- test get reproducibility info
- test as_dict
- test str?
"""


if __name__ == '__main__':
    unittest.main()
