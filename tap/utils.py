import os
import subprocess
from typing import Any, Union


NO_CHANGES_STATUS = """nothing to commit, working tree clean"""


def has_git() -> bool:
    """Checks if git is installed."""
    try:
        subprocess.run(['git', '--version'])
        return True
    except FileNotFoundError:
        return False


def get_git_root() -> str:
    """Gets the root of the git repo."""
    return subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).decode('utf-8').strip()


def get_git_url() -> str:
    """Gets the git url."""
    # Get either https or ssh url
    url: str = subprocess.check_output(['git', 'remote', 'get-url', 'origin']).decode('utf-8').strip()

    # Checks
    assert url.startswith('https://github.com') or url.startswith('git@github.com')
    assert url.endswith('.git')

    # Remove .git at end
    url = url[:-len('.git')]

    # Fix ssh url
    if url.startswith('git@github.com:'):
        url = url[len('git@github.com:'):]
        url = f'https://github.com/{url}'

    # Add tree and hash
    url = os.path.join(url, 'tree', get_git_hash())

    return url


def get_git_hash() -> str:
    """Gets the git hash of HEAD. Ignores uncommitted changes."""
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()


def has_uncommitted_changes() -> bool:
    """Checks whether there are uncommitted changes in the git repo."""
    status: str = subprocess.check_output(['git', 'status']).decode('utf-8').strip()

    return not status.endswith(NO_CHANGES_STATUS)


def type_to_str(type_annotation: Union[type, Any]) -> str:
    """Gets a string representation of the provided type."""
    # Built-in type
    if type(type_annotation) == type:
        return type_annotation.__name__

    # Type annotation type
    return str(type_annotation).replace('typing.', '')
