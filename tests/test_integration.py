from typing import List
import io

import unittest
from unittest import TestCase

from tap import Tap


class NotEnoughDocumentation(TestCase):

    def setUp(self):

        class NotEnoughDocumentation(Tap):
            """This is a simple argument parser.

            Arguments:
            :arg1: First argument.
            """
            arg1: str = 'hi'
            arg2: str = 'there'

        self.args = NotEnoughDocumentation().parse_args()

    def test_assignments_as_dict(self):
        self.assertEqual(self.args.as_dict(), {'arg1': 'hi',
                                               'arg2': 'there'})

    def test_docstring_parsing(self):
        self.assertEqual(self.args.description, 'This is a simple argument parser.')

        variable_descriptions = {k: v.strip() if v else v for k, v in self.args.variable_description.items()}
        self.assertEqual(variable_descriptions, {
            'arg1': 'First argument.',
            'arg2': ''})


class BadDocumentation(TestCase):

    def test_ignore_listing_too_many_arguments(self):

        class TooMuchDocumentation(Tap):
            """This is a simple argument parser.

            Arguments:
            :arg1: First arg.
            :arg2: Second arg.
            :arg3: Third arg.
            """
            arg1: str = "hi"
            arg2: str = "there"

        args = TooMuchDocumentation().parse_args()

        # The third argument in the documentation is ignored
        self.assertEqual(len(args._actions), 3)

    def test_ignore_incorrect_arguments(self):

        class MispelledDocumentation(Tap):
            """This is a simple argument parser.

            Arguments:
            :blarg: First arg.
            """
            arg: str = "hi"

        args = MispelledDocumentation().parse_args()
        self.assertEqual(args.variable_description["arg"], '')
        self.assertRaises(TypeError, args.variable_description["blarg"])

if __name__ == '__main__':
    unittest.main()
