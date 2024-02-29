"""
Works for Pydantic v1 and v2.

Example commands:

python demo_data_model.py -h

python demo_data_model.py \
    --arg_int 1 \
    --arg_list x y z \
    --argument_with_really_long_name 3

python demo_data_model.py \
    --arg_int 1 \
    --arg_list x y z \
    --arg_bool \
    -arg 3.14
"""
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field
from tap import tapify, to_tap_class, Tap


class Model(BaseModel):
    """
    My Pydantic Model which contains script args.
    """

    arg_int: int = Field(description="some integer")
    arg_bool: bool = Field(default=True)
    arg_list: Optional[List[str]] = Field(default=None, description="some list of strings")


def main(model: Model) -> None:
    print("Parsed args into Model:")
    print(model)


def to_number(string: str) -> Union[float, int]:
    return float(string) if "." in string else int(string)


class ModelTap(to_tap_class(Model)):
    # You can supply additional arguments here
    argument_with_really_long_name: Union[float, int] = 3
    "This argument has a long name and will be aliased with a short one"

    def configure(self) -> None:
        # You can still add special argument behavior
        self.add_argument("-arg", "--argument_with_really_long_name", type=to_number)

    def process_args(self) -> None:
        # You can still validate and modify arguments
        # (You should do this in the Pydantic Model. I'm just demonstrating that this functionality is still possible)
        if self.argument_with_really_long_name > 4:
            raise ValueError("argument_with_really_long_name cannot be > 4")

        # No auto-complete (and other niceties) for the super class attributes b/c this is a dynamic subclass. Sorry
        if self.arg_bool and self.arg_list is not None:
            self.arg_list.append("processed")


# class SubparserA(Tap):
#     bar: int  # bar help


# class SubparserB(Tap):
#     baz: Literal["X", "Y", "Z"]  # baz help


# class ModelTapWithSubparsing(to_tap_class(Model)):
#     foo: bool = False  # foo help

#     def configure(self):
#         self.add_subparsers(help="sub-command help")
#         self.add_subparser("a", SubparserA, help="a help", description="Description (a)")
#         self.add_subparser("b", SubparserB, help="b help")


if __name__ == "__main__":
    # You don't have to subclass tap_class_from_data_model(Model) if you just want a plain argument parser:
    # ModelTap = to_tap_class(Model)
    args = ModelTap(description="Script description").parse_args()
    # args = ModelTapWithSubparsing(description="Script description").parse_args()
    print("Parsed args:")
    print(args)
    # Run the main function
    model = Model(**args.as_dict())
    main(model)


# tapify works with Model. It immediately returns a Model instance instead of a Tap class
# if __name__ == "__main__":
#     model = tapify(Model)
#     print(model)
