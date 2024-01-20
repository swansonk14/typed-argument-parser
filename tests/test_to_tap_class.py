"""
Tests `tap.to_tap_class`.

TODO: test with func_kwargs
"""
from contextlib import redirect_stdout
import dataclasses
import io
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import pydantic
import pytest

from tap import to_tap_class, Tap


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

    arg_int: int = pydantic.dataclasses.Field(description="some integer")
    arg_bool: bool = pydantic.dataclasses.Field(default=True)
    arg_list: Optional[List[str]] = pydantic.Field(default=None, description="some list of strings")


@_monkeypatch_eq
class Model(pydantic.BaseModel):
    """
    Pydantic model
    """

    arg_int: int = pydantic.Field(description="some integer")
    arg_bool: bool = pydantic.Field(default=True)
    arg_list: Optional[List[str]] = pydantic.Field(default=None, description="some list of strings")


@pytest.fixture(
    scope="module",
    params=[
        function,
        Class,
        DataclassBuiltin,
        DataclassBuiltin(
            1, arg_bool=False, arg_list=["doesn't", "matter"]
        ),  # to_tap_class also works on instances of data models. It ignores the attribute values
        DataclassPydantic,
        DataclassPydantic(arg_int=1_000, arg_bool=False, arg_list=None),
        Model,
        Model(arg_int=1, arg_bool=True, arg_list=["not", "used"]),
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


# Test that the subclasser parses the args correctly or raises the correct error.
# The subclassers are tested separately b/c the parametrizaiton of args_string_and_arg_to_expected_value depends on the
# subclasser.


def _test_subclasser(
    subclasser: Callable[[Any], Type[Tap]],
    class_or_function: Any,
    args_string_and_arg_to_expected_value: Tuple[str, Union[Dict[str, Any], BaseException]],
    test_call: bool = True,
):
    args_string, arg_to_expected_value = args_string_and_arg_to_expected_value
    TapSubclass = subclasser(class_or_function)
    tap = TapSubclass(description="Script description")

    if isinstance(arg_to_expected_value, BaseException):
        # args_string is an invalid argument combo
        expected_exception = arg_to_expected_value.__class__
        expected_error_message = str(arg_to_expected_value) or None
        with pytest.raises(expected_exception=expected_exception, match=expected_error_message):
            args = tap.parse_args(args_string.split())
        return

    # args_string is a valid argument combo
    # Test that parsing works correctly
    args = tap.parse_args(args_string.split())
    for arg, expected_value in arg_to_expected_value.items():
        assert getattr(args, arg) == expected_value
    if test_call and callable(class_or_function):
        result = class_or_function(**args.as_dict())
        assert result == _Args(**arg_to_expected_value)


def _test_subclasser_help_message(
    subclasser: Callable[[Any], Type[Tap]], class_or_function: Any, description: str, help_message_expected: str
):
    def replace_whitespace(string: str):
        # Replace all whitespaces with a single space
        # FYI this line was written by an LLM:
        return re.sub(r"\s+", " ", string).strip()

    TapSubclass = subclasser(class_or_function)
    tap = TapSubclass(description=description)

    f = io.StringIO()
    with redirect_stdout(f):
        with pytest.raises(SystemExit):
            tap.parse_args(["-h"])

    help_message = f.getvalue()
    # Standardize to ignore trivial differences due to terminal settings
    assert replace_whitespace(help_message) == replace_whitespace(help_message_expected)


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
            "--arg_list x y z --arg_bool",  # Missing required arg_int
            SystemExit(),  # TODO: figure out how to get argparse's error message and test that it matches
        ),
        (
            "--arg_int not_an_int --arg_list x y z --arg_bool",  # Wrong type arg_int
            SystemExit(),
        ),
    ],
)
def test_subclasser_simple(
    data_model: Any, args_string_and_arg_to_expected_value: Tuple[str, Union[Dict[str, Any], BaseException]]
):
    _test_subclasser(subclasser_simple, data_model, args_string_and_arg_to_expected_value)


def test_subclasser_simple_help_message(data_model: Any):
    description = "Script description"
    help_message_expected = f"""
usage: pytest --arg_int ARG_INT [--arg_bool] [--arg_list [ARG_LIST ...]] [-h]

{description}

options:
  --arg_int ARG_INT     (int, required) some integer
  --arg_bool            (bool, default=True)
  --arg_list [ARG_LIST ...]
                        (Optional[List[str]], default=None) some list of strings
  -h, --help            show this help message and exit
""".lstrip(
        "\n"
    )
    _test_subclasser_help_message(subclasser_simple, data_model, description, help_message_expected)


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
            "--arg_list x y z --arg_bool",  # Missing required arg_int
            SystemExit(),
        ),
        (
            "--arg_int 1 --arg_list x y z -arg not_a_float_or_int",  # Wrong type
            SystemExit(),
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


def test_subclasser_complex_help_message(data_model: Any):
    description = "Script description"
    help_message_expected = f"""
usage: pytest [-arg ARGUMENT_WITH_REALLY_LONG_NAME] --arg_int ARG_INT [--arg_bool] [--arg_list [ARG_LIST ...]] [-h]

{description}

options:
  -arg ARGUMENT_WITH_REALLY_LONG_NAME, --argument_with_really_long_name ARGUMENT_WITH_REALLY_LONG_NAME
                        (Union[float, int], default=3) This argument has a long name and will be aliased with a short one
  --arg_int ARG_INT     (int, required) some integer
  --arg_bool            (bool, default=True)
  --arg_list [ARG_LIST ...]
                        (Optional[List[str]], default=None) some list of strings
  -h, --help            show this help message and exit
""".lstrip(
        "\n"
    )
    _test_subclasser_help_message(subclasser_complex, data_model, description, help_message_expected)
