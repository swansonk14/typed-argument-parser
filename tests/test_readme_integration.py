from typing import List
import io
from contextlib import redirect_stdout

import unittest
from unittest import TestCase

from tap import Tap


class SimpleArgumentParserIntegrationTests(TestCase):

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


class AdvancedArgumentParserIntegrationTests(TestCase):

    def setUp(self):

        class Printer:
            def __init__(self, suffix: str = ''):
                self.suffix = suffix

            def __call__(self, string: str) -> None:
                print(f'{string}{self.suffix}')

        class AdvancedArgumentParser(Tap):
            """You can do a lot with Tap!

            Arguments:
            :package_name: The name of a package.
                Note - we'd prefer cooler packages.
            :awards: The awards won by this package.
            :num_stars: The number of stars that this package received.
            :is_cool: Indicate whether or not the package is cool.
            :printer: Adds a suffix to the string being printed.
            """
            package_name: str
            awards: List[str] = []
            num_stars: float = 3.14
            is_cool: bool = False
            printer: Printer = Printer()

            def add_arguments(self) -> None:
                self.add_argument('-n', '--package_name')
                self.add_argument('-ns', '--num_stars')
                self.add_argument('--printer', type=Printer)

            def process_args(self) -> None:
                # Double check the input is valid
                cool_cutoff = 10
                if self.num_stars > cool_cutoff and not self.is_cool:
                    raise ValueError(f'A package with more than {cool_cutoff} stars must be marked cool.')

                # Automatically modify arguments for consistency
                if len(self.awards) > 2:
                    self.is_cool = True

        self.args = AdvancedArgumentParser().parse_args([
            '-n', 'Tap',
            '--awards', 'super', 'incredible', 'outstanding',
            '--is_cool', '--printer', '!!!',
            ])

    def test_assignments_as_dict(self):
        full_results = self.args.as_dict()
        keys = {'package_name', 'awards', 'num_stars', 'is_cool', 'printer'}
        self.assertEqual(set(full_results.keys()), keys)

        values = [['super', 'incredible', 'outstanding'], 3.14, True, 'Tap']
        for v in values:
            self.assertTrue(v in full_results.values())

    def test_individual_properties(self):
        self.assertEqual(self.args.package_name, 'Tap')
        self.assertEqual(set(self.args.awards), {'super', 'incredible', 'outstanding'})
        self.assertEqual(self.args.num_stars, 3.14)
        self.assertEqual(self.args.is_cool, True)

        # Capture the printed result in a variable
        with io.StringIO() as buf, redirect_stdout(buf):
            self.args.printer('')
            output = buf.getvalue()
            self.assertEqual(output, '!!!\n')

    def test_docstring_parsing(self):
        self.assertEqual(self.args.description, 'You can do a lot with Tap!')

        variable_descriptions = {k: v.strip() for k, v in self.args.variable_description.items()}
        self.assertEqual(variable_descriptions, {
            'package_name': 'The name of a package.\nNote - we\'d prefer cooler packages.',
            'awards': 'The awards won by this package.',
            'num_stars': 'The number of stars that this package received.',
            'is_cool': 'Indicate whether or not the package is cool.',
            'printer': 'Adds a suffix to the string being printed.'
            })

    def test_reproducibility_info(self):
        repro_result = self.args.get_reproducibility_info()
        self.assertTrue(isinstance(repro_result, dict))

        keys = repro_result.keys()
        self.assertTrue('command_line' in keys)
        self.assertTrue('time' in keys)


if __name__ == '__main__':
    unittest.main()
