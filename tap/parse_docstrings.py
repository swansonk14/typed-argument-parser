from typing import Dict, Optional, Tuple
import re
from collections import defaultdict


def extract_descriptions(doc: Optional[str]) -> Tuple[Optional[str], Optional[Dict[str, str]], Optional[ValueError]]:
    """Extracts the class and variable descriptions from a class-level doc string.

    :param doc: The docstring of a namespace class
    :return: a tuple of the description of the class
        and a dictionary mapping each attribute to its description
    """

    # We never want to raise errors for problems with documentation parsing.
    try:
        error_string = ''
        general_description, attribute_descriptions, error_string = _parse_docstring(doc)

        # If an error was detected, raise.
        if error_string:
            raise
    except:
        # Invalidate descriptions
        general_description, attribute_descriptions = '', defaultdict(lambda: '')

        # Add on a default error.
        if not error_string:
            error_string = ''
        error_string += """\nThe documentation should be of the form:

        Description

        Arguments:
        :arg1: Description
        :arg2: Description"""

    return general_description, attribute_descriptions, error_string


def _parse_docstring(doc: Optional[str]) -> Tuple[Optional[str], Optional[Dict[str, str]], Optional[ValueError]]:
    """Parses a sphinx-style docstring.

    :param doc: The docstring of a namespace class
    :return: a tuple of the description of the class
        and a dictionary mapping each attribute to its description
    """
    error_string = None

    if doc is None:
        return '', dict()

    # Extract the description from the header
    try:
        # Split on the attributes keyword
        general_description, attributes_block = re.split(r'[\t| ]*\n+[\t| ]*Arguments:', doc, maxsplit=1)
    except ValueError:
        error_string = 'Tap cannot find the "Arguments:" keyword.'
        return '', '', error_string

    general_description = re.sub(' +', ' ', general_description.replace('\t', ''), count=1).replace('  ', '').strip()

    # Extract the attributes and descriptions
    attributes = [
        s.replace('  ', '').strip()
        for s in re.findall(':(\w*):', attributes_block)
    ]

    descriptions = [
        s.replace('  ', '').strip()
        for s in re.split('[\n ]*:\w*: ', attributes_block)[1:]
    ]

    try:
        # Attributes and descriptions should match up one-to-one
        assert len(attributes) == len(descriptions)
        attribute_descriptions = dict(zip(attributes, descriptions))
    except (AttributeError, AssertionError):
        error_string = 'Tap is having trouble matching attributes with descriptions.'
        return general_description, '', error_string

    return general_description, attribute_descriptions, error_string
