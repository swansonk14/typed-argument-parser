"""
Example:

python demo_data_model.py \
--arg_str test \
--arg_list x y z \
--arg_bool \
-arg 2
"""
from pydantic import BaseModel, Field
from tap import tapify, convert_to_tap_class


class Model(BaseModel):
    """
    My Pydantic Model which contains script args.
    """

    arg_str: str = Field(description="hello")
    arg_bool: bool = Field(default=True, description=None)
    arg_list: list[str] | None = Field(default=None, description="optional list")


def main(model: Model) -> None:
    print("Parsed args into Model:")
    print(model)


def to_number(string: str) -> float | int:
    return float(string) if "." in string else int(string)


class ModelTap(convert_to_tap_class(Model)):
    # You can supply additional arguments here
    argument_with_really_long_name: float | int = 3
    "This argument has a long name and will be aliased with a short one"

    def configure(self) -> None:
        # You can still add special argument behavior
        self.add_argument("-arg", "--argument_with_really_long_name", type=to_number)

    def process_args(self) -> None:
        # You can still validate and modify arguments
        # (You should do this in the Pydantic Model. I'm just demonstrating that this functionality is still possible)
        if self.argument_with_really_long_name > 4:
            raise ValueError("nope")

        # No auto-complete (and other niceties) for the super class attributes b/c this is a dynamic subclass. Sorry
        if self.arg_bool:
            self.arg_str += " processed"


if __name__ == "__main__":
    # You don't have to subclass tap_class_from_data_model(Model) if you just want a plain argument parser:
    # ModelTap = tap_class_from_data_model(Model)
    args = ModelTap(description="Script description").parse_args()
    print("Parsed args:")
    print(args)
    # Run the main function. Pydantic BaseModels ignore arguments which aren't one of their fields instead of raising an
    # error
    model = Model(**args.as_dict())
    main(model)


# This works but doesn't show the field description, and immediately returns a Model instance instead of a Tap class
# if __name__ == "__main__":
#     model = tapify(Model)
#     print(model)
