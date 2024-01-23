"""
Tests `tap.to_tap_class`. This test works for Pydantic v1 and v2.
"""
from contextlib import redirect_stdout, redirect_stderr
import dataclasses
import io
import re
import sys
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, Union

import pydantic
import pytest

from tap import to_tap_class, Tap


_IS_PYDANTIC_V1 = pydantic.__version__ < "2.0.0"

# To properly test the help message, we need to know how argparse formats it. It changed from 3.8 -> 3.9 -> 3.10
_IS_BEFORE_PY_310 = sys.version_info < (3, 10)
_OPTIONS_TITLE = "options" if not _IS_BEFORE_PY_310 else "optional arguments"
_ARG_LIST_DOTS = "..." if not sys.version_info < (3, 9) else "[ARG_LIST ...]"


@dataclasses.dataclass
class _Args:
    """
    These are the arguments which every type of class or function must contain.
    """

    arg_int: int = dataclasses.field(metadata=dict(description="some integer"))
    arg_bool: bool = True
    arg_list: Optional[List[str]] = dataclasses.field(default=None, metadata=dict(description="some list of strings"))


def _monkeypatch_eq(cls):
    """
    Monkey-patches `cls.__eq__` to check that the attribute values are equal to a dataclass representation of them.
    """

    def _equality(self, other: _Args) -> bool:
        return _Args(self.arg_int, arg_bool=self.arg_bool, arg_list=self.arg_list) == other

    cls.__eq__ = _equality
    return cls


# Define a few different classes or functions which all take the same arguments (same by name, annotation, and default
# if not required)


def function(arg_int: int, arg_bool: bool = True, arg_list: Optional[List[str]] = None) -> _Args:
    """
    :param arg_int: some integer
    :param arg_list: some list of strings
    """
    return _Args(arg_int, arg_bool=arg_bool, arg_list=arg_list)


@_monkeypatch_eq
class Class:
    def __init__(self, arg_int: int, arg_bool: bool = True, arg_list: Optional[List[str]] = None):
        """
        :param arg_int: some integer
        :param arg_list: some list of strings
        """
        self.arg_int = arg_int
        self.arg_bool = arg_bool
        self.arg_list = arg_list


DataclassBuiltin = _Args


@_monkeypatch_eq
@pydantic.dataclasses.dataclass
class DataclassPydantic:
    """
    Dataclass (pydantic)
    """

    # Mixing field types should be ok
    arg_int: int = pydantic.dataclasses.Field(description="some integer")
    arg_bool: bool = pydantic.dataclasses.Field(default=True)
    arg_list: Optional[List[str]] = pydantic.Field(default=None, description="some list of strings")


@_monkeypatch_eq
@pydantic.dataclasses.dataclass
class DataclassPydanticV1:  # for Pydantic v1 data models, we rely on the docstring to get descriptions
    """
    Dataclass (pydantic v1)

    :param arg_int: some integer
    :param arg_list: some list of strings
    """

    arg_int: int
    arg_bool: bool = True
    arg_list: Optional[List[str]] = None


@_monkeypatch_eq
class Model(pydantic.BaseModel):
    """
    Pydantic model
    """

    # Mixing field types should be ok
    arg_int: int = pydantic.Field(description="some integer")
    arg_bool: bool = pydantic.Field(default=True)
    arg_list: Optional[List[str]] = pydantic.dataclasses.Field(default=None, description="some list of strings")


@_monkeypatch_eq
class ModelV1(pydantic.BaseModel):  # for Pydantic v1 data models, we rely on the docstring to get descriptions
    """
    Pydantic model (pydantic v1)

    :param arg_int: some integer
    :param arg_list: some list of strings
    """

    arg_int: int
    arg_bool: bool = True
    arg_list: Optional[List[str]] = None


@pytest.fixture(
    scope="module",
    params=[
        function,
        Class,
        DataclassBuiltin,
        DataclassBuiltin(
            1, arg_bool=False, arg_list=["these", "values", "don't", "matter"]
        ),  # to_tap_class also works on instances of data models. It ignores the attribute values
        DataclassPydantic if not _IS_PYDANTIC_V1 else DataclassPydanticV1,
        Model if not _IS_PYDANTIC_V1 else ModelV1,
        # We can test instances of DataclassPydantic and Model for pydantic v2 but not v1
    ],
)
def data_model(request: pytest.FixtureRequest):
    """
    Same meaning as class_or_function. Only difference is that data_model is parametrized.
    """
    return request.param


# Define some functions which take a class or function and calls `tap.to_tap_class` on it to create a `tap.Tap`
# subclass (class, not instance)


def subclasser_simple(class_or_function: Any) -> Type[Tap]:
    """
    Plain subclass, does nothing extra.
    """
    return to_tap_class(class_or_function)


def subclasser_complex(class_or_function):
    """
    It's conceivable that someone has a data model, but they want to add more arguments or handling when running a
    script.
    """

    def to_number(string: str) -> Union[float, int]:
        return float(string) if "." in string else int(string)

    class TapSubclass(to_tap_class(class_or_function)):
        # You can supply additional arguments here
        argument_with_really_long_name: Union[float, int] = 3
        "This argument has a long name and will be aliased with a short one"

        def configure(self) -> None:
            # You can still add special argument behavior
            self.add_argument("-arg", "--argument_with_really_long_name", type=to_number)

        def process_args(self) -> None:
            # You can still validate and modify arguments
            if self.argument_with_really_long_name > 4:
                raise ValueError("argument_with_really_long_name cannot be > 4")

            # No auto-complete (and other niceties) for the super class attributes b/c this is a dynamic subclass. Sorry
            if self.arg_bool and self.arg_list is not None:
                self.arg_list.append("processed")

    return TapSubclass


def subclasser_subparser(class_or_function):
    class SubparserA(Tap):
        bar: int  # bar help

    class SubparserB(Tap):
        baz: Literal["X", "Y", "Z"]  # baz help

    class TapSubclass(to_tap_class(class_or_function)):
        foo: bool = False  # foo help

        def configure(self):
            self.add_subparsers(help="sub-command help")
            self.add_subparser("a", SubparserA, help="a help", description="Description (a)")
            self.add_subparser("b", SubparserB, help="b help")

    return TapSubclass


# Test that the subclasser parses the args correctly or raises the correct error.
# The subclassers are tested separately b/c the parametrizaiton of args_string_and_arg_to_expected_value depends on the
# subclasser.
# First, some helper functions.


def _test_raises_system_exit(tap: Tap, args_string: str) -> str:
    is_help = (
        args_string.endswith("-h")
        or args_string.endswith("--help")
        or " -h " in args_string
        or " --help " in args_string
    )
    f = io.StringIO()
    with redirect_stdout(f) if is_help else redirect_stderr(f):
        with pytest.raises(SystemExit):
            tap.parse_args(args_string.split())

    return f.getvalue()


def _test_subclasser(
    subclasser: Callable[[Any], Type[Tap]],
    class_or_function: Any,
    args_string_and_arg_to_expected_value: Tuple[str, Union[Dict[str, Any], BaseException]],
    test_call: bool = True,
):
    """
    Tests that the `subclasser` converts `class_or_function` to a `Tap` class which parses the argument string
    correctly.

    Setting `test_call=True` additionally tests that calling the `class_or_function` on the parsed arguments works.
    """
    args_string, arg_to_expected_value = args_string_and_arg_to_expected_value
    TapSubclass = subclasser(class_or_function)
    assert issubclass(TapSubclass, Tap)
    tap = TapSubclass(description="Script description")  # description is a kwarg for argparse.ArgumentParser

    # args_string is an invalid argument combo
    if isinstance(arg_to_expected_value, SystemExit):
        # We need to get the error message by reading stdout
        stderr = _test_raises_system_exit(tap, args_string)
        assert str(arg_to_expected_value) in stderr
        return
    if isinstance(arg_to_expected_value, BaseException):
        expected_exception = arg_to_expected_value.__class__
        expected_error_message = str(arg_to_expected_value) or None
        with pytest.raises(expected_exception=expected_exception, match=expected_error_message):
            args = tap.parse_args(args_string.split())
        return

    # args_string is a valid argument combo
    # Test that parsing works correctly
    args = tap.parse_args(args_string.split())
    assert arg_to_expected_value == args.as_dict()
    if test_call and callable(class_or_function):
        result = class_or_function(**args.as_dict())
        assert result == _Args(**arg_to_expected_value)


def _test_subclasser_message(
    subclasser: Callable[[Any], Type[Tap]],
    class_or_function: Any,
    message_expected: str,
    description: str = "Script description",
    args_string: str = "-h",
):
    """
    Tests that::

        subclasser(class_or_function)(description=description).parse_args(args_string.split())

    outputs `message_expected` to stdout, ignoring differences in whitespaces/newlines/tabs.
    """

    def replace_whitespace(string: str) -> str:
        return re.sub(r"\s+", " ", string).strip()  # FYI this line was written by an LLM

    TapSubclass = subclasser(class_or_function)
    tap = TapSubclass(description=description)
    message = _test_raises_system_exit(tap, args_string)
    # Standardize to ignore trivial differences due to terminal settings
    assert replace_whitespace(message) == replace_whitespace(message_expected)


# Test sublcasser_simple


@pytest.mark.parametrize(
    "args_string_and_arg_to_expected_value",
    [
        (
            "--arg_int 1 --arg_list x y z",
            {"arg_int": 1, "arg_bool": True, "arg_list": ["x", "y", "z"]},
        ),
        (
            "--arg_int 1 --arg_bool",
            {"arg_int": 1, "arg_bool": False, "arg_list": None},
        ),
        # The rest are invalid argument combos, as indicated by the 2nd elt being a BaseException instance
        (
            "--arg_list x y z --arg_bool",
            SystemExit("error: the following arguments are required: --arg_int"),
        ),
        (
            "--arg_int not_an_int --arg_list x y z --arg_bool",
            SystemExit("error: argument --arg_int: invalid int value: 'not_an_int'"),
        ),
    ],
)
def test_subclasser_simple(
    data_model: Any, args_string_and_arg_to_expected_value: Tuple[str, Union[Dict[str, Any], BaseException]]
):
    _test_subclasser(subclasser_simple, data_model, args_string_and_arg_to_expected_value)


# @pytest.mark.skipif(_IS_BEFORE_PY_310, reason="argparse is different. Need to fix help_message_expected")
def test_subclasser_simple_help_message(data_model: Any):
    description = "Script description"
    help_message_expected = f"""
usage: pytest --arg_int ARG_INT [--arg_bool] [--arg_list [ARG_LIST {_ARG_LIST_DOTS}]] [-h]

{description}

{_OPTIONS_TITLE}:
  --arg_int ARG_INT     (int, required) some integer
  --arg_bool            (bool, default=True)
  --arg_list [ARG_LIST {_ARG_LIST_DOTS}]
                        ({str(Optional[List[str]]).replace('typing.', '')}, default=None) some list of strings
  -h, --help            show this help message and exit
""".lstrip(
        "\n"
    )
    _test_subclasser_message(subclasser_simple, data_model, help_message_expected, description=description)


# Test subclasser_complex


@pytest.mark.parametrize(
    "args_string_and_arg_to_expected_value",
    [
        (
            "--arg_int 1 --arg_list x y z",
            {
                "arg_int": 1,
                "arg_bool": True,
                "arg_list": ["x", "y", "z", "processed"],
                "argument_with_really_long_name": 3,
            },
        ),
        (
            "--arg_int 1 --arg_list x y z -arg 2",
            {
                "arg_int": 1,
                "arg_bool": True,
                "arg_list": ["x", "y", "z", "processed"],
                "argument_with_really_long_name": 2,
            },
        ),
        (
            "--arg_int 1 --arg_bool --argument_with_really_long_name 2.3",
            {
                "arg_int": 1,
                "arg_bool": False,
                "arg_list": None,
                "argument_with_really_long_name": 2.3,
            },
        ),
        # The rest are invalid argument combos, as indicated by the 2nd elt being a BaseException instance
        (
            "--arg_list x y z --arg_bool",
            SystemExit("error: the following arguments are required: --arg_int"),
        ),
        (
            "--arg_int 1 --arg_list x y z -arg not_a_float_or_int",
            SystemExit(
                "error: argument -arg/--argument_with_really_long_name: invalid to_number value: 'not_a_float_or_int'"
            ),
        ),
        (
            "--arg_int 1 --arg_list x y z -arg 5",  # Wrong value arg (aliases argument_with_really_long_name)
            ValueError("argument_with_really_long_name cannot be > 4"),
        ),
    ],
)
def test_subclasser_complex(
    data_model: Any, args_string_and_arg_to_expected_value: Tuple[str, Union[Dict[str, Any], BaseException]]
):
    # Currently setting test_call=False b/c all data models except the pydantic Model don't accept extra args
    _test_subclasser(subclasser_complex, data_model, args_string_and_arg_to_expected_value, test_call=False)


# @pytest.mark.skipif(_IS_BEFORE_PY_310, reason="argparse is different. Need to fix help_message_expected")
def test_subclasser_complex_help_message(data_model: Any):
    description = "Script description"
    help_message_expected = f"""
usage: pytest [-arg ARGUMENT_WITH_REALLY_LONG_NAME] --arg_int ARG_INT [--arg_bool] [--arg_list [ARG_LIST {_ARG_LIST_DOTS}]] [-h]

{description}

{_OPTIONS_TITLE}:
  -arg ARGUMENT_WITH_REALLY_LONG_NAME, --argument_with_really_long_name ARGUMENT_WITH_REALLY_LONG_NAME
                        (Union[float, int], default=3) This argument has a long name and will be aliased with a short one
  --arg_int ARG_INT     (int, required) some integer
  --arg_bool            (bool, default=True)
  --arg_list [ARG_LIST {_ARG_LIST_DOTS}]
                        ({str(Optional[List[str]]).replace('typing.', '')}, default=None) some list of strings
  -h, --help            show this help message and exit
""".lstrip(
        "\n"
    )
    _test_subclasser_message(subclasser_complex, data_model, help_message_expected, description=description)


# Test subclasser_subparser


@pytest.mark.parametrize(
    "args_string_and_arg_to_expected_value",
    [
        (
            "--arg_int 1",
            {"arg_int": 1, "arg_bool": True, "arg_list": None, "foo": False},
        ),
        (
            "--arg_int 1 a --bar 2",
            {"arg_int": 1, "arg_bool": True, "arg_list": None, "bar": 2, "foo": False},
        ),
        (
            "--arg_int 1 --foo a --bar 2",
            {"arg_int": 1, "arg_bool": True, "arg_list": None, "bar": 2, "foo": True},
        ),
        (
            "--arg_int 1 b --baz X",
            {"arg_int": 1, "arg_bool": True, "arg_list": None, "baz": "X", "foo": False},
        ),
        (
            "--foo --arg_bool --arg_list x y z --arg_int 1 b --baz Y",
            {"arg_int": 1, "arg_bool": False, "arg_list": ["x", "y", "z"], "baz": "Y", "foo": True},
        ),
        # The rest are invalid argument combos, as indicated by the 2nd elt being a BaseException instance
        (
            "a --bar 1",
            SystemExit("error: the following arguments are required: --arg_int"),
        ),
        (
            "--arg_int not_an_int a --bar 1",
            SystemExit("error: argument --arg_int: invalid int value: 'not_an_int'"),
        ),
        (
            "--arg_int 1 --baz X --foo b",
            SystemExit(
                "error: argument {a,b}: invalid choice: 'X' (choose from 'a', 'b')"
                if sys.version_info >= (3, 9)
                else "error: invalid choice: 'X' (choose from 'a', 'b')"
            ),
        ),
        (
            "--arg_int 1 b --baz X --foo",
            SystemExit("error: unrecognized arguments: --foo"),
        ),
        (
            "--arg_int 1 --foo b --baz A",
            SystemExit("""error: argument --baz: Value for variable "baz" must be one of ['X', 'Y', 'Z']."""),
        ),
    ],
)
def test_subclasser_subparser(
    data_model: Any, args_string_and_arg_to_expected_value: Tuple[str, Union[Dict[str, Any], BaseException]]
):
    # Currently setting test_call=False b/c all data models except the pydantic Model don't accept extra args
    _test_subclasser(subclasser_subparser, data_model, args_string_and_arg_to_expected_value, test_call=False)


# @pytest.mark.skipif(_IS_BEFORE_PY_310, reason="argparse is different. Need to fix help_message_expected")
@pytest.mark.parametrize(
    "args_string_and_description_and_expected_message",
    [
        (
            "-h",
            "Script description",
            # foo help likely missing b/c class nesting. In a demo in a Python 3.8 env, foo help appears in -h
            f"""
usage: pytest [--foo] --arg_int ARG_INT [--arg_bool] [--arg_list [ARG_LIST {_ARG_LIST_DOTS}]] [-h] {{a,b}} ...

Script description

positional arguments:
  {{a,b}}               sub-command help
    a                   a help
    b                   b help

{_OPTIONS_TITLE}:
  --foo                 (bool, default=False) {'' if sys.version_info < (3, 9) else 'foo help'}
  --arg_int ARG_INT     (int, required) some integer
  --arg_bool            (bool, default=True)
  --arg_list [ARG_LIST {_ARG_LIST_DOTS}]
                        ({str(Optional[List[str]]).replace('typing.', '')}, default=None) some list of strings
  -h, --help            show this help message and exit
""",
        ),
        (
            "a -h",
            "Description (a)",
            f"""
usage: pytest a --bar BAR [-h]

Description (a)

{_OPTIONS_TITLE}:
  --bar BAR   (int, required) bar help
  -h, --help  show this help message and exit
""",
        ),
        (
            "b -h",
            "",
            f"""
usage: pytest b --baz {{X,Y,Z}} [-h]

{_OPTIONS_TITLE}:
  --baz {{X,Y,Z}}  (Literal['X', 'Y', 'Z'], required) baz help
  -h, --help     show this help message and exit
""",
        ),
    ],
)
def test_subclasser_subparser_help_message(
    data_model: Any, args_string_and_description_and_expected_message: Tuple[str, str]
):
    args_string, description, expected_message = args_string_and_description_and_expected_message
    _test_subclasser_message(
        subclasser_subparser, data_model, expected_message, description=description, args_string=args_string
    )
