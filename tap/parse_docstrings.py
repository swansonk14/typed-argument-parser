from typing import Optional, Dict
import re


def extract_descriptions(doc: Optional[str]) -> (Optional[str], Optional[Dict[str, str]]):
    """Extracts the class and variable descriptions from a class-level doc string.

    :param doc: The docstring of a namespace class
    :return: a tuple of the description of the class
        and a dictionary mapping each attribute to its description
    """
    if doc is None:
        return None, None

    # Extract the description from the header
    general_description, attributes_block = doc.split('\n\n', 1)
    general_description = re.sub(' +', ' ', general_description.replace('\t', '').replace('\n', ' '))

    # TODO: This assumes that ':' isn't in the description. Can be cleaned up with better regex.
    # Extract the attributes and descriptions
    enumerated_attributes = attributes_block.replace('\t', '').split(':')[2:]
    attributes = [
            re.sub(' +', ' ', attribute.replace('\n', ''))
            for attribute in enumerated_attributes[::2]
        ]
    descriptions = [
            re.sub(' +', ' ', attribute)[1:-1]
            for attribute in enumerated_attributes[1::2]
        ]
    attribute_descriptions = dict(zip(attributes, descriptions))

    return general_description, attribute_descriptions
