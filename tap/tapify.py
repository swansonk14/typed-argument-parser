"""Tapify module, which can initialize a class or run a function by parsing arguments from the command line."""
from inspect import signature, Parameter
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

from docstring_parser import parse

from tap import Tap
from tap.utils import type_to_str

InputType = TypeVar('InputType')
OutputType = TypeVar('OutputType')


def convert_to_tap(class_or_function: Union[Callable[[InputType], OutputType], OutputType]) -> Type[Tap]:
    """Converts a class or function into a Tap class.

    :param class_or_function: The class or function whose parameters will be converted to a Tap class.
    :return: A Tap class with arguments from the function.
    """
    # Get signature from class or function
    sig = signature(class_or_function)

    # Parse class or function docstring in one line
    if isinstance(class_or_function, type) and class_or_function.__init__.__doc__ is not None:
        doc = class_or_function.__init__.__doc__
    else:
        doc = class_or_function.__doc__

    # Parse docstring
    docstring = parse(doc)

    # Get class or function description
    description = '\n'.join(filter(None, (docstring.short_description, docstring.long_description)))

    # Add arguments of function to the Tap class
    annotations, defaults = {}, {}

    # Add arguments of class init or function to the Tap object
    for param_name, param in sig.parameters.items():
        # Skip **kwargs
        if param.kind == Parameter.VAR_KEYWORD:
            continue

        # Get type of the argument
        if param.annotation != Parameter.empty:
            # Any type defaults to str (needed for dataclasses where all non-default attributes must have a type)
            if param.annotation is Any:
                annotations[param.name] = str
            # Otherwise, get the type of the argument
            else:
                annotations[param.name] = param.annotation

        # Get the default for the argument
        if param.default != Parameter.empty:
            defaults[param_name] = param.default

    # Get docstring descriptions for parameters
    param_to_docstring = {param.arg_name: param.description for param in docstring.params}

    # Set parameter docstrings in configure
    def configure(self):
        for param_name in sig.parameters:
            req_status = f'default={defaults[param_name]}' if param_name in defaults else 'required'

            if param_name in annotations:
                help = f'({type_to_str(annotations[param_name])}, {req_status})'
            else:
                help = f'({req_status})'

            if param_name in param_to_docstring:
                help += f' {param_to_docstring[param_name]}'

            self.add_argument(f'--{param_name}', help=help)

    # Create tap class
    tap_class = type(f'{class_or_function.__name__}_tap', (Tap,), {
        '__doc__': description,
        '__annotations__': annotations,
        'configure': configure,
    } | defaults)

    return tap_class


def tapify(class_or_function: Union[Callable[[InputType], OutputType], OutputType],
           known_only: bool = False,
           command_line_args: Optional[List[str]] = None,
           **func_kwargs) -> OutputType:
    """Tapify initializes a class or runs a function by parsing arguments from the command line.

    :param class_or_function: The class or function to run with the provided arguments.
    :param known_only: If true, ignores extra arguments and only parses known arguments.
    :param command_line_args: A list of command line style arguments to parse (e.g., ['--arg', 'value']).
                              If None, arguments are parsed from the command line (default behavior).
    :param func_kwargs: Additional keyword arguments for the function. These act as default values when
                        parsing the command line arguments and overwrite the function defaults but
                        are overwritten by the parsed command line arguments.
    """
    # If any func_kwargs remain, they are not used in the function, so raise an error
    if func_kwargs and not known_only:
        raise ValueError(f'Unknown keyword arguments: {func_kwargs}')

    # Get signature from class or function
    sig = signature(class_or_function)

    # Determine if there are any **kwargs
    has_kwargs = False
    for param_name, param in sig.parameters.items():
        if param.kind == Parameter.VAR_KEYWORD:
            known_only = True
            has_kwargs = True
            break

    # Get Tap class for the class or function
    tap_class = convert_to_tap(class_or_function)

    # Instantiate tap object
    tap = tap_class()

    # Parse command line arguments
    command_line_args = tap.parse_args(
        args=command_line_args,
        known_only=known_only
    )

    # Get command line arguments as a dictionary
    command_line_args_dict = command_line_args.as_dict()

    # Get **kwargs from extra command line arguments
    if has_kwargs:
        kwargs = {
            tap.extra_args[i].lstrip('-'): tap.extra_args[i + 1]
            for i in range(0, len(tap.extra_args), 2)
        }

        command_line_args_dict.update(kwargs)

    # Initialize the class or run the function with the parsed arguments
    return class_or_function(**command_line_args_dict)
