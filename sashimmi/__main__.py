#!/usr/bin/env python3

import argparse
import logging
import os

from .subcommands import get_subcommand, get_subcommands


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable debug logging."
    )
    parser.add_argument(
        "--root",
        default=os.getcwd(),
        help=
        "Search for sashimmi root node from this alternate location instead of current working directory."
    )

    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = True

    for subcommand in get_subcommands():
        subparser = subparsers.add_parser(
            subcommand.name(), help=subcommand.help()
        )
        subcommand.configure_subparser(subparser)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    get_subcommand(args.subcommand).main(args)


if __name__ == "__main__":
    main()
