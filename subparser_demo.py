from typing import Union

from tap import Tap


class A(Tap):
    foo: int


class B(Tap):
    foo: str = '2'


class C(Tap):
    bar: int = 3

    _sub_parsers = [A, B]


args: Union[A, B, C] = C().parse_args()
print(f'{args.bar=}')
print(f'{args.foo=}')
