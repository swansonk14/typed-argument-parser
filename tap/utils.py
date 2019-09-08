from argparse import ArgumentParser
from collections import OrderedDict
import inspect
from io import StringIO
import os
import re
import subprocess
import tokenize
from typing import Any, Dict, Generator, List, Union


NO_CHANGES_STATUS = """nothing to commit, working tree clean"""


def check_output(command: List[str]) -> str:
    """Runs subprocess.check_output and returns the result as a string.

    :param command: A list of strings representing the command to run on the command line.
    :return: The output of the command, converted from bytes to string and stripped.
    """
    return subprocess.check_output(command).decode('utf-8').strip()


def has_git() -> bool:
    """Returns whether git is installed.

    :return: True if git is installed, False otherwise.
    """
    try:
        subprocess.check_output(['git', '--version'])
        return True
    except FileNotFoundError:
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
    url = check_output(['git', 'remote', 'get-url', 'origin'])

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
        url = os.path.join(url, 'tree', get_git_hash())

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


def get_dest(*name_or_flags, **kwargs) -> str:
    """Gets the name of the destination of the argument.

    :param name_or_flags: Either a name or a list of option strings, e.g. foo or -f, --foo.
    :param kwargs: Keyword arguments.
    :return: The name of the argument (extracted from name_or_flags)
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
    variable_to_comment = OrderedDict()
    for tokens in line_to_tokens.values():
        for i, token in enumerate(tokens):

            # Skip whitespace
            if token['token'].strip() == '':
                continue

            # Match class variable
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
