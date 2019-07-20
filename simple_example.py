"""simple_example.py"""


# ---------- argparse ----------

#
# from argparse import ArgumentParser
#
# parser = ArgumentParser()
# parser.add_argument('--name', type=str, required=True,
#                     help='Your first name only please.')
# parser.add_argument('--language', type=str,
#                     help='The programming language of the package.')
# parser.add_argument('--package', type=str, default='Tap',
#                     help='The name of the Python package to rate.')
# parser.add_argument('--stars', type=int, required=True,
#                     help='The number of stars to give the package.')
# parser.add_argument('--max_stars', type=int, default=5,
#                     help='The maximum number of stars a package can receive.')
# args = parser.parse_args()
#
# print(f'My name is {args.name} and I give the {args.language} package '
#       f'{args.package} {args.stars}/{args.max_stars} stars!')
#

# ---------- Tap ----------


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
