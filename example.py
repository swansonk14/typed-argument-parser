from typing import Optional, Sequence

from typed_argument_parsing import TypedArgumentParser, TypedNamespace


class MyNamespace(TypedNamespace):
    """
    My TypedNamespace.

    Attributes:
    :data_path: Path to data file.
        One that is very important!

        An unusually cool path.
    :embedding_path: Path to embedding file.
    :hidden_size: Hidden size.
    """
    data_path: str
    embedding_path: str = '/home'
    hidden_size: int = 2


class MyArgumentParser(TypedArgumentParser):
    """My TypedArgumentParser."""

    def add_arguments(self) -> None:
        self.add_argument('-dp', '--data_path', required=True)
        self.add_argument('--embedding_path')
        self.add_argument('--hidden_size')

    # TODO: would be nice to get rid of this but seems necessary b/c need to
    # explicitly say MyNamespace as the return type to get click through
    def parse_args(self,
                   args: Optional[Sequence[str]] = None,
                   namespace: Optional[TypedNamespace] = None) -> MyNamespace:
        return super(MyArgumentParser, self).parse_args(args, namespace)


if __name__ == '__main__':
    parser = MyArgumentParser(MyNamespace)
    args = parser.parse_args()

    print(args.data_path)
    print(args.embedding_path)
    print(args.hidden_size)
