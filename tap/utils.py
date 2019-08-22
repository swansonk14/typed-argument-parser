from argparse import ArgumentParser
import inspect
from io import StringIO
import os
import subprocess
import tokenize
from typing import Any, Dict, List, Union


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

    # Check to ensure url starts and ends as expected for https and ssh
    assert url.startswith('https://github.com') or url.startswith('git@github.com')
    assert url.endswith('.git')

    # Remove .git at end
    url = url[:-len('.git')]

    # Convert ssh url to https url
    if url.startswith('git@github.com:'):
        url = url[len('git@github.com:'):]
        url = f'https://github.com/{url}'

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


def extract_class_variable_to_comment_mapping(cls: type) -> Dict[str, str]:
    """Returns a dictionary mapping from class variables their single line comments on the same line."""
    # Get source code for the class
    class_source_code = inspect.getsource(cls)

    # Determine indentation
    first_line = class_source_code.split('\n')[0]
    indent = len(first_line) - len(first_line.lstrip())

    # Get mapping from line number to tokens
    line_to_tokens = {}
    for token_type, token, (start_line, start_column), (end_line, end_column), line in tokenize.generate_tokens(StringIO(class_source_code).readline):
        line_to_tokens.setdefault(start_line, []).append({
            'token_type': token_type,
            'token': token,
            'start_line': start_line,
            'start_column': start_column,
            'end_line': end_line,
            'end_column': end_column,
            'line': line
        })

    # Identify lines with class variables and extract comments
    variable_to_comment = {}
    for tokens in line_to_tokens.values():
        for i, token in enumerate(tokens):
            # Skip past all the whitespace
            if token['token'].strip() == '':
                continue

            # Match class variable and extract comment
            # TODO: support other indenting styles???
            if (token['token_type'] == tokenize.NAME and
                    token['start_column'] in [indent + 2, indent + 4] and
                    len(tokens) > i and
                    tokens[i + 1]['token'] in ['=', ':']):
                if tokens[-2]['token_type'] == tokenize.COMMENT:
                    print('hello')
                    variable_to_comment[token['token']] = tokens[-2]['token']
                else:
                    variable_to_comment[token['token']] = ''

            break

    return variable_to_comment
