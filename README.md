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
  - Validating arguments (`validate_args`) to ensure consistency among arguments
  - Modifying arguments (`modify_args`) to update the parsed arguments if necessary
- Add you own methods
- Inherit from your own template classes

## A more advanced example

<TODO show all we can do!>