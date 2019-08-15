from argparse import ArgumentParser
from tap import Tap


def add_one(num: int) -> int:
    return num + 1


# ----- ArgumentParser -----

parser = ArgumentParser()
parser.add_argument('--rnn', type=str, required=True)
parser.add_argument('--hidden_size', type=int, default=300)
parser.add_argument('--dropout', type=float, default=0.2)


args = parser.parse_args()

print(args.hidden_size)  # no autocomplete, no type inference, no source code navigation

add_one(args.rnn)  # no static type checking


# ----- Tap -----

class MyTap(Tap):
    rnn: str
    hidden_size: int = 300
    dropout: float = 0.2


args = MyTap().parse_args()

print(args.hidden_size)  # autocomplete, type inference, source code navigation

add_one(args.rnn)  # static type checking
