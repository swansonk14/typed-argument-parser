from argparse import ArgumentParser
from copy import deepcopy
import json
from pprint import pformat
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Set

from tap.parse_docstrings import extract_descriptions
from tap.utils import get_dest, get_git_root, get_git_url, has_git, has_uncommitted_changes, is_option_arg, type_to_str


SUPPORTED_DEFAULT_TYPES = {str, int, float, bool, List[str], List[int], List[float]}
SUPPORTED_DEFAULT_LIST_TYPES = {List[str], List[int], List[float]}


class Tap(ArgumentParser):
    """Tap is a typed argument parser that wraps Python's built-in ArgumentParser."""

    def __init__(self, *args, **kwargs):
        """Initializes the Tap instance.

        :param args: Arguments passed to the super class ArgumentParser.
        :param kwargs: Keyword arguments passed to the super class ArgumentParser.
        """
        # Whether the arguments have been parsed (i.e. if parse_args has been called)
        self._parsed = False

        # Get descriptions of the arguments from the doc string
        self.description, self.variable_description, self.parse_error = extract_descriptions(self.__doc__)

        # Get annotations from self and all super classes up through tap
        self._annotations = self._get_annotations()

        # Initialize the super class, i.e. ArgumentParser
        super(Tap, self).__init__(description=self.description, *args, **kwargs)

        # Add arguments to self
        self.add_arguments()
        self._add_remaining_arguments()

    def add_argument(self, *name_or_flags, **kwargs) -> None:
        """Adds an argument to self (i.e. the super class ArgumentParser).

        Sets the following attributes of kwargs when not explicitly provided:
        - type: Set to the type annotation of the argument.
        - default: Set to the default value of the argument (if provided).
        - required: True if a default value of the argument is not provided, False otherwise.
        - action: Set to "store_true" if the argument is a required bool or a bool with default value False.
                  Set to "store_false" if the argument is a bool with default value True.
        - nargs: Set to "*" if the type annotation is List[str], List[int], or List[float].
        - help: Set to the argument documentation from the class docstring.

        :param name_or_flags: Either a name or a list of option strings, e.g. foo or -f, --foo.
        :param kwargs: Keyword arguments.
        """
        # Get variable name
        variable = get_dest(*name_or_flags, **kwargs)

        # Get default if not specified
        if hasattr(self, variable):
            kwargs['default'] = kwargs.get('default', getattr(self, variable))

        # Set other kwargs where not provided
        if variable in self._annotations:
            # Get type annotation
            var_type = self._annotations[variable]

            # Set required if option arg
            if is_option_arg(*name_or_flags):
                kwargs['required'] = kwargs.get('required', not hasattr(self, variable))

            # Set help
            kwargs['help'] = kwargs.get('help', f'({type_to_str(var_type)}) {self.variable_description.get(variable)}')

            # If type is not explicitly provided, set it if it's one of our supported default types
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

                # If List type, set type of elements in list and nargs
                if var_type in SUPPORTED_DEFAULT_LIST_TYPES:
                    element_type = var_type.__args__[0]
                    var_type = element_type
                    kwargs['nargs'] = kwargs.get('nargs', '*')

                # If bool then set action, otherwise set type
                if var_type == bool:
                    kwargs['action'] = kwargs.get('action', f'store_{"true" if kwargs["required"] or not kwargs["default"] else "false"}')
                else:
                    kwargs['type'] = var_type

        super(Tap, self).add_argument(*name_or_flags, **kwargs)

    def _add_remaining_arguments(self) -> None:
        """Adds any arguments not explicitly added in add_arguments.

        Uses the name, type annotation, and default provided in the definition
        of the argument. If no default is provided, the argument is required.
        """
        added_arguments = {action.dest for action in self._actions}
        remaining_arguments = self._get_argument_names() - added_arguments

        for variable in sorted(remaining_arguments):
            self.add_argument(f'--{variable}')

            # Variables without documentation provided have a help value of None
            if variable not in self.variable_description:
                self.variable_description[variable] = ''

    def add_arguments(self) -> None:
        """Explicitly add arguments to the parser if not using default settings."""
        pass

    def _parse_args(self,
                    args: Optional[Sequence[str]] = None,
                    namespace: Optional['Tap'] = None) -> None:
        """Parses arguments and sets attributes of self equal to the parsed arguments.

        :param args: List of strings to parse. The default is taken from sys.argv.
        TODO: should we support providing a namespace?
        """
        # Parse args using super class ArgumentParser's parse_args function
        default_namespace = super(Tap, self).parse_args(args, namespace)

        # Set variables (and deepcopy to avoid modifying the class variable)
        for variable, value in vars(default_namespace).items():
            setattr(self, variable, deepcopy(value))

    def process_args(self) -> None:
        """Perform additional argument processing and/or validation."""
        pass

    @staticmethod
    def get_reproducibility_info() -> Dict[str, str]:
        """Gets a dictionary of reproducibility information.

        Reproducibility information always includes:
        - command_line: The command line command used to execute the code.
        - time: The current time.

        If git is installed, reproducibility information also includes:
        - git_root: The root of the git repo where the command is run.
        - git_url: The url of the current hash of the git repo where the command is run.
                   Ex. https://github.com/kswanson-asapp/rationale-alignment/tree/<hash>
        - git_has_uncommitted_changes: Whether the current git repo has uncommitted changes.

        :return: A dictionary of reproducibility information.
        """
        reproducibility = {
            'command_line': f'python {" ".join(sys.argv)}',
            'time': time.strftime('%c')
        }

        if has_git():
            reproducibility['git_root'] = get_git_root()
            reproducibility['git_url'] = get_git_url(commit_hash=True)
            reproducibility['git_has_uncommitted_changes'] = has_uncommitted_changes()

        return reproducibility

    def _log_all(self) -> Dict[str, Any]:
        """Gets all arguments along with reproducibility information.

        :return: A dictionary containing all arguments along with reproducibility information.
        """
        arg_log = self.as_dict()
        arg_log['reproducibility'] = self.get_reproducibility_info()

        return arg_log

    def parse_args(self,
                   args: Optional[Sequence[str]] = None,
                   namespace: Optional['Tap'] = None) -> 'Tap':
        """Parses arguments, sets attributes of self equal to the parsed arguments, and processes arguments.

        :param args: List of strings to parse. The default is taken from `sys.argv`.
        TODO: should we support providing a namespace?
        :return: self, which is a Tap instance containing all of the parsed args.
        """
        self._parse_args(args, namespace)
        self.process_args()
        self._parsed = True

        return self

    @classmethod
    def _get_from_self_and_super(cls, key: str) -> Dict[str, Any]:
        """Returns a dictionary mapping variable names to values.

        Variables and values are extracted from classes using key starting
        with this class and traversing up through the super classes up through Tap.

        If super class and sub class have the same key, the sub class value is used.

        :param key: The key to extract from all classes. Must return a dictionary.
        :return: A dictionary mapping variable names to values from the class dict.
        """
        visited = set()
        super_classes = [cls]
        dictionary = dict()

        while len(super_classes) > 0:
            super_class = super_classes.pop(0)

            if super_class not in visited and issubclass(super_class, Tap):
                super_dictionary = dict(getattr(super_class, key, dict()))

                # Update only unseen variables to avoid overriding subclass type annotations
                for variable in super_dictionary.keys() - dictionary.keys():
                    dictionary[variable] = super_dictionary[variable]

                super_classes += list(super_class.__bases__)
                visited.add(super_class)

        return dictionary

    def _get_class_dict(self) -> Dict[str, Any]:
        """Returns a dictionary mapping class variable names to values from the class dict."""
        class_dict = self._get_from_self_and_super(key='__dict__')
        class_dict = {var: val for var, val in class_dict.items() if not var.startswith('_') and not callable(val)}

        return class_dict

    def _get_annotations(self) -> Dict[str, Any]:
        """Returns a dictionary mapping variable names to their type annotations."""
        return self._get_from_self_and_super(key='__annotations__')

    def _get_argument_names(self) -> Set[str]:
        """Returns a list of variable names corresponding to the arguments."""
        return set(self._get_class_dict().keys()) | set(self._annotations.keys())

    def as_dict(self) -> Dict[str, Any]:
        """Returns the member variables corresponding to the class variable arguments.

         :return: A dictionary mapping each argument's name to its value.
         """
        if not self._parsed:
            raise ValueError('You should call `parse_args` before retrieving arguments.')

        return {var: getattr(self, var) for var in self._get_argument_names()}

    def save(self, path: str) -> None:
        """Saves the arguments and reproducibility information in JSON format.

        :param path: Path to the JSON file where the arguments will be saved.
        """
        with open(path, 'w') as f:
            json.dump(self._log_all(), f, indent=4, sort_keys=True)

    def __str__(self) -> str:
        """Returns a string representation of self.

        :return: A formatted string representation of the dictionary of all arguments.
        """
        return pformat(self.as_dict())
