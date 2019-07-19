import subprocess


NO_CHANGES_STATUS = """On branch master
nothing to commit, working tree clean"""


def has_git() -> bool:
    """Checks if git is installed."""
    try:
        subprocess.check_output(['git', '--version'])
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

    # Remove .git at end
    url = url[:-len('.git')]

    # Fix ssh url
    if url.startswith('git@'):
        url = url[len('git@github.com:'):]
        url = f'https://github.com/{url}'

    # Add tree and hash
    url = f'{url}/tree/{get_git_hash()}'

    return url


def get_git_hash() -> str:
    """Gets the git hash of HEAD. Ignores uncommitted changes."""
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()


def has_uncommitted_changes() -> bool:
    """Checks whether there are uncommitted changes in the git repo."""
    status = subprocess.check_output(['git', 'status']).decode('utf-8').strip()

    return status != NO_CHANGES_STATUS
