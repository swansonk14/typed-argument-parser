"""
`tapify`: initialize a class or run a function by parsing arguments from the command line.

`to_tap_class`: convert a class or function into a `Tap` class, which can then be subclassed to add special argument
handling
"""

import dataclasses
from functools import partial
import inspect
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, TypeVar, Union

from docstring_parser import Docstring, parse
from packaging.version import Version

try:
    import pydantic
except ModuleNotFoundError:
    _IS_PYDANTIC_V1 = None
    # These are "empty" types. isinstance and issubclass will always be False
    BaseModel = type("BaseModel", (object,), {})
    _PydanticField = type("_PydanticField", (object,), {})
    _PYDANTIC_FIELD_TYPES = ()
else:
    _IS_PYDANTIC_V1 = Version(pydantic.__version__) < Version("2.0.0")
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo as PydanticFieldBaseModel
    from pydantic.dataclasses import FieldInfo as PydanticFieldDataclass

    _PydanticField = Union[PydanticFieldBaseModel, PydanticFieldDataclass]
    # typing.get_args(_PydanticField) is an empty tuple for some reason. Just repeat
    _PYDANTIC_FIELD_TYPES = (PydanticFieldBaseModel, PydanticFieldDataclass)

from tap import Tap

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")

_ClassOrFunction = Union[Callable[[InputType], OutputType], Type[OutputType]]


@dataclasses.dataclass
class _ArgData:
    """
    Data about an argument which is sufficient to inform a Tap variable/argument.
    """

    name: str

    annotation: Type
    "The type of values this argument accepts"

    is_required: bool
    "Whether or not the argument must be passed in"

    default: Any
    "Value of the argument if the argument isn't passed in. This gets ignored if `is_required`"

    description: Optional[str] = ""
    "Human-readable description of the argument"

    is_positional_only: bool = False
    "Whether or not the argument must be provided positionally"


@dataclasses.dataclass(frozen=True)
class _TapData:
    """
    Data about a class' or function's arguments which are sufficient to inform a Tap class.
    """

    args_data: List[_ArgData]
    "List of data about each argument in the class or function"

    has_kwargs: bool
    "True if you can pass variable/extra kwargs to the class or function (as in **kwargs), else False"

    known_only: bool
    "If true, ignore extra arguments and only parse known arguments"


def _is_pydantic_base_model(obj: Union[Type[Any], Any]) -> bool:
    if inspect.isclass(obj):  # issublcass requires that obj is a class
        return issubclass(obj, BaseModel)
    else:
        return isinstance(obj, BaseModel)


def _is_pydantic_dataclass(obj: Union[Type[Any], Any]) -> bool:
    if _IS_PYDANTIC_V1:
        # There's no public function in v1. This is a somewhat safe but linear check
        return dataclasses.is_dataclass(obj) and any(key.startswith("__pydantic") for key in obj.__dict__)
    else:
        return pydantic.dataclasses.is_pydantic_dataclass(obj)


def _tap_data_from_data_model(
    data_model: Any, func_kwargs: Dict[str, Any], param_to_description: Dict[str, str] = None
) -> _TapData:
    """
    Currently only works when `data_model` is a:
      - builtin dataclass (class or instance)
      - Pydantic dataclass (class or instance)
      - Pydantic BaseModel (class or instance).

    The advantage of this function over :func:`_tap_data_from_class_or_function` is that field/argument descriptions are
    extracted, b/c this function look at the fields of the data model.

    Note
    ----
    Deletes redundant keys from `func_kwargs`
    """
    param_to_description = param_to_description or {}

    def arg_data_from_dataclass(name: str, field: dataclasses.Field) -> _ArgData:
        def is_required(field: dataclasses.Field) -> bool:
            return field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING

        description = param_to_description.get(name, field.metadata.get("description"))
        return _ArgData(
            name,
            field.type,
            is_required(field),
            field.default,
            description,
        )

    def arg_data_from_pydantic(name: str, field: _PydanticField, annotation: Optional[Type] = None) -> _ArgData:
        annotation = field.annotation if annotation is None else annotation
        # Prefer the description from param_to_description (from the data model / class docstring) over the
        # field.description b/c a docstring can be modified on the fly w/o causing real issues
        description = param_to_description.get(name, field.description)
        return _ArgData(name, annotation, field.is_required(), field.default, description)

    # Determine what type of data model it is and extract fields accordingly
    if dataclasses.is_dataclass(data_model):
        name_to_field = {field.name: field for field in dataclasses.fields(data_model)}
        has_kwargs = False
        known_only = False
    elif _is_pydantic_base_model(data_model):
        name_to_field = data_model.model_fields
        # For backwards compatibility, only allow new kwargs to get assigned if the model is explicitly configured to do
        # so via extra="allow". See https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra
        is_extra_ok = data_model.model_config.get("extra", "ignore") == "allow"
        has_kwargs = is_extra_ok
        known_only = is_extra_ok
    else:
        raise TypeError(
            "data_model must be a builtin or Pydantic dataclass (instance or class) or "
            f"a Pydantic BaseModel (instance or class). Got {type(data_model)}"
        )

    # It's possible to mix fields w/ classes, e.g., use pydantic Fields in a (builtin) dataclass, or use (builtin)
    # dataclass fields in a pydantic BaseModel. It's also possible to use (builtin) dataclass fields and pydantic Fields
    # in the same data model. Therefore, the type of the data model doesn't determine the type of each field. The
    # solution is to iterate through the fields and check each type.
    args_data: List[_ArgData] = []
    for name, field in name_to_field.items():
        if isinstance(field, dataclasses.Field):
            # Idiosyncrasy: if a pydantic Field is used in a pydantic dataclass, then field.default is a FieldInfo
            # object instead of the field's default value. Furthermore, field.annotation is always NoneType. Luckily,
            # the actual type of the field is stored in field.type
            if isinstance(field.default, _PYDANTIC_FIELD_TYPES):
                arg_data = arg_data_from_pydantic(name, field.default, annotation=field.type)
            else:
                arg_data = arg_data_from_dataclass(name, field)
        elif isinstance(field, _PYDANTIC_FIELD_TYPES):
            arg_data = arg_data_from_pydantic(name, field)
        else:
            raise TypeError(f"Each field must be a dataclass or Pydantic field. Got {type(field)}")
        # Handle case where func_kwargs is supplied
        if name in func_kwargs:
            arg_data.default = func_kwargs[name]
            arg_data.is_required = False
            del func_kwargs[name]
        args_data.append(arg_data)
    return _TapData(args_data, has_kwargs, known_only)


def _tap_data_from_class_or_function(
    class_or_function: _ClassOrFunction, func_kwargs: Dict[str, Any], param_to_description: Dict[str, str]
) -> _TapData:
    """
    Extract data by inspecting the signature of `class_or_function`.

    Note
    ----
    Deletes redundant keys from `func_kwargs`
    """
    args_data: List[_ArgData] = []
    has_kwargs = False
    known_only = False

    sig = inspect.signature(class_or_function)

    for param_name, param in sig.parameters.items():
        # Skip **kwargs
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            has_kwargs = True
            known_only = True
            continue

        if param.annotation != inspect.Parameter.empty:
            annotation = param.annotation
        else:
            annotation = Any

        if param.name in func_kwargs:
            is_required = False
            default = func_kwargs[param.name]
            del func_kwargs[param.name]
        elif param.default != inspect.Parameter.empty:
            is_required = False
            default = param.default
        else:
            is_required = True
            default = inspect.Parameter.empty  # Can be set to anything. It'll be ignored

        arg_data = _ArgData(
            name=param_name,
            annotation=annotation,
            is_required=is_required,
            default=default,
            description=param_to_description.get(param.name),
            is_positional_only=param.kind == inspect.Parameter.POSITIONAL_ONLY,
        )
        args_data.append(arg_data)
    return _TapData(args_data, has_kwargs, known_only)


def _is_data_model(obj: Union[Type[Any], Any]) -> bool:
    return dataclasses.is_dataclass(obj) or _is_pydantic_base_model(obj)


def _docstring(class_or_function) -> Docstring:
    is_function = not inspect.isclass(class_or_function)
    if is_function or _is_pydantic_base_model(class_or_function):
        doc = class_or_function.__doc__
    else:
        doc = class_or_function.__init__.__doc__ or class_or_function.__doc__
    return parse(doc)


def _tap_data(class_or_function: _ClassOrFunction, param_to_description: Dict[str, str], func_kwargs) -> _TapData:
    """
    Controls how :class:`_TapData` is extracted from `class_or_function`.
    """
    is_pydantic_v1_data_model = _IS_PYDANTIC_V1 and (
        _is_pydantic_base_model(class_or_function) or _is_pydantic_dataclass(class_or_function)
    )
    if _is_data_model(class_or_function) and not is_pydantic_v1_data_model:
        # Data models from Pydantic v1 don't lend themselves well to _tap_data_from_data_model.
        # _tap_data_from_data_model looks at the data model's fields. In Pydantic v1, the field.type_ attribute stores
        # the field's annotation/type. But (in Pydantic v1) there's a bug where field.type_ is set to the inner-most
        # type of a subscripted type. For example, annotating a field with list[str] causes field.type_ to be str, not
        # list[str]. To get around this, we'll extract _TapData by looking at the signature of the data model
        return _tap_data_from_data_model(class_or_function, func_kwargs, param_to_description)
        # TODO: allow passing func_kwargs to a Pydantic BaseModel
    return _tap_data_from_class_or_function(class_or_function, func_kwargs, param_to_description)


def _tap_class(args_data: Sequence[_ArgData]) -> Type[Tap]:
    """
    Transfers argument data to a :class:`tap.Tap` class. Arguments will be added to the parser on initialization.
    """

    class ArgParser(Tap):
        # Overwriting configure would force a user to remember to call super().configure if they want to overwrite it
        # Instead, overwrite _configure
        def _configure(self):
            for arg_data in args_data:
                variable = arg_data.name
                self._annotations[variable] = str if arg_data.annotation is Any else arg_data.annotation
                self.class_variables[variable] = {"comment": arg_data.description or ""}
                if arg_data.is_required:
                    kwargs = {}
                else:
                    kwargs = dict(required=False, default=arg_data.default)
                self.add_argument(f"--{variable}", **kwargs)

            super()._configure()

    return ArgParser


def to_tap_class(class_or_function: _ClassOrFunction) -> Type[Tap]:
    """Creates a `Tap` class from `class_or_function`. This can be subclassed to add custom argument handling and
    instantiated to create a typed argument parser.

    :param class_or_function: The class or function to run with the provided arguments.
    """
    docstring = _docstring(class_or_function)
    param_to_description = {param.arg_name: param.description for param in docstring.params}
    # TODO: add func_kwargs
    tap_data = _tap_data(class_or_function, param_to_description, func_kwargs={})
    return _tap_class(tap_data.args_data)


def tapify(
    class_or_function: Union[Callable[[InputType], OutputType], Type[OutputType]],
    known_only: bool = False,
    command_line_args: Optional[List[str]] = None,
    explicit_bool: bool = False,
    description: Optional[str] = None,
    **func_kwargs,
) -> OutputType:
    """Tapify initializes a class or runs a function by parsing arguments from the command line.

    :param class_or_function: The class or function to run with the provided arguments.
    :param known_only: If true, ignores extra arguments and only parses known arguments.
    :param command_line_args: A list of command line style arguments to parse (e.g., `['--arg', 'value']`). If None,
                              arguments are parsed from the command line (default behavior).
    :param explicit_bool: Booleans can be specified on the command line as `--arg True` or `--arg False` rather than
                          `--arg`. Additionally, booleans can be specified by prefixes of True and False with any
                          capitalization as well as 1 or 0.
    :param description: The description displayed in the help message—the same description passed in
                        `argparse.ArgumentParser(description=...)`. By default, it's extracted from `class_or_function`'s
                        docstring.
    :param func_kwargs: Additional keyword arguments for the function. These act as default values when parsing the
                        command line arguments and overwrite the function defaults but are overwritten by the parsed
                        command line arguments.
    """
    # We don't directly call to_tap_class b/c we need tap_data, not just tap_class
    docstring = _docstring(class_or_function)
    param_to_description = {param.arg_name: param.description for param in docstring.params}
    tap_data = _tap_data(class_or_function, param_to_description, func_kwargs)
    tap_class = _tap_class(tap_data.args_data)
    # Create a Tap object
    if description is None:
        description = "\n".join(filter(None, (docstring.short_description, docstring.long_description)))
    tap = tap_class(description=description, explicit_bool=explicit_bool)

    # If any func_kwargs remain, they are not used in the function, so raise an error
    known_only = known_only or tap_data.known_only
    if func_kwargs and not known_only:
        raise ValueError(f"Unknown keyword arguments: {func_kwargs}")

    # Parse command line arguments
    command_line_args: Tap = tap.parse_args(args=command_line_args, known_only=known_only)

    # Prepare command line arguments for class_or_function, respecting positional-only args
    class_or_function_args: list[Any] = []
    class_or_function_kwargs: Dict[str, Any] = {}
    command_line_args_dict = command_line_args.as_dict()
    for arg_data in tap_data.args_data:
        arg_value = command_line_args_dict[arg_data.name]
        if arg_data.is_positional_only:
            class_or_function_args.append(arg_value)
        else:
            class_or_function_kwargs[arg_data.name] = arg_value

    # Get **kwargs from extra command line arguments
    if tap_data.has_kwargs:
        kwargs = {tap.extra_args[i].lstrip("-"): tap.extra_args[i + 1] for i in range(0, len(tap.extra_args), 2)}
        class_or_function_kwargs.update(kwargs)

    # Initialize the class or run the function with the parsed arguments
    return class_or_function(*class_or_function_args, **class_or_function_kwargs)


def tapify_with_subparsers(class_: Type):
    # Create a Tap class with subparsers defined by the class_'s methods
    docstring = _docstring(class_)
    param_to_description = {param.arg_name: param.description for param in docstring.params}
    args_data = _tap_data(class_, param_to_description, func_kwargs={}).args_data

    subparser_dest = "_tap_subparser_dest"

    class TapWithSubparsers(_tap_class(args_data)):
        def configure(self):  # TODO: understand why overriding _configure is wrong
            self.add_subparsers(
                help="sub-command help",  # TODO: prolly should be user-inputted instead
                required=True,  # If not required just use tapify
                dest=subparser_dest,  # Need to know which subparser (i.e., which method) is being hit by the CLI
            )
            for method_name in dir(class_):
                method = getattr(class_, method_name)
                if method_name.startswith("_") or not callable(method):
                    # TODO: maybe the user can input their own function (method_name: str -> bool) for deciding whether
                    # or not a method_name should be included as a subparser or not.
                    continue
                subparser_tap = to_tap_class(partial(method, None))
                # TODO: the partial part is a stupid fix for getting rid of self. Need to also handle static and class
                # methods
                self.add_subparser(
                    method_name,
                    subparser_tap,
                    help=f"{method_name} help",  # TODO: think about how to set
                    description=f"{method_name} description",  # TODO: think about how to set
                )

    # Parse the user's command
    cli_args = TapWithSubparsers().parse_args()

    # TODO: think about how to avoid name collisions b/t the init and method args / avoid loading everything into as_dict

    # Create the class_ object
    # TODO: maybe figure out how to not do this step so that the input class_ can be a module or any collection of things
    # where calling dir on it gives a bunch of functions
    args_for_init = {arg_data.name for arg_data in args_data}
    # TODO: handle args and kwargs like we did for tapify
    init_kwargs = {name: value for name, value in cli_args.as_dict().items() if name in args_for_init}
    object_ = class_(**init_kwargs)

    # Call the method
    method = getattr(object_, getattr(cli_args, subparser_dest))
    # TODO: handle args and kwargs like we did for tapify
    method_kwargs = {name: value for name, value in cli_args.as_dict().items() if name not in args_for_init}
    return method(**method_kwargs)  # TODO: also return the object?
