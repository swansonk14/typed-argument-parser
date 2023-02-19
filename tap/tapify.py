"""Tapify module, which can run a function by parsing arguments for the function from the command line."""
from inspect import signature, Parameter
from typing import Any, Callable, Optional

from tap import Tap


def tapify(function: Callable,
           args: Optional[list[str]] = None,
           known_only: bool = False,
           **func_kwargs) -> Any:
    """Runs a function by parsing arguments for the function from the command line.

    :param function: The function to run with the provided arguments.
    :param args: Arguments to parse. If None, the arguments are parsed from the command line.
    :param known_only: If true, ignores extra arguments and only parses known arguments.
                       Unparsed arguments are saved to self.extra_args.
    :param func_kwargs: Additional keyword arguments for the function. These act as default values when
                        parsing the command line arguments and overwrite the function defaults but
                        are overwritten by the parsed command line arguments.
    """
    # Get signature from function
    sig = signature(function)

    # Create a Tap object with the arguments of the function
    tap = Tap(description=function.__doc__)
    for param_name, param in sig.parameters.items():
        tap_kwargs = {}

        # Get type of the argument
        if param.annotation != Parameter.empty:
            tap._annotations[param.name] = param.annotation

        # Get the default or required of the argument
        if param.name in func_kwargs:
            tap_kwargs['default'] = func_kwargs[param.name]
            del func_kwargs[param.name]
        elif param.default != Parameter.empty:
            tap_kwargs['default'] = param.default
        else:
            tap_kwargs['required'] = True

        # Add the argument to the Tap object
        tap._add_argument(f'--{param_name}', **tap_kwargs)

    # If any func_kwargs remain, they are not used in the function, so raise an error
    if func_kwargs and not known_only:
        raise ValueError(f'Unknown keyword arguments: {func_kwargs}')

    # Parse command line arguments
    args = tap.parse_args(
        args=args,
        known_only=known_only
    )

    # Run the function with the parsed arguments
    return function(**args.as_dict())
