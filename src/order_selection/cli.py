"""Command line interface that receives a configuration file (issue #15).

Parses a single positional path pointing to a JSON batch configuration file and
passes it to ``batch_runner.run_batch``. All run settings live inside that JSON
file, so no extra command line flags are accepted.
"""

import argparse
from collections.abc import Sequence
from pathlib import Path

from order_selection import batch_runner

# Showing the module invocation in usage lines instead of the __main__.py path
PROGRAM_NAME = "python -m order_selection"


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser accepting only the configuration file path."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Run the batch described by a JSON configuration file.",
    )
    # Accepting a single positional path because every setting belongs in the JSON
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the JSON configuration file.",
    )
    return parser


def parse_config_path(argv: Sequence[str] | None = None) -> Path:
    """Parse command line arguments and return the configuration file path.

    Args:
        argv: Optional argument list; defaults to ``sys.argv[1:]`` when ``None``.

    Returns:
        The configuration file path given as the single positional argument.
    """
    # Delegating parsing and --help formatting to the standard library parser
    parser = build_parser()
    arguments = parser.parse_args(argv)
    return arguments.config


def main(argv: Sequence[str] | None = None) -> None:
    """Run the batch described by the configuration file given as argument.

    Args:
        argv: Optional argument list; defaults to ``sys.argv[1:]`` when ``None``.
    """
    # Resolving the config path from CLI arguments and running every batch combination
    config_path = parse_config_path(argv)
    batch_runner.run_batch(config_path)
