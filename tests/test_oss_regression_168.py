from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import pytest

from tap import Positional, TapIgnore, tapify, to_tap_class
from tap.tapify import _tap_data_from_class_or_function

if TYPE_CHECKING:
    Unused = str

Count = int


class Driver:
    def __init__(
        self, value: Count, name: str = "driver", hidden: TapIgnore[str] = "hidden", **kwargs: Unused
    ) -> Unused:
        self.value = value
        self.name = name
        self.hidden = hidden


class InheritedDriver(Driver):
    pass


class ScopedDriver:
    Value = int

    def __init__(self, value: Value):
        self.value = value


def drive(value: Count, name: str = "driver", hidden: TapIgnore[str] = "hidden", **kwargs: Unused) -> Unused:
    return Driver(value, name, hidden)


@pytest.mark.parametrize("target", [Driver, InheritedDriver, ScopedDriver, drive])
def test_postponed_parameter_annotations(target):
    data = _tap_data_from_class_or_function(target, {}, {})
    assert data.args_data[0].annotation is int, "postponed parameter annotations must resolve in their defining scope"

    result = tapify(target, command_line_args=["--value", "42"])
    assert result.value == 42
    parser = to_tap_class(target)().parse_args(["--value", "7"])
    assert parser.value == 7
    if target is not ScopedDriver:
        assert result.name == "driver"
        assert result.hidden == "hidden"
        assert "hidden" not in parser.as_dict()


def positional(value: Annotated[int, "metadata"], label: Positional[str]):
    return value, label


def test_postponed_annotation_metadata():
    data = _tap_data_from_class_or_function(positional, {}, {})
    assert data.args_data[0].annotation == Annotated[int, "metadata"], "annotation metadata must be preserved"
    assert tapify(positional, command_line_args=["--value", "42", "label"]) == (42, "label")
