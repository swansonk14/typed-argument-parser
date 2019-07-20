from argparse import ArgumentParser
from copy import deepcopy
import json
from pprint import pformat
import sys
import time
from typing import Any, Dict, List, Optional, Sequence

from tap.parse_docstrings import extract_descriptions
from tap.utils import get_git_root, get_git_url, has_git, has_uncommitted_changes, type_to_str


SUPPORTED_DEFAULT_TYPES = {str, int, float, bool, List[str], List[int], List[float]}
SUPPORTED_DEFAULT_LIST_TYPES = {List[str], List[int], List[float]}


class Tap(ArgumentParser):
    """Tap is a typed argument parser that wraps argparser. """

    def __init__(self,
                 *args,
                 verbose: bool = False,
                 **kwargs):
        self.verbose = verbose
        self._parsed = False

        # Get descriptions from the doc string
        self.description, self.variable_description = extract_descriptions(self.__doc__)

        super(Tap, self).__init__(description=self.description, *args, **kwargs)

        self.add_arguments()
        self._add_remaining_arguments()

    def add_argument(self, *args, **kwargs) -> None:
        # Get variable name
        variable = self._get_optional_kwargs(*args, **kwargs)['dest']

        # Get default if not specified
        if hasattr(self, variable):
            kwargs['default'] = kwargs.get('default', getattr(self, variable))

        # Get required, type, and help if not specified
        if variable in self.__annotations__:
            var_type = self.__annotations__[variable]
            kwargs['required'] = kwargs.get('required', not hasattr(self, variable))
            kwargs['help'] = kwargs.get('help', f'({type_to_str(var_type)}) {self.variable_description[variable]}')

            # If type is not explicitly provided, try to provide a default
            if 'type' not in kwargs:
                if var_type not in SUPPORTED_DEFAULT_TYPES:
                    raise ValueError(
                        f'Variable "{variable}" has type "{var_type}" which is not supported by default.\n'
                        f'Please explicitly add the argument to the parser by writing:\n\n'
                        f'def add_arguments(self) -> None:\n'
                        f'    self.add_argument('
                        f'        "--{variable}", '
                        f'        type=func, '
                        f'        {"required=True" if kwargs["required"] else f"default={getattr(self, variable)}"}'
                        f'    )\n\n'
                        f'where "func" maps from str to {var_type}.')

                if var_type in SUPPORTED_DEFAULT_LIST_TYPES:
                    element_type = var_type.__args__[0]
                    var_type = element_type
                    kwargs['nargs'] = kwargs.get('nargs', '*')

                if var_type == bool:
                    kwargs['action'] = kwargs.get('action', f'store_{"true" if kwargs["required"] or not kwargs["default"] else "false"}')
                else:
                    kwargs['type'] = var_type

        super(Tap, self).add_argument(*args, **kwargs)

    def _add_remaining_arguments(self) -> None:
        current_arguments = {action.dest for action in self._actions}
        remaining_arguments = self.__annotations__.keys() - current_arguments

        for variable in remaining_arguments:
            self.add_argument(f'--{variable}')

    def add_arguments(self) -> None:
        """Explicitly add arguments to the parser if not using default settings."""
        pass

    def _parse_args(self,
                    args: Optional[Sequence[str]] = None,
                    namespace: Optional['Tap'] = None) -> None:
        default_namespace = super(Tap, self).parse_args(args, namespace)

        for variable, value in vars(default_namespace).items():
            # Check if variable has been defined
            if variable not in self.__annotations__:
                raise ValueError(f'Variable "{variable}" is not defined in class "{self.__class__.__name__}.')

            # Set variable (and deepcopy)
            setattr(self, variable, deepcopy(value))

    def validate_args(self) -> None:
        """Perform argument validation to ensure valid argument combinations."""
        pass

    def process_args(self) -> None:
        """Perform additional argument processing."""
        pass

    @staticmethod
    def get_reproducibility_info() -> Dict[str, str]:
        """Gets a dictionary of reproducibility information."""
        reproducibility = {
            'command_line': f'python {" ".join(sys.argv)}',
            'time': time.strftime('%c')
        }

        if has_git():
            reproducibility['git_root'] = get_git_root()
            reproducibility['git_url'] = get_git_url()
            reproducibility['git_has_uncommitted_changes'] = has_uncommitted_changes()

        return reproducibility

    def get_arg_log(self) -> Dict[str, Any]:
        """Gets all args plus reproducibility info."""
        arg_log = self.as_dict()
        arg_log['reproducibility'] = self.get_reproducibility_info()

        return arg_log

    def parse_args(self,
                   args: Optional[Sequence[str]] = None,
                   namespace: Optional['Tap'] = None) -> 'Tap':
        self._parse_args(args, namespace)
        self.validate_args()
        self.process_args()
        self._parsed = True

        return self

    def as_dict(self) -> Dict[str, Any]:
        """Return only member variables corresponding to arguments. """
        if not self._parsed:
            raise ValueError("You should call `parse_args` before retrieving arguments.")

        # Required arguments assigned to the instance
        required_args = {
            var: getattr(self, var)
            for var, val in self.__class__.__dict__.items()
            if not var.startswith('_') and not callable(val)
            }

        # Arguments that are not required must have types and not be set
        not_required_args = {
            var: getattr(self, var)
            for var, val in self.__annotations__.items()
            }

        return {**required_args, **not_required_args}

    def save(self, path: str) -> None:
        """
        Saves the arguments in JSON format.

        :param path: Path to a JSON file.
        """
        with open(path, 'w') as f:
            json.dump(self.get_arg_log(), f, indent=4, sort_keys=True)

    def __str__(self) -> str:
        """Pretty prints the arg log."""
        return pformat(self.as_dict())
