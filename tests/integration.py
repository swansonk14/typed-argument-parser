import unittest
from unittest import TestCase

from tap import Tap


class SimpleArgumentParserIntegrationTestCase(TestCase):

    def setUp(self):

        class SimpleArgumentParser(Tap):
            """This is a simple argument parser.

            Arguments:
            :name: Your first name only please.
            :language: The programming language of the package.
            :package: The name of the package to rate.
            :stars: The number of stars to give the package.
            :max_stars: The maximum number of stars a package can receive.
            """
            name: str
            language: str = 'Python'
            package: str = 'Tap'
            stars: int
            max_stars: int = 5

        self.args = SimpleArgumentParser().parse_args(args=['--name', 'Jesse', '--stars', '5'])

    def test_assignments_as_dict(self):
        self.assertEqual(self.args.as_dict(), {'language': 'Python',
                                               'package': 'Tap',
                                               'max_stars': 5,
                                               'name': 'Jesse',
                                               'stars': 5})

    def test_individual_properties(self):
        self.assertEqual(self.args.name, 'Jesse')
        self.assertEqual(self.args.language, 'Python')
        self.assertEqual(self.args.package, 'Tap')
        self.assertEqual(self.args.max_stars, 5)
        self.assertEqual(self.args.stars, 5)

    def test_docstring_parsing(self):
        self.assertEqual(self.args.description, 'This is a simple argument parser.')

        variable_descriptions = {k: v.strip() for k, v in self.args.variable_description.items()}
        self.assertEqual(variable_descriptions, {
            'name': 'Your first name only please.',
            'language': 'The programming language of the package.',
            'package': 'The name of the package to rate.',
            'stars': 'The number of stars to give the package.',
            'max_stars': 'The maximum number of stars a package can receive.'
            })


if __name__ == '__main__':
    unittest.main()
