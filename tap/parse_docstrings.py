from typing import Optional, Dict
import re


def extract_descriptions(doc: Optional[str]) -> (Optional[str], Optional[Dict[str, str]]):
    """Extracts the class and variable descriptions from a class-level doc string.

    Attributes:
    :param doc: The docstring of a namespace class
    :return: a tuple of the description of the class
        and a dictionary mapping each attribute to its description
    """
    if doc is None:
        return None, None

    # Extract the description from the header
    try:
        # Split on the attributes keyword
        general_description, attributes_block = re.split(r'[\t| ]*\n+[\t| ]*Attributes:', doc, maxsplit=1)
    except ValueError:
        raise ValueError("""The documentation should be of the form:

        Description

        Attributes:
        :arg1: Description
        :arg2: Description""")
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

    attribute_descriptions = dict(zip(attributes, descriptions))

    return general_description, attribute_descriptions
