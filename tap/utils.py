from argparse import ArgumentParser, ArgumentTypeError
from base64 import b64encode, b64decode
from collections import OrderedDict
import copy
from functools import wraps
import inspect
from io import StringIO
from json import JSONEncoder
import os
import pickle
import re
import subprocess
import sys
import tokenize
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)
from typing_extensions import Literal
from typing_inspect import get_args, get_origin as typing_inspect_get_origin


NO_CHANGES_STATUS = """nothing to commit, working tree clean"""
PRIMITIVES = (str, int, float, bool)


def check_output(command: List[str], suppress_stderr: bool = True) -> str:
    """Runs subprocess.check_output and returns the result as a string.

    :param command: A list of strings representing the command to run on the command line.
    :param suppress_stderr: Whether to suppress anything written to standard error.
    :return: The output of the command, converted from bytes to string and stripped.
    """
    with open(os.devnull, 'w') as devnull:
        devnull = devnull if suppress_stderr else None
        output = subprocess.check_output(command, stderr=devnull).decode('utf-8').strip()
    return output


def has_git() -> bool:
    """Returns whether git is installed.

    :return: True if git is installed, False otherwise.
    """
    try:
        output = check_output(['git', 'rev-parse', '--is-inside-work-tree'])
        return output == 'true'
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def get_git_root() -> str:
    """Gets the root directory of the git repo where the command is run.

    :return: The root directory of the current git repo.
    """
    return check_output(['git', 'rev-parse', '--show-toplevel'])


def get_git_url(commit_hash: bool = True) -> str:
    """Gets the https url of the git repo where the command is run.

    :param commit_hash: If True, the url links to the latest local git commit hash.
    If False, the url links to the general git url.
    :return: The https url of the current git repo.
    """
    # Get git url (either https or ssh)
    try:
        url = check_output(['git', 'remote', 'get-url', 'origin'])
    except subprocess.CalledProcessError:
        # For git versions <2.0
        url = check_output(['git', 'config', '--get', 'remote.origin.url'])

    # Remove .git at end
    url = url[:-len('.git')]

    # Convert ssh url to https url
    m = re.search('git@(.+):', url)
    if m is not None:
        domain = m.group(1)
        path = url[m.span()[1]:]
        url = f'https://{domain}/{path}'

    if commit_hash:
        # Add tree and hash of current commit
        url = f'{url}/tree/{get_git_hash()}'

    return url


def get_git_hash() -> str:
    """Gets the git hash of HEAD of the git repo where the command is run.

    :return: The git hash of HEAD of the current git repo.
    """
    return check_output(['git', 'rev-parse', 'HEAD'])


def has_uncommitted_changes() -> bool:
    """Returns whether there are uncommitted changes in the git repo where the command is run.

    :return: True if there are uncommitted changes in the current git repo, False otherwise.
    """
    status = check_output(['git', 'status'])

    return not status.endswith(NO_CHANGES_STATUS)


def type_to_str(type_annotation: Union[type, Any]) -> str:
    """Gets a string representation of the provided type.

    :param type_annotation: A type annotation, which is either a built-in type or a typing type.
    :return: A string representation of the type annotation.
    """
    # Built-in type
    if type(type_annotation) == type:
        return type_annotation.__name__

    # Typing type
    return str(type_annotation).replace('typing.', '')


def get_argument_name(*name_or_flags) -> str:
    """Gets the name of the argument.

    :param name_or_flags: Either a name or a list of option strings, e.g. foo or -f, --foo.
    :return: The name of the argument (extracted from name_or_flags).
    """
    if '-h' in name_or_flags or '--help' in name_or_flags:
        return 'help'

    if len(name_or_flags) > 1:
        name_or_flags = [n_or_f for n_or_f in name_or_flags if n_or_f.startswith('--')]

    if len(name_or_flags) != 1:
        raise ValueError(f'There should only be a single canonical name for argument {name_or_flags}!')

    return name_or_flags[0].lstrip('-')


def get_dest(*name_or_flags, **kwargs) -> str:
    """Gets the name of the destination of the argument.

    :param name_or_flags: Either a name or a list of option strings, e.g. foo or -f, --foo.
    :param kwargs: Keyword arguments.
    :return: The name of the argument (extracted from name_or_flags).
    """
    if '-h' in name_or_flags or '--help' in name_or_flags:
        return 'help'

    return ArgumentParser().add_argument(*name_or_flags, **kwargs).dest


def is_option_arg(*name_or_flags) -> bool:
    """Returns whether the argument is an option arg (as opposed to a positional arg).

    :param name_or_flags: Either a name or a list of option strings, e.g. foo or -f, --foo.
    :return: True if the argument is an option arg, False otherwise.
    """
    return any(name_or_flag.startswith('-') for name_or_flag in name_or_flags)


def tokenize_source(obj: object) -> Generator:
    """Returns a generator for the tokens of the object's source code."""
    source = inspect.getsource(obj)
    token_generator = tokenize.generate_tokens(StringIO(source).readline)

    return token_generator


def get_class_column(obj: type) -> int:
    """Determines the column number for class variables in a class."""
    for token_type, token, (start_line, start_column), (end_line, end_column), line in tokenize_source(obj):
        if start_line == 1 or token.strip() == '':
            continue

        return start_column


def source_line_to_tokens(obj: object) -> Dict[int, List[Dict[str, Union[str, int]]]]:
    """Gets a dictionary mapping from line number to a dictionary of tokens on that line for an object's source code."""
    line_to_tokens = {}
    for token_type, token, (start_line, start_column), (end_line, end_column), line in tokenize_source(obj):
        line_to_tokens.setdefault(start_line, []).append({
            'token_type': token_type,
            'token': token,
            'start_line': start_line,
            'start_column': start_column,
            'end_line': end_line,
            'end_column': end_column,
            'line': line
        })

    return line_to_tokens


def get_class_variables(cls: type) -> OrderedDict:
    """Returns an OrderedDict mapping class variables to their additional information (currently just comments)."""
    # Get mapping from line number to tokens
    line_to_tokens = source_line_to_tokens(cls)

    # Get class variable column number
    class_variable_column = get_class_column(cls)

    # Extract class variables
    class_variable = None
    variable_to_comment = OrderedDict()
    for tokens in line_to_tokens.values():
        for i, token in enumerate(tokens):

            # Skip whitespace
            if token['token'].strip() == '':
                continue

            # Extract multiline comments
            if (class_variable is not None
                    and token['token_type'] == tokenize.STRING
                    and token['token'][:3] in {'"""', "'''"}):
                sep = ' ' if variable_to_comment[class_variable]['comment'] else ''
                variable_to_comment[class_variable]['comment'] += sep + token['token'][3:-3].strip()

            # Match class variable
            class_variable = None
            if (token['token_type'] == tokenize.NAME and
                    token['start_column'] == class_variable_column and
                    len(tokens) > i and
                    tokens[i + 1]['token'] in ['=', ':']):

                class_variable = token['token']
                variable_to_comment[class_variable] = {'comment': ''}

                # Find the comment (if it exists)
                for j in range(i + 1, len(tokens)):
                    if tokens[j]['token_type'] == tokenize.COMMENT:
                        # Leave out "#" and whitespace from comment
                        variable_to_comment[class_variable]['comment'] = tokens[j]['token'][1:].strip()
                        break

            break

    return variable_to_comment


def get_literals(literal: Literal, variable: str) -> Tuple[Callable[[str], Any], List[str]]:
    """Extracts the values from a Literal type and ensures that the values are all primitive types."""
    literals = list(get_args(literal))

    if not all(isinstance(literal, PRIMITIVES) for literal in literals):
        raise ValueError(
            f'The type for variable "{variable}" contains a literal'
            f'of a non-primitive type e.g. (str, int, float, bool).\n'
            f'Currently only primitive-typed literals are supported.'
        )

    str_to_literal = {str(literal): literal for literal in literals}

    if len(literals) != len(str_to_literal):
        raise ValueError('All literals must have unique string representations')

    def var_type(arg: str) -> Any:
        return str_to_literal.get(arg, arg)

    return var_type, literals


def boolean_type(flag_value: str) -> bool:
    """Convert a string to a boolean if it is a prefix of 'True' or 'False' (case insensitive) or is '1' or '0'."""
    if 'true'.startswith(flag_value.lower()) or flag_value == '1':
        return True
    if 'false'.startswith(flag_value.lower()) or flag_value == '0':
        return False
    raise ArgumentTypeError('Value has to be a prefix of "True" or "False" (case insensitive) or "1" or "0".')


class TupleTypeEnforcer:
    """The type argument to argparse for checking and applying types to Tuples."""
    def __init__(self, types: List[type], loop: bool = False):
        self.types = [boolean_type if t == bool else t for t in types]
        self.loop = loop
        self.index = 0

    def __call__(self, arg: str) -> Any:
        arg = self.types[self.index](arg)
        self.index += 1

        if self.loop:
            self.index %= len(self.types)

        return arg


class MockTuple:
    """Mock of a tuple needed to prevent JSON encoding tuples as lists."""
    def __init__(self, _tuple: tuple) -> None:
        self.tuple = _tuple


def _nested_replace_type(obj: Any, find_type: type, replace_type: type) -> Any:
    """Replaces any instance (including instances within lists, tuple, dict) of find_type with an instance of replace_type.

    Note: Tuples, lists, and dicts are NOT modified in place.
    Note: Does NOT do a nested search through objects besides tuples, lists, and dicts (e.g. sets).

    :param obj: The object to modify by replacing find_type instances with replace_type instances.
    :param find_type: The type to find in obj.
    :param replace_type: The type to used to replace find_type in obj.
    :return: A version of obj with all instances of find_type replaced by replace_type
    """
    if isinstance(obj, tuple):
        obj = tuple(_nested_replace_type(item, find_type, replace_type) for item in obj)

    elif isinstance(obj, list):
        obj = [_nested_replace_type(item, find_type, replace_type) for item in obj]

    elif isinstance(obj, dict):
        obj = {
            _nested_replace_type(key, find_type, replace_type): _nested_replace_type(value, find_type, replace_type)
            for key, value in obj.items()
        }

    if isinstance(obj, find_type):
        obj = replace_type(obj)

    return obj


def define_python_object_encoder(skip_unpicklable: bool = False) -> 'PythonObjectEncoder':  # noqa F821

    class PythonObjectEncoder(JSONEncoder):
        """Stores parameters that are not JSON serializable as pickle dumps.

        See: https://stackoverflow.com/a/36252257
        """
        def iterencode(self, o: Any, _one_shot: bool = False) -> Iterator[str]:
            o = _nested_replace_type(o, tuple, MockTuple)
            return super(PythonObjectEncoder, self).iterencode(o, _one_shot)

        def default(self, obj: Any) -> Any:
            if isinstance(obj, set):
                return {
                    '_type': 'set',
                    '_value': list(obj)
                }
            elif isinstance(obj, MockTuple):
                return {
                    '_type': 'tuple',
                    '_value': list(obj.tuple)
                }

            try:
                return {
                    '_type': f'python_object (type = {obj.__class__.__name__})',
                    '_value': b64encode(pickle.dumps(obj)).decode('utf-8')
                }
            except (pickle.PicklingError, TypeError, AttributeError) as e:
                if not skip_unpicklable:
                    raise ValueError(f'Could not pickle this object: Failed with exception {e}\n'
                                     f'If you would like to ignore unpicklable attributes set '
                                     f'skip_unpickleable = True in save.')
                else:
                    return {
                        '_type': f'unpicklable_object {obj.__class__.__name__}',
                        '_value': None
                    }

    return PythonObjectEncoder


class UnpicklableObject:
    """A class that serves as a placeholder for an object that could not be pickled. """

    def __eq__(self, other):
        return isinstance(other, UnpicklableObject)


def as_python_object(dct: Any) -> Any:
    """The hooks that allow a parameter that is not JSON serializable to be loaded.

    See: https://stackoverflow.com/a/36252257
    """
    if '_type' in dct and '_value' in dct:
        _type, value = dct['_type'], dct['_value']

        if _type == 'tuple':
            return tuple(value)

        elif _type == 'set':
            return set(value)

        elif _type.startswith('python_object'):
            return pickle.loads(b64decode(value.encode('utf-8')))

        elif _type.startswith('unpicklable_object'):
            return UnpicklableObject()

        else:
            raise ValueError(f'Special type "{_type}" not supported for JSON loading.')

    return dct


def fix_py36_copy(func: Callable) -> Callable:
    """Decorator that fixes functions using Python 3.6 deepcopy of ArgumentParsers.

    Based on https://stackoverflow.com/questions/6279305/typeerror-cannot-deepcopy-this-pattern-object
    """
    if sys.version_info[:2] > (3, 6):
        return func

    @wraps(func)
    def wrapper(*args, **kwargs):
        re_type = type(re.compile(''))
        has_prev_val = re_type in copy._deepcopy_dispatch
        prev_val = copy._deepcopy_dispatch.get(re_type, None)
        copy._deepcopy_dispatch[type(re.compile(''))] = lambda r, _: r

        result = func(*args, **kwargs)

        if has_prev_val:
            copy._deepcopy_dispatch[re_type] = prev_val
        else:
            del copy._deepcopy_dispatch[re_type]

        return result

    return wrapper


def enforce_reproducibility(saved_reproducibility_data: Optional[Dict[str, str]],
                            current_reproducibility_data: Dict[str, str],
                            path: str) -> None:
    """Checks if reproducibility has failed and raises the appropriate error.

    :param saved_reproducibility_data: Reproducibility information loaded from a saved file.
    :param current_reproducibility_data: Reproducibility information from the current object.
    :param path: The path name of the file that is being loaded.
    """
    no_reproducibility_message = 'Reproducibility not guaranteed'

    if saved_reproducibility_data is None:
        raise ValueError(f'{no_reproducibility_message}: Could not find reproducibility '
                         f'information in args loaded from "{path}".')

    if 'git_url' not in saved_reproducibility_data:
        raise ValueError(f'{no_reproducibility_message}: Could not find '
                         f'git url in args loaded from "{path}".')

    if 'git_url' not in current_reproducibility_data:
        raise ValueError(f'{no_reproducibility_message}: Could not find '
                         f'git url in current args.')

    if saved_reproducibility_data['git_url'] != current_reproducibility_data['git_url']:
        raise ValueError(f'{no_reproducibility_message}: Differing git url/hash '
                         f'between current args and args loaded from "{path}".')

    if saved_reproducibility_data['git_has_uncommitted_changes']:
        raise ValueError(f'{no_reproducibility_message}: Uncommitted changes '
                         f'in args loaded from "{path}".')

    if current_reproducibility_data['git_has_uncommitted_changes']:
        raise ValueError(f'{no_reproducibility_message}: Uncommitted changes '
                         f'in current args.')


# TODO: remove this once typing_inspect.get_origin is fixed for Python 3.8 and 3.9
# https://github.com/ilevkivskyi/typing_inspect/issues/64
# https://github.com/ilevkivskyi/typing_inspect/issues/65
def get_origin(tp: Any) -> Any:
    """Same as typing_inspect.get_origin but fixes unparameterized generic types like Set."""
    origin = typing_inspect_get_origin(tp)

    if origin is None:
        origin = tp

    return origin
