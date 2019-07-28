import unittest
from unittest import TestCase

from tap.parse_docstrings import extract_descriptions


class DocstringParsingTests(TestCase):

    def test_simple_docstring(self) -> None:
        simplest_docstring = """How simple is this docstring?

        Arguments:
        :pretty_simple: this is quite simple
        :very_simple: quite as simple as it gets
        """
        gen_desc, attr_desc, error_string = extract_descriptions(simplest_docstring)
        self.assertEqual(gen_desc, "How simple is this docstring?")
        self.assertEqual(attr_desc, {
            "pretty_simple": "this is quite simple",
            "very_simple": "quite as simple as it gets",
            })

    def test_with_extract_tab(self) -> None:
        extra_tabs = """Extra tab.\n\t \nArguments:\n:arg: desc"""
        gen_desc, attr_desc, error_string = extract_descriptions(extra_tabs)
        self.assertEqual(gen_desc, "Extra tab.")
        self.assertEqual(attr_desc, {"arg": "desc"})

    def test_multiline_descriptions(self) -> None:
        long_descriptions = """Longer description with an unnecessary tabs.

        More of a description
        Arguments:
        :arg: far
        too
        many enters
        :more_args: trailing enters

            at the end

         """
        gen_desc, attr_desc, error_string = extract_descriptions(long_descriptions)
        self.assertEqual(gen_desc, "Longer description with an unnecessary tabs.\n\nMore of a description")
        self.assertEqual(attr_desc, {
            "arg": "far\ntoo\nmany enters",
            "more_args": "trailing enters\n\nat the end",
            })
        self.assertIsNone(error_string)

    def test_no_attribute_errors(self) -> None:
        no_attributes = """The comment lacks attributes, which should error out."""
        gen_desc, attr_desc, error_string = extract_descriptions(no_attributes)
        self.assertTrue(not gen_desc)
        self.assertTrue(not attr_desc)
        self.assertIsNotNone(error_string)

    def test_colons_in_description(self) -> None:
        colons_in_description = """So happy :)

        Arguments:
        :arg: still so happy :)
        """
        gen_desc, attr_desc, error_string = extract_descriptions(colons_in_description)
        self.assertEqual(gen_desc, "So happy :)")
        self.assertEqual(attr_desc, {"arg": "still so happy :)"})
        self.assertIsNone(error_string)

    def test_sneaky_attributes(self) -> None:
        colons_in_description = """Arguments: So happy :) Arguments:

        Arguments:
        :arg: still so happy :) Arguments:
        :another_arg: the arg
        """
        gen_desc, attr_desc, error_string = extract_descriptions(colons_in_description)
        self.assertEqual(gen_desc, "Arguments: So happy :) Arguments:")
        self.assertEqual(attr_desc, {
            'arg': 'still so happy :) Arguments:',
            'another_arg': 'the arg'
            })
        self.assertIsNone(error_string)

    # A debatable example.
    # def test_no_description(self) -> None:
    #     no_main_description = """
    #     Arguments:
    #     :arg: the first arg
    #     """
    #     gen_desc, attr_desc = extract_descriptions(no_main_description)
    #     self.assertEqual(gen_desc, "")
    #     self.assertEqual(attr_desc, {"arg": "the first arg"})


if __name__ == '__main__':
    unittest.main()
