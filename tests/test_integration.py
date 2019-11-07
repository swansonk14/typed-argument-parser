from typing import List, Optional, Set
import unittest
from unittest import TestCase
import sys 

from tap import Tap


class EdgeCaseTests(TestCase):
    def test_empty(self) -> None:
        class EmptyTap(Tap):
            pass

        EmptyTap().parse_args()

    def test_empty_add_argument(self) -> None:
        class EmptyAddArgument(Tap):
            def add_arguments(self) -> None:
                self.add_argument('--hi')

        hi = 'yo'
        args = EmptyAddArgument().parse_args(['--hi', hi])
        self.assertEqual(args.hi, hi)

    def test_no_typed_args(self) -> None:
        class NoTypedTap(Tap):
            hi = 3

        args = NoTypedTap().parse_args()
        self.assertEqual(args.hi, 3)

        hi = 'yo'
        args = NoTypedTap().parse_args(['--hi', hi])
        self.assertEqual(args.hi, hi)

    def test_only_typed_args(self) -> None:
        class OnlyTypedTap(Tap):
            hi: str = 'sup'

        args = OnlyTypedTap().parse_args()
        self.assertEqual(args.hi, 'sup')

        hi = 'yo'
        args = OnlyTypedTap().parse_args(['--hi', hi])
        self.assertEqual(args.hi, hi)

    def test_type_as_string(self) -> None:
        class TypeAsString(Tap):
            a_number: "int" = 3
            a_list: "List[float]" = [3.7, 0.3]

        args = TypeAsString().parse_args()
        self.assertEqual(args.a_number, 3)
        self.assertEqual(args.a_list, [3.7, 0.3])

        a_number = 42
        a_list = [3, 4, 0.7]

        args = TypeAsString().parse_args(
            ['--a_number', str(a_number), '--a_list'] + [str(i) for i in a_list]
        )
        self.assertEqual(args.a_number, a_number)
        self.assertEqual(args.a_list, a_list)


class RequiredClassVariableTests(TestCase):

    def setUp(self) -> None:
        class RequiredArgumentsParser(Tap):
            arg_str_required: str
            arg_list_str_required: List[str]

        self.tap = RequiredArgumentsParser()

        # Suppress prints from SystemExit
        class DevNull:
            def write(self, msg):
                pass
        self.dev_null = DevNull()

    def test_arg_str_required(self):
        with self.assertRaises(SystemExit):
            sys.stderr = self.dev_null
            self.tap.parse_args([
                '--arg_str_required', 'tappy',
            ])

    def test_arg_list_str_required(self):
        with self.assertRaises(SystemExit):
            sys.stderr = self.dev_null
            self.tap.parse_args([
                '--arg_list_str_required', 'hi', 'there',
            ])
    
    def test_both_assigned_okay(self):
        args = self.tap.parse_args([
            '--arg_str_required', 'tappy',
            '--arg_list_str_required', 'hi', 'there',
        ])
        self.assertEqual(args.arg_str_required, 'tappy')
        self.assertEqual(args.arg_list_str_required, ['hi', 'there'])


class Person:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other) -> bool:
        if not isinstance(other, Person):
            return False

        return self.name == other.name


class IntegrationDefaultTap(Tap):
    """Documentation is boring"""
    arg_untyped = 42
    arg_str: str = 'hello there'
    arg_int: int = -100
    arg_float: float = 77.3
    # TODO: how to handle untyped arguments? users might accidentally think they should behave according to the inferred type
    # arg_bool_untyped_true = True
    # arg_bool_untyped_false = False
    arg_bool_true: bool = True
    arg_bool_false: bool = False
    arg_optional_str: Optional[str] = None
    arg_optional_int: Optional[int] = None
    arg_optional_float: Optional[float] = None
    arg_list_str: List[str] = ['hello', 'how are you']
    arg_list_int: List[int] = [10, -11]
    arg_list_float: List[float] = [3.14, 6.28]
    arg_list_str_empty: List[str] = []
    arg_set_str: Set[str] = {'hello', 'how are you'}
    arg_set_int: Set[int] = {10, -11}
    arg_set_float: Set[float] = {3.14, 6.28}
    # TODO: move these elsewhere since we don't support them as defaults
    # arg_other_type_required: Person
    # arg_other_type_default: Person = Person('tap')


class SubclassTests(TestCase):
    def test_subclass(self):
        class IntegrationSubclassTap(IntegrationDefaultTap):
            arg_subclass_untyped = 33
            arg_subclass_str: str = 'hello'
            arg_subclass_str_required: str
            arg_subclass_str_set_me: str = 'goodbye'
            arg_float: float = -2.7

        arg_subclass_str_required = 'subclassing is fun'
        arg_subclass_str_set_me = 'all set!'
        arg_int = '77'
        self.args = IntegrationSubclassTap().parse_args([
            '--arg_subclass_str_required', arg_subclass_str_required,
            '--arg_subclass_str_set_me', arg_subclass_str_set_me,
            '--arg_int', arg_int
        ])

        arg_int = int(arg_int)

        self.assertEqual(self.args.arg_str, IntegrationDefaultTap.arg_str)
        self.assertEqual(self.args.arg_int, arg_int)
        self.assertEqual(self.args.arg_float, -2.7)
        self.assertEqual(self.args.arg_subclass_str_required, arg_subclass_str_required)
        self.assertEqual(self.args.arg_subclass_str_set_me, arg_subclass_str_set_me)


class DefaultClassVariableTests(TestCase):

    def test_get_default_args(self) -> None:
        args = IntegrationDefaultTap().parse_args()

        self.assertEqual(args.arg_untyped, 42)
        self.assertEqual(args.arg_str, 'hello there')
        self.assertEqual(args.arg_int, -100)
        self.assertEqual(args.arg_float, 77.3)
        self.assertEqual(args.arg_bool_true, True)
        self.assertEqual(args.arg_bool_false, False)
        self.assertTrue(args.arg_optional_str is None)
        self.assertTrue(args.arg_optional_int is None)
        self.assertTrue(args.arg_optional_float is None)
        self.assertEqual(args.arg_list_str, ['hello', 'how are you'])
        self.assertEqual(args.arg_list_int, [10, -11])
        self.assertEqual(args.arg_list_float, [3.14, 6.28])
        self.assertEqual(args.arg_list_str_empty, [])
        self.assertEqual(args.arg_set_str, {'hello', 'how are you'})
        self.assertEqual(args.arg_set_int, {10, -11})
        self.assertEqual(args.arg_set_float, {3.14, 6.28})

    def test_set_default_args(self) -> None:
        arg_untyped = 'yes'
        arg_str = 'goodbye'
        arg_int = '2'
        arg_float = '1e-2'
        arg_optional_str = 'hello'
        arg_optional_int = '77'
        arg_optional_float = '7.7'
        arg_list_str = ['hi', 'there', 'how', 'are', 'you']
        arg_list_int = ['1', '2', '3', '10', '-11']
        arg_list_float = ['2.2', '-3.3', '2e20']
        arg_list_str_empty = []
        arg_set_str = ['hi', 'hi', 'hi', 'how']
        arg_set_int = ['1', '2', '2', '2', '3']
        arg_set_float = ['1.23', '4.4', '1.23']


        args = IntegrationDefaultTap().parse_args([
            '--arg_untyped', arg_untyped,
            '--arg_str', arg_str,
            '--arg_int', arg_int,
            '--arg_float', arg_float,
            '--arg_bool_true',
            '--arg_bool_false',
            '--arg_optional_str', arg_optional_str,
            '--arg_optional_int', arg_optional_int,
            '--arg_optional_float', arg_optional_float,
            '--arg_list_str', *arg_list_str,
            '--arg_list_int', *arg_list_int,
            '--arg_list_float', *arg_list_float,
            '--arg_list_str_empty', *arg_list_str_empty,
            '--arg_set_str', *arg_set_str,
            '--arg_set_int', *arg_set_int,
            '--arg_set_float', *arg_set_float
        ])

        arg_int = int(arg_int)
        arg_float = float(arg_float)
        arg_optional_int = float(arg_optional_int)
        arg_optional_float = float(arg_optional_float)
        arg_list_int = [int(arg) for arg in arg_list_int]
        arg_list_float = [float(arg) for arg in arg_list_float]
        arg_set_str = set(arg_set_str)
        arg_set_int = {int(arg) for arg in arg_set_int}
        arg_set_float = {float(arg) for arg in arg_set_float}


        self.assertEqual(args.arg_untyped, arg_untyped)
        self.assertEqual(args.arg_str, arg_str)
        self.assertEqual(args.arg_int, arg_int)
        self.assertEqual(args.arg_float, arg_float)
        # Note: setting the bools as flags results in the opposite of their default
        self.assertEqual(args.arg_bool_true, False)
        self.assertEqual(args.arg_bool_false, True)
        self.assertEqual(args.arg_optional_str, arg_optional_str)
        self.assertEqual(args.arg_optional_int, arg_optional_int)
        self.assertEqual(args.arg_optional_float, arg_optional_float)
        self.assertEqual(args.arg_list_str, arg_list_str)
        self.assertEqual(args.arg_list_int, arg_list_int)
        self.assertEqual(args.arg_list_float, arg_list_float)
        self.assertEqual(args.arg_list_str_empty, arg_list_str_empty)
        self.assertEqual(args.arg_set_str, arg_set_str)
        self.assertEqual(args.arg_set_int, arg_set_int)
        self.assertEqual(args.arg_set_float, arg_set_float)


class AddArgumentTests(TestCase):
    def test_positional(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('arg_str')

        arg_str = 'positional'
        self.args = IntegrationAddArgumentTap().parse_args([arg_str])

        self.assertEqual(self.args.arg_str, arg_str)

    def test_positional_ordering(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('arg_str')
                self.add_argument('arg_int')
                self.add_argument('arg_float')

        arg_str = 'positional'
        arg_int = '5'
        arg_float = '1.1'
        self.args = IntegrationAddArgumentTap().parse_args([arg_str, arg_int, arg_float])

        arg_int = int(arg_int)
        arg_float = float(arg_float)

        self.assertEqual(self.args.arg_str, arg_str)
        self.assertEqual(self.args.arg_int, arg_int)
        self.assertEqual(self.args.arg_float, arg_float)

    def test_one_dash(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('-arg_str')

        arg_str = 'one_dash'
        self.args = IntegrationAddArgumentTap().parse_args(['-arg_str', arg_str])

        self.assertEqual(self.args.arg_str, arg_str)

    def test_two_dashes(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('--arg_str')

        arg_str = 'two_dashes'
        self.args = IntegrationAddArgumentTap().parse_args(['--arg_str', arg_str])

        self.assertEqual(self.args.arg_str, arg_str)

    def test_one_and_two_dashes(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('-a', '--arg_str')

        arg_str = 'one_or_two_dashes'
        self.args = IntegrationAddArgumentTap().parse_args(['-a', arg_str])

        self.assertEqual(self.args.arg_str, arg_str)

        self.args = IntegrationAddArgumentTap().parse_args(['--arg_str', arg_str])

        self.assertEqual(self.args.arg_str, arg_str)

    def test_not_class_variable(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('--non_class_arg')

        arg_str = 'non_class_arg'
        self.tap = IntegrationAddArgumentTap()
        self.assertFalse('non_class_arg' in self.tap._get_argument_names())  # ensure it's actually not a class variable
        self.args = self.tap.parse_args(['--non_class_arg', arg_str])

        self.assertEqual(self.args.non_class_arg, arg_str)

    def test_complex_type(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            arg_person: Person = Person('tap')
            # arg_person_required: Person  # TODO
            arg_person_untyped = Person('tap untyped')

            # TODO: assert a crash if any complex types are not explicitly added in add_argument
            def add_arguments(self) -> None:
                self.add_argument('--arg_person', type=Person)
                # self.add_argument('--arg_person_required', type=Person)  # TODO
                self.add_argument('--arg_person_untyped', type=Person)

        args = IntegrationAddArgumentTap().parse_args()
        self.assertEqual(args.arg_person, Person('tap'))
        self.assertEqual(args.arg_person_untyped, Person('tap untyped'))

        arg_person = Person('hi there')
        arg_person_untyped = Person('heyyyy')
        args = IntegrationAddArgumentTap().parse_args([
            '--arg_person', arg_person.name,
            '--arg_person_untyped', arg_person_untyped.name
        ])
        self.assertEqual(args.arg_person, arg_person)
        self.assertEqual(args.arg_person_untyped, arg_person_untyped)

    def test_repeat_default(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('--arg_str', default=IntegrationDefaultTap.arg_str)

        args = IntegrationAddArgumentTap().parse_args()
        self.assertEqual(args.arg_str, IntegrationDefaultTap.arg_str)

    def test_conflicting_default(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('--arg_str', default='yo dude')

        args = IntegrationAddArgumentTap().parse_args()
        self.assertEqual(args.arg_str, 'yo dude')

    # TODO: this
    def test_repeat_required(self) -> None:
        pass

    # TODO: this
    def test_conflicting_required(self) -> None:
        pass

    def test_repeat_type(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('--arg_int', type=int)

        args = IntegrationAddArgumentTap().parse_args()
        self.assertEqual(type(args.arg_int), int)
        self.assertEqual(args.arg_int, IntegrationDefaultTap.arg_int)

        arg_int = '99'
        args = IntegrationAddArgumentTap().parse_args(['--arg_int', arg_int])
        arg_int = int(arg_int)
        self.assertEqual(type(args.arg_int), int)
        self.assertEqual(args.arg_int, arg_int)

    def test_conflicting_type(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('--arg_int', type=str)

        arg_int = 'yo dude'
        args = IntegrationAddArgumentTap().parse_args(['--arg_int', arg_int])
        self.assertEqual(type(args.arg_int), str)
        self.assertEqual(args.arg_int, arg_int)

    # TODO
    def test_repeat_help(self) -> None:
        pass

    # TODO
    def test_conflicting_help(self) -> None:
        pass

    def test_repeat_nargs(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('--arg_list_str', nargs='*')

        arg_list_str = ['hi', 'there', 'person', '123']
        args = IntegrationAddArgumentTap().parse_args(['--arg_list_str', *arg_list_str])
        self.assertEqual(args.arg_list_str, arg_list_str)

    # TODO: figure out how to check for system exit
    # def test_conflicting_nargs(self) -> None:
    #     class IntegrationAddArgumentTap(IntegrationDefaultTap):
    #         def add_arguments(self) -> None:
    #             self.add_argument('--arg_list_str', nargs=3)
    #
    #     arg_list_str = ['hi', 'there', 'person', '123']
    #     self.assertRaises(SystemExit, IntegrationAddArgumentTap().parse_args(['--arg_list_str', *arg_list_str]))

    def test_repeat_action(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('--arg_bool_false', action='store_true', default=False)

        args = IntegrationAddArgumentTap().parse_args()
        self.assertEqual(args.arg_bool_false, False)

        args = IntegrationAddArgumentTap().parse_args(['--arg_bool_false'])
        self.assertEqual(args.arg_bool_false, True)

    def test_conflicting_action(self) -> None:
        class IntegrationAddArgumentTap(IntegrationDefaultTap):
            def add_arguments(self) -> None:
                self.add_argument('--arg_bool_false', action='store_false', default=True)

        args = IntegrationAddArgumentTap().parse_args()
        self.assertEqual(args.arg_bool_false, True)

        args = IntegrationAddArgumentTap().parse_args(['--arg_bool_false'])
        self.assertEqual(args.arg_bool_false, False)   


class KnownTap(Tap):
    arg_int: int = 2


class ParseKnownArgsTests(TestCase):
    arg_int = 3
    arg_float = 3.3

    def test_all_known(self):
        args = KnownTap().parse_args([
            '--arg_int', str(self.arg_int)
        ], known_only=True)
        self.assertEqual(args.arg_int, self.arg_int)
        self.assertEqual(args.extra_args, [])

    def test_some_known(self):
        args = KnownTap().parse_args([
            '--arg_int', str(self.arg_int),
            '--arg_float', str(self.arg_float)
        ], known_only=True)
        self.assertEqual(args.arg_int, self.arg_int)
        self.assertEqual(args.extra_args, ['--arg_float', '3.3'])

    def test_none_known(self):
        args = KnownTap().parse_args([
            '--arg_float', str(self.arg_float)
        ], known_only=True)
        self.assertEqual(args.extra_args, ['--arg_float', '3.3'])


"""
- crash if default type not supported
- user specifying process_args
- test save args
- test get reproducibility info
- test as_dict
- test str?
- test comments
"""


if __name__ == '__main__':
    unittest.main()
