from abc import abstractmethod
from argparse import ArgumentParser, Action

from typed_argument_parsing.parse_docstrings import extract_descriptions


class TypedArgumentParser():

    def __init__(self, *args, **kwargs):
        # Freeze attributes that are arguments before adding more arguments
        self.attributes = self.__dict__.copy()

        # Get descriptions from the TypedNamespace
        self.description, self.variable_description = extract_descriptions(self.__doc__)

        self.arg_parser = ArgumentParser(description=self.description, *args, **kwargs)
        self.add_arguments()

    def add_argument(self, *args, **kwargs) -> None:
        # Get variable name
        variable = self.arg_parser._get_optional_kwargs(*args, **kwargs)['dest']

        # Get type from custom namespace annotations if not specified
        if variable in self.__annotations__:
            annotation = self.__annotations__[variable]
            kwargs['type'] = kwargs.get('type', annotation)
            kwargs['help'] = kwargs.get('help', f"({annotation.__name__}) {self.variable_description[variable]}")

        # Get default from custom namespace if not specified
        if hasattr(self, variable):
            kwargs['default'] = kwargs.get('default', getattr(self, variable))

        self.arg_parser.add_argument(*args, **kwargs)

    @abstractmethod
    def add_arguments(self) -> None:
        pass

    def parse_args(self) -> 'TypedArgumentParser':
        default_namespace = self.arg_parser.parse_args()

        for variable, value in vars(default_namespace).items():
            # Check if variable has been defined for the TypedNamespace
            if variable not in self.__annotations__:
                raise ValueError(f'Variable "{variable}" is not defined in class "{self.__class__.__name__}.')

            # Ensure the variable is of the right type
            variable_type, arg_type = self.__annotations__[variable], type(value)
            if variable_type != arg_type:
                raise ValueError(f'Variable "{variable}" of type "{arg_type}" does not match annotation type '
                                 f'"{variable_type}" for class "{self.__class__.__name__}".')

            # Set variable
            setattr(self, variable, value)

        return self
