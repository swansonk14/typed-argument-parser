from argparse import ArgumentParser
from copy import deepcopy
import json
import sys
import time
from typing import Any, Dict, Optional, Sequence

from typed_argument_parsing.parse_docstrings import extract_descriptions
from typed_argument_parsing.utils import get_git_hash, get_git_root


class TypedArgumentParser(ArgumentParser):

    def __init__(self,
                 *args,
                 verbose: bool = False,
                 **kwargs):
        self.verbose = verbose

        # Get descriptions from the doc string
        self.description, self.variable_description = extract_descriptions(self.__doc__)

        super(TypedArgumentParser, self).__init__(description=self.description, *args, **kwargs)

        self.add_arguments()
        self._add_remaining_arguments()

    def add_argument(self, *args, **kwargs) -> None:
        # Get variable name
        variable = self._get_optional_kwargs(*args, **kwargs)['dest']

        # Get type and help if not specified
        if variable in self.__annotations__:
            annotation = self.__annotations__[variable]
            kwargs['type'] = kwargs.get('type', annotation)
            kwargs['help'] = kwargs.get('help', f'({annotation.__name__}) {self.variable_description[variable]}')

        # Get default if not specified
        if hasattr(self, variable):
            kwargs['default'] = kwargs.get('default', getattr(self, variable))

        super(TypedArgumentParser, self).add_argument(*args, **kwargs)

    def _add_remaining_arguments(self) -> None:
        current_arguments = {action.dest for action in self._actions}

        for variable in self.__annotations__.keys():
            if variable not in current_arguments:
                required = not hasattr(self, variable)
                self.add_argument(f'--{variable}', required=required)

    def add_arguments(self) -> None:
        """Explicitly add arguments to the parser if not using default settings."""
        pass

    def _parse_args(self,
                    args: Optional[Sequence[str]] = None,
                    namespace: Optional['TypedArgumentParser'] = None) -> None:
        default_namespace = super(TypedArgumentParser, self).parse_args(args, namespace)

        for variable, value in vars(default_namespace).items():
            # Check if variable has been defined
            if variable not in self.__annotations__:
                raise ValueError(f'Variable "{variable}" is not defined in class "{self.__class__.__name__}.')

            # Ensure the variable is of the right type
            variable_type, arg_type = self.__annotations__[variable], type(value)
            if variable_type != arg_type:
                raise ValueError(f'Variable "{variable}" of type "{arg_type}" does not match annotation type '
                                 f'"{variable_type}" for class "{self.__class__.__name__}".')

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
        return {
            'git_root': get_git_root(),
            'git_url': f'https://github.com/kswanson-asapp/rationale-alignment/tree/{get_git_hash()}',
            'command_line': f'python {" ".join(sys.argv)}',
            'time': time.strftime('%c')
        }

    def parse_args(self,
                   args: Optional[Sequence[str]] = None,
                   namespace: Optional['TypedArgumentParser'] = None) -> 'TypedArgumentParser':
        self._parse_args(args, namespace)
        self.validate_args()
        self.process_args()

        return self

    def as_dict(self) -> Dict[str, Any]:
        """ Return only the member variables, which correspond to the  """
        # Build a dictionary of results
        class_dict = self.__class__.__dict__.items()

        return {var: val for var, val in class_dict if not var.startswith('_') and not callable(val)}

    def save(self, path: str) -> None:
        """
        Saves the arguments in JSON format.

        :param path: Path to a JSON file.
        """
        args = self.as_dict()
        args['reproducibility'] = self.get_reproducibility_info()

        with open(path, 'w') as f:
            json.dump(args, f, indent=4, sort_keys=True)
