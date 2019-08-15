# Typed Argument Parsing (Tap)

Tap is a typed modernization of Python's [argparse](https://docs.python.org/3/library/argparse.html) library with the following benefits:
- Static type checking
- Code completion
- Source code navigation (e.g. go to definition and go to implementation)

<TODO: gifs for the above>

## Tap is Python-native
To see this, let's look at an example:

```python
"""main.py"""

from tap import Tap

class SimpleArgumentParser(Tap):
    """This is a simple argument parser.
    
    Arguments:
    :name: Your name.
    :language: Programming language.
    :package: Package name.
    :stars: Number of stars.
    :max_stars: Maximum stars.
    """
    name: str
    language: str = 'Python'
    package: str = 'Tap'
    stars: int
    max_stars: int = 5
    
args = SimpleArgumentParser().parse_args()

print(f'My name is {args.name} and I give the {args.language} package '
      f'{args.package} {args.stars}/{args.max_stars} stars!')
```

Note that `name` is automatically made a required argument since no default is provided.

You use Tap the same way you use standard argparse.

```
>>> python main.py --name Jesse --stars 5
My name is Jesse and I give the Python package Tap 5/5 stars!
```

The equivalent `argparse` code is:
```python
"""main.py"""

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('--name', type=str, required=True,
                    help='Your name.')
parser.add_argument('--language', type=str,
                    help='Programming language.')
parser.add_argument('--package', type=str, default='Tap',
                    help='Package name.')
parser.add_argument('--stars', type=int, required=True,
                    help='Number of stars.')
parser.add_argument('--max_stars', type=int, default=5,
                    help='Maximum stars.')
args = parser.parse_args()

print(f'My name is {args.name} and I give the {args.language} package '
      f'{args.package} {args.stars}/{args.max_stars} stars!')
```

The advantages of being Python-native include being able to:
- Overwrite convenient built-in methods (e.g. `process_args` ensures consistency among arguments)
- Add custom methods
- Inherit from your own template classes

### Tap features

Here we overview the major features of Tap.

#### Tap arguments

Arguments are specified as class variables defined in a subclass of `Tap`. Variables defined as `name: type` are required arguments while variables defined as `name: type = value` are not required and default to the provided value.

```python
class MyTap(Tap):
    required_arg: str
    default_arg: str = 'default value'
```

#### Help string

Class documentation is automatically parsed into the help string provided when running `python main.py -h`.

```python
"""main.py"""

from tap import Tap

class MyTap(Tap):
    """You can document Tap!

    Arguments:
    :argument: This is an argument.
    """
    argument: str = "I'm well documented!"

args = MyTap().parse_args()
```

Running `python main.py -h` would result in the following:

```
>>> python main.py -h
usage: blah.py [-h] [--arg ARG]

You can document Tap!

optional arguments:
  -h, --help  show this help message and exit
  --argument ARGUMENT   (str) This is an argument.
```

Documentation must follow the format seen above in order to appear in the help string, otherwise it is ignored.

#### Flexibility with `add_arguments`

Python's argparse provides a number of advanced argument parsing features with the `add_argument` method. Since Tap is a wrapper around argparse, Tap provides all of the same functionality.

To make use of this functionality, first define arguments as class variables as usual, then override Tap's `add_arguments` and use `self.add_argument` just as you would use argparse's `add_argument`.

```python
from tap import Tap

class MyTap(Tap):
    positional_argument: str
    list_of_three_things: List[str]
    argument_with_really_long_name: int

    def add_arguments(self):
        self.add_argument('positional_argument')
        self.add_argument('--list_of_three_things', nargs=3)
        self.add_argument('-arg', '--argument_with_really_long_name')
```

#### Types

Tap automatically handles all of the following types:
- `str`
- `int`
- `float`
- `bool`
- `List[str]`
- `List[int]`
- `List[float]`

`str`, `int`, and `float` arguments: These arguments are automatically parsed to their respective types, just like argparse.

`bool` arguments: If an argument `arg` is specified as `arg: bool` or `arg: bool = False`, then adding the `--arg` flag to the command line will set `arg` to `True`. If `arg` is specified as `arg: bool = True`, then adding `--arg` sets `arg` to `False`.

`List` arguments: If an argument `arg` is a `List`, simply specify the values separated by spaces just as you would with regular argparse. For example, `--arg 1 2 3` parses to `arg = [1, 2, 3]`.

More complex types must be specified with the `type` keyword argument in `add_argument`, as in the example below.

```python
def to_number(string: str):
    return float(string) if '.' in input else int(string)

class MyTap(Tap):
    number: Union[int, float]

    def add_arguments(self):
        self.add_argument('--percent', type=to_number)
```

#### Argument processing with `process_args`

#### Subclassing

#### Printing

#### Reproducibility

info plus saving




Let's dive into some of the more advanced features of Tap.
 
- required vs default
- built-in types
- non-built in types
- custom functionality with add_argument
 
 Here we highlight that:
- We support all of the functionality from `argparse`'s `add_argument` function for more further use-cases
- We support serialization of user-defined types. By default we support `bool, int, float, str, List[int], List[float], List[str]`


```python
"""main.py"""
from typing import List

from tap import Tap


class Printer:
    def __init__(self, suffix: str = ''):
        self.suffix = suffix
    
    def __call__(self, string: str) -> None:
        print(f'{string}{self.suffix}')


class AdvancedArgumentParser(Tap):
    """You can do a lot with Tap!

    Arguments:
    :package_name: Name of the package.
    :awards: Awards won by the package.
    :num_stars: Number of stars.
    :is_cool: Whether the package is cool.
    :printer: Prints strings.
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


class SubAdvancedArgumentParser(AdvancedArgumentParser):
    """You can even subclass with Tap!
    
    :language: Programming language.
    """
    language: str = 'Python'

args = SubAdvancedArgumentParser().parse_args()

args.printer(f'The {args.language} package {args.package_name} has {len(args.awards)} awards')
print('-' * 10)
print(args)
print('-' * 10)
print(args.get_reproducibility_info())

args.save('args.json')
```

```
>>> python main.py --package_name Tap --awards super incredible outstanding --is_cool --printer !!!
The Python package Tap has 3 awards!!!
--------------------------------------------------
{'awards': ['super', 'incredible', 'outstanding'],
 'is_cool': True,
 'language': 'Python',
 'num_stars': 3.14,
 'package_name': 'Tap',
 'printer': <__main__.Printer object at 0x105048e80>}
--------------------------------------------------
{'command_line': 'python [[PYTHON_PATH]]',
 'time': '[[EXPERIMENT_TIME]]',
 'git_root': '[[PATH]]/typed-argument-parsing',
 'git_url': 'https://github.com/swansonk14/typed-argument-parsing/tree/[[COMMIT_HASH]]',
  'git_has_uncommitted_changes': False}
```
