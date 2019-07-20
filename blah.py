from tap import Tap


class SimpleArgumentParser(Tap):
    """This is a simple argument parser.

    Arguments:
    :first_argument: This is the first argument!
    :second_argument: Here's a second argument. 
    :third_argument: The third argument is super cool.
    """
    first_argument: str
    second_argument: int = 3
    third_argument: float = 6.9


args = SimpleArgumentParser().parse_args()
print(args)
