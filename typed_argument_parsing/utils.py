import subprocess


def get_git_root() -> str:
    """Gets the root of the git repo."""
    return subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).decode('utf-8').strip()


def get_git_hash() -> str:
    """Gets the git hash of HEAD. Ignores uncommitted changes."""
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
