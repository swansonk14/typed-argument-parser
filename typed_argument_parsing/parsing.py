from abc import abstractmethod
from argparse import ArgumentParser, Action
from typing import Optional, Sequence, Type

from typed_argument_parsing.parse_docstrings import extract_descriptions


class TypedNamespace:
    def __init__(self, **kwargs):
        for variable, value in kwargs.items():
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


class TypedArgumentParser(ArgumentParser):
    def __init__(self, namespace_class: Type, *args, **kwargs):
        self.namespace_class = namespace_class

        # Get descriptions from the TypedNamespace
        self.description, self.variable_description = extract_descriptions(self.namespace_class.__doc__)

        super(TypedArgumentParser, self).__init__(description=self.description, *args, **kwargs)
        self.add_arguments()

    def add_argument(self, *args, **kwargs) -> Action:
        # Get variable name
        variable = self._get_optional_kwargs(*args, **kwargs)['dest']

        # Get type from custom namespace annotations if not specified
        if variable in self.namespace_class.__annotations__:
            annotation = self.namespace_class.__annotations__[variable]
            kwargs['type'] = kwargs.get('type', annotation)
            kwargs['help'] = kwargs.get('help', f"({annotation.__name__}) {self.variable_description[variable]}")

        # Get default from custom namespace if not specified
        if hasattr(self.namespace_class, variable):
            kwargs['default'] = kwargs.get('default', getattr(self.namespace_class, variable))

        return super(TypedArgumentParser, self).add_argument(*args, **kwargs)

    @abstractmethod
    def add_arguments(self) -> None:
        pass

    def parse_args(self,
                   args: Optional[Sequence[str]] = None,
                   namespace: Optional[TypedNamespace] = None) -> TypedNamespace:
        default_namespace = super(TypedArgumentParser, self).parse_args(args, namespace)
        custom_namespace = self.namespace_class(**vars(default_namespace))

        return custom_namespace
