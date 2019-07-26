import os
import subprocess
from typing import Any, List, Union


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
