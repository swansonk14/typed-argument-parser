from collections import OrderedDict
import os
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Callable, List, Dict, Set, Tuple, Union
import unittest
from unittest import TestCase
from typing_extensions import Literal

from tap.utils import (
    get_class_column,
    get_class_variables,
    get_git_root,
    get_git_url,
    has_uncommitted_changes,
    type_to_str,
    get_literals
)


class GitTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        subprocess.check_output(['git', 'init'])
        self.url = 'https://github.com/test_account/test_repo'
        subprocess.check_output(['git', 'remote', 'add', 'origin', f'{self.url}.git'])
        subprocess.check_output(['touch', 'README.md'])
        subprocess.check_output(['git', 'add', 'README.md'])
        subprocess.check_output(['git', 'commit', '-m', 'Initial commit'])

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_get_git_root(self) -> None:
        self.assertTrue(get_git_root() in f'/private{self.temp_dir.name}')

    def test_get_git_root_subdir(self) -> None:
        os.makedirs(os.path.join(self.temp_dir.name, 'subdir'))
        self.assertTrue(get_git_root() in f'/private{self.temp_dir.name}')

    def test_get_git_url_https(self) -> None:
        self.assertEqual(get_git_url(commit_hash=False), self.url)

    def test_get_git_url_https_hash(self) -> None:
        url = f'{self.url}/tree/'
        self.assertEqual(get_git_url(commit_hash=True)[:len(url)], url)

    def test_get_git_url_ssh(self) -> None:
        subprocess.run(['git', 'remote', 'set-url', 'origin', 'git@github.com:test_account/test_repo.git'])
        self.assertEqual(get_git_url(commit_hash=False), self.url)

    def test_get_git_url_ssh_hash(self) -> None:
        subprocess.run(['git', 'remote', 'set-url', 'origin', 'git@github.com:test_account/test_repo.git'])
        url = f'{self.url}/tree/'
        self.assertEqual(get_git_url(commit_hash=True)[:len(url)], url)

    def test_get_git_url_https_enterprise(self) -> None:
        true_url = 'https://github.tap.com/test_account/test_repo'
        subprocess.run(['git', 'remote', 'set-url', 'origin', f'{true_url}.git'])
        self.assertEqual(get_git_url(commit_hash=False), true_url)

    def test_get_git_url_https_hash_enterprise(self) -> None:
        true_url = 'https://github.tap.com/test_account/test_repo'
        subprocess.run(['git', 'remote', 'set-url', 'origin', f'{true_url}.git'])
        url = f'{true_url}/tree/'
        self.assertEqual(get_git_url(commit_hash=True)[:len(url)], url)

    def test_get_git_url_ssh_enterprise(self) -> None:
        true_url = 'https://github.tap.com/test_account/test_repo'
        subprocess.run(['git', 'remote', 'set-url', 'origin', 'git@github.tap.com:test_account/test_repo.git'])
        self.assertEqual(get_git_url(commit_hash=False), true_url)

    def test_get_git_url_ssh_hash_enterprise(self) -> None:
        true_url = 'https://github.tap.com/test_account/test_repo'
        subprocess.run(['git', 'remote', 'set-url', 'origin', 'git@github.tap.com:test_account/test_repo.git'])
        url = f'{true_url}/tree/'
        self.assertEqual(get_git_url(commit_hash=True)[:len(url)], url)

    def test_has_uncommitted_changes_false(self) -> None:
        self.assertFalse(has_uncommitted_changes())

    def test_has_uncommited_changes_true(self) -> None:
        subprocess.run(['touch', 'main.py'])
        self.assertTrue(has_uncommitted_changes())


class TypeToStrTests(TestCase):
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
        self.assertEqual(type_to_str(Set[int]), 'Set[int]')
        self.assertEqual(type_to_str(Dict[str, int]), 'Dict[str, int]')
        self.assertEqual(type_to_str(Union[List[int], Dict[float, bool]]), 'Union[List[int], Dict[float, bool]]')


class ClassColumnTests(TestCase):
    def test_column_simple(self):
        class SimpleColumn:
            arg = 2
        self.assertEqual(get_class_column(SimpleColumn), 12)

    def test_column_comment(self):
        class CommentColumn:
            """hello
            there


            hi
            """
            arg = 2
        self.assertEqual(get_class_column(CommentColumn), 12)

    def test_column_space(self):
        class SpaceColumn:

            arg = 2
        self.assertEqual(get_class_column(SpaceColumn), 12)

    def test_column_method(self):
        class FuncColumn:
            def func(self):
                pass

        self.assertEqual(get_class_column(FuncColumn), 12)


class ClassVariableTests(TestCase):
    def test_no_variables(self):
        class NoVariables:
            pass
        self.assertEqual(get_class_variables(NoVariables), OrderedDict())

    def test_one_variable(self):
        class OneVariable:
            arg = 2
        class_variables = OrderedDict()
        class_variables['arg'] = {'comment': ''}
        self.assertEqual(get_class_variables(OneVariable), class_variables)

    def test_multiple_variable(self):
        class MultiVariable:
            arg_1 = 2
            arg_2 = 3
        class_variables = OrderedDict()
        class_variables['arg_1'] = {'comment': ''}
        class_variables['arg_2'] = {'comment': ''}
        self.assertEqual(get_class_variables(MultiVariable), class_variables)

    def test_typed_variables(self):
        class TypedVariable:
            arg_1: str
            arg_2: int = 3
        class_variables = OrderedDict()
        class_variables['arg_1'] = {'comment': ''}
        class_variables['arg_2'] = {'comment': ''}
        self.assertEqual(get_class_variables(TypedVariable), class_variables)

    def test_separated_variables(self):
        class SeparatedVariable:
            """Comment

            """
            arg_1: str

            # Hello
            def func(self):
                pass

            arg_2: int = 3
            """More comment"""
        class_variables = OrderedDict()
        class_variables['arg_1'] = {'comment': ''}
        class_variables['arg_2'] = {'comment': ''}
        self.assertEqual(get_class_variables(SeparatedVariable), class_variables)

    def test_commented_variables(self):
        class CommentedVariable:
            """Comment

            """
            arg_1: str  # Arg 1 comment

            # Hello
            def func(self):
                pass

            arg_2: int = 3  # Arg 2 comment
            arg_3   :   Dict[str, int]      #     Poorly   formatted comment
            """More comment"""
        class_variables = OrderedDict()
        class_variables['arg_1'] = {'comment': 'Arg 1 comment'}
        class_variables['arg_2'] = {'comment': 'Arg 2 comment'}
        class_variables['arg_3'] = {'comment': 'Poorly   formatted comment'}
        self.assertEqual(get_class_variables(CommentedVariable), class_variables)


class GetLiteralsTests(TestCase):
    def test_get_literals_string(self) -> None:
        literal_f, shapes = get_literals(Literal['square', 'triangle', 'circle'], 'shape')
        self.assertEqual(shapes, ['square', 'triangle', 'circle'])
        self.assertEqual(literal_f('square'), 'square')
        self.assertEqual(literal_f('triangle'), 'triangle')
        self.assertEqual(literal_f('circle'), 'circle')
        with self.assertRaises(KeyError):
            literal_f('tuba')

    def test_get_literals_primitives(self) -> None:
        literals = [True, 'one', 2, 3.14]
        literal_f, prims = get_literals(Literal[True, 'one', 2, 3.14], 'number')
        self.assertEqual(prims, literals)
        self.assertEqual([literal_f(str(p)) for p in prims], literals)
        with self.assertRaises(KeyError):
            literal_f(3)

    def test_get_literals_primitives(self) -> None:
        with self.assertRaises(ValueError):
            literal_f, prims = get_literals(Literal['two', 2, '2'], 'number')

    def test_get_literals_empty(self) -> None:
        literal_f, prims = get_literals(Literal, 'hi')
        self.assertEqual(prims, [])
        with self.assertRaises(KeyError):
            literal_f(None)


if __name__ == '__main__':
    unittest.main()
