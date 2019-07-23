import os
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Callable, List, Dict, Tuple, Union
import unittest
from unittest import TestCase

from tap.utils import get_git_root, get_git_url, has_uncommitted_changes, type_to_str


class GitTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        subprocess.run(['git', 'init'])
        self.url = 'https://github.com/test_account/test_repo/tree'
        subprocess.run(['git', 'remote', 'add', 'origin', self.url.replace('/tree', '.git')])
        subprocess.run(['touch', 'README.md'])
        subprocess.run(['git', 'add', 'README.md'])
        subprocess.run(['git', 'commit', '-m', 'Initial commit'])

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_get_git_root(self) -> None:
        self.assertEqual(get_git_root(), f'/private{self.temp_dir.name}')

        os.makedirs(os.path.join(self.temp_dir.name, 'subdir'))
        self.assertEqual(get_git_root(), f'/private{self.temp_dir.name}')

    def test_get_git_url(self) -> None:
        self.assertEqual(get_git_url()[:len(self.url)], self.url)

        subprocess.run(['git', 'remote', 'set-url', 'origin', 'git@github.com:test_account/test_repo.git'])
        self.assertEqual(get_git_url()[:len(self.url)], self.url)

    def test_has_uncommitted_changes(self) -> None:
        self.assertFalse(has_uncommitted_changes())

        subprocess.run(['touch', 'main.py'])
        self.assertTrue(has_uncommitted_changes())


class UtilTests(TestCase):
    def test_type_to_str(self) -> None:
        self.assertEqual(type_to_str(str), 'str')
        self.assertEqual(type_to_str(int), 'int')
        self.assertEqual(type_to_str(float), 'float')
        self.assertEqual(type_to_str(bool), 'bool')
        self.assertEqual(type_to_str(Any), 'Any')
        self.assertEqual(type_to_str(Callable[[str], str]), 'Callable[[str], str]')
        self.assertEqual(type_to_str(Callable[[str, int], Tuple[float, bool]]), 'Callable[[str, int], Tuple[float, bool]]')
        self.assertEqual(type_to_str(List[int]), 'List[int]')
        self.assertEqual(type_to_str(List[str]), 'List[str]')
        self.assertEqual(type_to_str(List[float]), 'List[float]')
        self.assertEqual(type_to_str(List[bool]), 'List[bool]')
        self.assertEqual(type_to_str(Dict[str, int]), 'Dict[str, int]')
        self.assertEqual(type_to_str(Union[List[int], Dict[float, bool]]), 'Union[List[int], Dict[float, bool]]')


if __name__ == '__main__':
    unittest.main()
