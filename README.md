# Typed Argument Parsing (Tap)

A typed modernization of Python's [argparse](https://docs.python.org/3/library/argparse.html) library with the following benefits.
- Static type checking
- Code completion
- Source code navigation (e.g. go to definition and go to implementation)

<TODO: gifs for the above>

# Tap is Python-native
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
You can make parameters required in Tap by not setting a default -- in our example, we declare `stars: int`, making `stars` a required parameter. Also note that the docstring is compiled to the help strings that are shown with `python main.py -h`. For now, the docstring format in the example is the format that we support. 

Advantages of being Python-native include:
- Overwrite convenient built-in methods (e.g. `process_args` ensures consistency among arguments)
- Add custom methods
- Inherit from your own template classes

## A more advanced example
Let's dive into some of the more advanced features of Tap. Here we highlight that:
- We support all of the functionality from `argparse`'s `add_argument` function for more further use-cases
- We support serialization of user-defined types. By default we support `bool, int, float, str, List[int], List[float], List[str]`

First, we create a custom `Printer` class that adds a custom suffix onto a given string. 
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
    
args = AdvancedArgumentParser().parse_args()

args.printer(f'The package {args.package_name} has {len(args.awards)} awards')
print('-' * 10)
print(args)
print('-' * 10)
print(args.get_reproducibility_info())

args.save('args.json')
```

```
>>> python main.py --package_name Tap --awards super incredible outstanding --is_cool --printer !!!
The package Tap has 3 awards!!!
--------------------------------------------------
{'awards': ['super', 'incredible', 'outstanding'],
 'is_cool': True,
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

TODO: add a thing about subclassing other Taps
