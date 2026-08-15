import pytest

from tap import Tap, to_argv


class ServerArgs(Tap):
    host: str = "localhost"
    verbose: bool = False  # store_true action
    disable_cache: bool = True  # store_false action (TAP uses --disable_cache to set it to False)
    tags: tuple[str, ...] = ()  # store action with nargs="*"

    def configure(self):
        # Explicit positional argument
        self.add_argument("input_files", nargs="*")

        # Explicit append action (requires --header A --header B)
        self.add_argument("--header", action="append")

        # Explicit count action (requires -v -v -v)
        self.add_argument("-v", "--verbosity", action="count", default=0)


def test_to_argv_reconstruction() -> None:
    """Exercise every action type together in one populated namespace round-trip."""
    simulated_input = [
        "--host",
        "0.0.0.0",
        "--tags",
        "web",
        "api",
        "--header",
        "Auth",
        "--header",
        "Accept",
        "-vvv",
        "--disable_cache",
        "--verbose",
        "file1.txt",
        "file2.txt",
    ]

    parsed_args = ServerArgs().parse_args(simulated_input)
    reconstructed_argv = to_argv(parsed_args)

    # Not asserted as exact list equality: option order may change and short
    # flags may become long ones. Reparsing to an equal namespace is what matters.
    reparsed_args = ServerArgs().parse_args(reconstructed_argv)

    assert parsed_args.as_dict() == reparsed_args.as_dict(), "The reconstructed argv did not produce the same Namespace."


class PositionalArgs(Tap):
    def configure(self):
        self.add_argument("input_files", nargs="*")


def test_to_argv_positional_starting_with_dash() -> None:
    """A positional value that looks like a flag must round-trip via a "--" separator."""
    parsed_args = PositionalArgs().parse_args(["--", "-weird.txt"])

    reconstructed_argv = to_argv(parsed_args)
    assert "--" in reconstructed_argv

    reparsed_args = PositionalArgs().parse_args(reconstructed_argv)
    assert parsed_args.as_dict() == reparsed_args.as_dict()


class SetArgs(Tap):
    tags: set[str]

    def configure(self):
        self.add_argument("--tags", default=set())


def test_to_argv_set_field() -> None:
    """Tap boxes multi-value fields as list, tuple, or set."""
    parsed_args = SetArgs().parse_args(["--tags", "web", "api"])

    reconstructed_argv = to_argv(parsed_args)
    reparsed_args = SetArgs().parse_args(reconstructed_argv)

    assert parsed_args.as_dict() == reparsed_args.as_dict()


class StoreConstArgs(Tap):
    def configure(self):
        self.add_argument("--mode", action="store_const", const="fast", default="slow")


def test_to_argv_unsupported_action_raises() -> None:
    """Action types without explicit support must fail loudly, not drop the value."""
    parsed_args = StoreConstArgs().parse_args(["--mode"])

    with pytest.raises(NotImplementedError):
        to_argv(parsed_args)
