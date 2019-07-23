from typing import Any, Callable, List, Dict, Tuple, Union
import unittest
from unittest import TestCase

from tap.utils import type_to_str


class UnitTests(TestCase):
    def test_type_to_str(self):
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
