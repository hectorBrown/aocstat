import argparse
import os
import sys

import aocstat.api as api
import aocstat.format as fmt

# make ANSI colour work on win
os.system("")


def start(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Interact with Advent of Code from your terminal."
    )
    parser.add_argument("subcommand", choices=["lb", "purge"])
    parser.add_argument("subcommand_args", nargs=argparse.REMAINDER)
    args = vars(parser.parse_args(args))
    if args["subcommand"] == "lb":
        lb(args=args["subcommand_args"])


def lb(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Interact with Advent of Code leaderboards."
    )
    parser.add_argument(
        "-y",
        "--year",
        action="store",
        metavar="YEAR",
        choices=range(2015, api.get_year() + 1),
        type=int,
        help="Specify a year other than the most recent event.",
    )
    priv_glob = parser.add_mutually_exclusive_group()
    priv_glob.add_argument(
        "--id",
        metavar="ID",
        type=int,
        # TODO: restrict choices to available leaderboards/aliases
        help="Specify a private leaderboard id other than your own. Cannot be used with '-g, --global'",
    )
    priv_glob.add_argument(
        "-g",
        "--global",
        default=False,
        nargs="?",
        metavar="DAY",
        type=int,
        choices=range(1, 26),  # this still allows invalid days
        help="View the global leaderboard. optionally include a day number in the range [1..25]. Cannot be used with '--id'",
    )
    parser.add_argument(
        "-f",
        "--force",
        default=False,
        action="store_true",
        help="Force update leaderboard, even if within the cache ttl. "
        + "Please use responsibly (preferably not at all) and be considerate of others, especially in December!",
    )
    args = vars(parser.parse_args(args))
    if not args["global"]:
        # TODO: read config file to get custom ttl
        _lb = api.get_priv_lb(
            id=args["id"], yr=args["year"], force_update=args["force"]
        )
        print(fmt.format_priv_lb(_lb))


if __name__ == "__main__":
    start()
