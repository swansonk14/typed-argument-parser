# Typed Argument Parsing (Tap)

A typed wrapper around Python's [argparse](https://docs.python.org/3/library/argparse.html) library.


Here's a simple example of how to use Tap:


```python
"""main.py"""

from tap import Tap

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
                    help='Your first name only please.')
parser.add_argument('--language', type=str,
                    help='The programming language of the package.')
parser.add_argument('--package', type=str, default='Tap',
                    help='The name of the Python package to rate.')
parser.add_argument('--stars', type=int, required=True,
                    help='The number of stars to give the package.')
parser.add_argument('--max_stars', type=int, default=5,
                    help='The maximum number of stars a package can receive.')
args = parser.parse_args()

print(f'My name is {args.name} and I give the {args.language} package '
      f'{args.package} {args.stars}/{args.max_stars} stars!')
```

## Why Tap?
As a wrapper of `argparse`, we support all of its functionality, modernize it, and extend it to support:
- Static type checking
- Code completion
- Source code navigation (e.g. go to definition and go to implementation)

<TODO: gifs for the above>

Since parsed arguments are now a class, you can:
- Overwrite convenient built-in methods including:
  - Processing arguments (`process_args`) to ensure consistency among arguments
- Add you own methods
- Inherit from your own template classes

## A more advanced example
Now we'll present an example that features provided by Tap.

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