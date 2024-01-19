"""
Tests `tap.to_tap_class`.

TODO: test help message, test subclass_tap_weird, test with func_kwargs
TODO: I might redesign this soon. It's not thorough yet.
"""
import dataclasses
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import pydantic
import pytest

from tap import to_tap_class, Tap


@dataclasses.dataclass
class _Args:
    """These are the argument names which every type of class or function must contain."""

    arg_str: str = dataclasses.field(metadata=dict(description="some string"))
    arg_bool: bool = True
    arg_list: Optional[List[str]] = dataclasses.field(default=None, metadata=dict(description="some list of strings"))


def _monkeypatch_eq(cls):
    """Monkey-patches `cls.__eq__` to check that the attribute values are equal to a dataclass representation of them"""

    def _equality(self, other: _Args) -> bool:
        return _Args(self.arg_str, self.arg_bool, self.arg_list) == other

    cls.__eq__ = _equality
    return cls


# Define a few different classes or functions which all take the same arguments (same by name, annotation, and default
# if not required)


def function(arg_str: str, arg_bool: bool = True, arg_list: Optional[List[str]] = None) -> _Args:
    """
    :param arg_str: some string
    :param arg_list: some list of strings
    """
    return _Args(*locals().values())


@_monkeypatch_eq
class Class:
    def __init__(self, arg_str: str, arg_bool: bool = True, arg_list: Optional[List[str]] = None):
        """
        :param arg_str: some string
        :param arg_list: some list of strings
        """
        self.arg_str = arg_str
        self.arg_bool = arg_bool
        self.arg_list = arg_list


DataclassBuiltin = _Args
"""Dataclass (builtin)"""


@_monkeypatch_eq
@pydantic.dataclasses.dataclass
class DataclassPydantic:
    """Dataclass (pydantic)"""

    arg_str: str = pydantic.dataclasses.Field(description="some string")
    arg_bool: bool = pydantic.dataclasses.Field(default=True)
    arg_list: Optional[List[str]] = pydantic.Field(default=None, description="some list of strings")


@_monkeypatch_eq
class Model(pydantic.BaseModel):
    """Pydantic model"""

    arg_str: str = pydantic.Field(description="some string")
    arg_bool: bool = pydantic.Field(default=True)
    arg_list: Optional[List[str]] = pydantic.Field(default=None, description="some list of strings")


# Define some functions which take a class or function and calls `tap.to_tap_class` on it to create a `tap.Tap`
# subclass (class, not instance)


def subclass_tap_simple(class_or_function: Any) -> Type[Tap]:
    return to_tap_class(class_or_function)  # plain subclass / do nothing


# TODO: use this. Will need to change how the test is parametrized b/c the output will depend on using
# subclass_tap_simple vs subclass_tap_weird
def subclass_tap_weird(class_or_function):
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
                raise ValueError("nope")

            # No auto-complete (and other niceties) for the super class attributes b/c this is a dynamic subclass. Sorry
            if self.arg_bool:
                self.arg_str += " processed"

    return TapSubclass


@pytest.mark.parametrize("subclasser", [subclass_tap_simple])
@pytest.mark.parametrize(
    "class_or_function",
    [
        function,
        Class,
        DataclassBuiltin,
        DataclassBuiltin(
            "to_tap_class works on instances of data models (for free). It ignores the attribute values",
            arg_bool=False,
            arg_list=["doesn't", "matter"],
        ),
        DataclassPydantic,
        DataclassPydantic(arg_str="...", arg_bool=False, arg_list=[]),
        Model,
        Model(arg_str="...", arg_bool=False, arg_list=[]),
    ],
)
@pytest.mark.parametrize(
    "args_string_and_arg_to_expected_value",
    [
        (
            "--arg_str test --arg_list x y z",
            {"arg_str": "test", "arg_bool": True, "arg_list": ["x", "y", "z"]},
        ),
        (
            "--arg_str test --arg_list x y z --arg_bool",
            {"arg_str": "test", "arg_bool": False, "arg_list": ["x", "y", "z"]},
        ),
        # The rest are invalid argument combos. This fact is indicated by the 2nd elt being a BaseException instance
        (
            "--arg_list x y z --arg_bool",  # Missing required arg_str
            SystemExit(),
        ),
    ],
)
def test_to_tap_class(
    subclasser: Callable[[Any], Type[Tap]],
    class_or_function: Any,
    args_string_and_arg_to_expected_value: Tuple[str, Union[Dict[str, Any], BaseException]],
):
    args_string, arg_to_expected_value = args_string_and_arg_to_expected_value
    TapSubclass = subclasser(class_or_function)
    tap = TapSubclass(description="My description")

    # args_string is an invalid argument combo
    if isinstance(arg_to_expected_value, BaseException):
        expected_exception = arg_to_expected_value.__class__
        expected_error_message = str(arg_to_expected_value) or None
        with pytest.raises(expected_exception=expected_exception, match=expected_error_message):
            args = tap.parse_args(args_string.split())
        return

    # args_string is a valid argument combo
    args = tap.parse_args(args_string.split())
    for arg, expected_value in arg_to_expected_value.items():
        assert getattr(args, arg) == expected_value
    if callable(class_or_function):
        result = class_or_function(**args.as_dict())
        assert result == _Args(**arg_to_expected_value)
