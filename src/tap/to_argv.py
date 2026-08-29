import argparse

from tap import Tap


def _stringify(value: object) -> list[str]:
    # Tap boxes multi-value fields as list, tuple, or set (see tap.tap.BOXED_COLLECTION_TYPES).
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def to_argv(args: Tap) -> list[str]:
    """Reconstruct an argv list that reparses to an equivalent namespace.

    Values equal to their action's default are treated as not having been
    passed on the command line, since a parsed Namespace does not record
    which flags were explicitly provided. If a flag was explicitly given a
    value equal to its default, that flag is dropped from the result.
    """
    argv: list[str] = []
    positional_argv: list[str] = []

    for action in args._actions:
        # The help action's default is argparse.SUPPRESS, so `args` has no
        # `help` attribute; the getattr below would raise if not skipped here.
        if isinstance(action, argparse._HelpAction):
            continue

        value = getattr(args, action.dest)

        # A value equal to the default is treated as unset (see docstring).
        if value == action.default:
            continue

        # No option strings means this is a positional argument.
        if not action.option_strings:
            positional_argv.extend(_stringify(value))
            continue

        # Prefer the longest option string for readability (e.g. '--host' over '-h').
        flag = max(action.option_strings, key=len)

        match action:
            case argparse._StoreTrueAction() | argparse._StoreFalseAction():
                argv.append(flag)

            case argparse._CountAction():
                # The count accumulates from a possibly-None default; subtract
                # it to get how many times the flag needs to be repeated.
                count = value - (action.default or 0)
                argv.extend([flag] * count)

            case argparse._AppendAction():
                # Repeats the flag once per item (e.g. --header A --header B).
                for item in value:
                    argv.extend([flag, str(item)])

            case argparse._StoreAction():
                # Single value, or nargs list (e.g. --tags A B).
                argv.append(flag)
                argv.extend(_stringify(value))

            case _:
                raise NotImplementedError(f"Unsupported argparse action type for {flag!r}: {type(action).__name__}")

    # A "--" separator guards against positional values that look like
    # options (e.g. a filename starting with "-").
    if positional_argv:
        argv.append("--")
        argv.extend(positional_argv)
    return argv
