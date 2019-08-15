# Typed Argument Parsing (Tap)

Tap is a typed modernization of Python's [argparse](https://docs.python.org/3/library/argparse.html) library.

## Why Tap?
 
Tap provides the following benefits with the following benefits:
- Static type checking
- Code completion
- Source code navigation (e.g. go to definition and go to implementation)

<TODO: gifs for the above>
 
## Table of Contents

* [Tap is Python-native](#tap-is-python-native)
* [Tap features](#tap-features)
    + [Arguments](#arguments)
    + [Help string](#help-string)
    + [Flexibility of `add_arguments`](#flexibility-of--add-arguments-)
    + [Types](#types)
    + [Argument processing with `process_args`](#argument-processing-with--process-args-)
    + [Subclassing](#subclassing)
    + [Printing](#printing)
    + [Reproducibility](#reproducibility)
      - [Reproducibility info](#reproducibility-info)
      - [Saving arguments](#saving-arguments)

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

## Tap features

Here we overview the major features of Tap.

### Arguments

Arguments are specified as class variables defined in a subclass of `Tap`. Variables defined as `name: type` are required arguments while variables defined as `name: type = value` are not required and default to the provided value.

```python
class MyTap(Tap):
    required_arg: str
    default_arg: str = 'default value'
```

### Help string

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

### Flexibility of `add_arguments`

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

### Types

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

### Argument processing with `process_args`

With complex argument parsing, it is sometimes necessary to prevent certain combinations of arguments. Futhermore, the value of some arguments may depend on the values of other arguments. To handle cases like these, simply override `process_args` and add the required logic. `process_args` is automatically called when `parse_args` is called.

```python
class MyTap(Tap):
    package: str
    is_cool: bool
    stars: int

    def process_args(self):
        # Validate arguments
        if self.is_cool and self.stars < 4:
            raise ValueError('Cool packages cannot have fewer than 4 stars')

        # Modify arguments
        if self.package == 'Tap':
            self.is_cool = True
            self.stars = 5
```

### Subclassing

In some cases, it may be useful to define a template Tap and then subclass it for different use cases. Since Tap is simply a native Python class, inheritance is built-in.

In the example below, `StarsTap` and `AwardsTap` inherit the arguments (`package` and `is_cool`) and the methods (`process_args`) from `BaseTap`, making it easy to customize a template Tap.

```python
class BaseTap(Tap):
    package: str
    is_cool: bool
    
    def process_args(self):
        if self.package == 'Tap':
            self.is_cool = True


class StarsTap(BaseTap):
    stars: int


class AwardsTap(BaseTap):
    awards: List[str]
```

### Printing

Tap uses Python's [pretty printer](https://docs.python.org/3/library/pprint.html) to print out arguments in an easy-to-read format.

```python
"""main.py"""

from tap import Tap
from typing import List

class MyTap(Tap):
    package: str = 'Tap'
    is_cool: bool = True
    awards: List[str] = ['amazing', 'wow', 'incredible', 'awesome']

args = MyTap().parse_args()
print(args)
```

Running `python main.py` results in:

```
>>> python main.py
{'awards': ['amazing', 'wow', 'incredible', 'awesome'],
 'is_cool': True,
 'package': 'Tap'}
```

### Reproducibility

Tap makes reproducibility easy, especially when running code in a git repo.

#### Reproducibility info

Specifically, Tap has a method called `get_reproducibility_info` that returns a dictionary containing information necessary to replicate the settings under which the code was run. This dictionary includes:
- Python command
    - The command that was used to run the program
    - Ex. `python main.py --package Tap`
- Time
    - The time when the command was run
    - Ex. `Thu Aug 15 00:09:13 2019`
- Git root
    - The root of the git repo containing the code
    - Ex. `/Users/kyleswanson/typed-argument-parsing`
- Git url
    - The url to the git repo, specifically pointing to the current git hash (i.e. the hash of HEAD in the local repo)
    - Ex. `https://github.com/swansonk14/typed-argument-parsing/tree/9e2e69dd353abe247f4305dfd59143245de9dcaa`
- Uncommited changes
    - Whether there are any uncommitted changes in the git repo (i.e. whether the code is different from the code at the above url)
    - Ex. `True` or `False`
    
#### Saving arguments

Tap has a method called `save` which saves all all arguments, along with the reproducibility info, to a JSON file.

```python
"""main.py"""

from tap import Tap

class MyTap(Tap):
    package: str = 'Tap'
    is_cool: bool = True
    stars: int = 5

args = MyTap().parse_args()
args.save('args.json')
```

After running `python main.py`, the file `args.json` will contain:

```
{
    "is_cool": true,
    "package": "Tap",
    "reproducibility": {
        "command_line": "python main.py",
        "git_has_uncommitted_changes": true,
        "git_root": "/Users/kyleswanson/typed-argument-parsing",
        "git_url": "https://github.com/swansonk14/typed-argument-parsing/tree/9e2e69dd353abe247f4305dfd59143245de9dcaa",
        "time": "Thu Aug 15 00:18:31 2019"
    },
    "stars": 5
}
```
