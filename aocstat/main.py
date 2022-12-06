import argparse
import sys


def start(args=sys.argv):
    args = args[1:]
    parser = argparse.ArgumentParser(
        description="Interact with Advent of Code from your terminal."
    )
    parser.add_argument("subcommand", choices=["lb", "purge"])
    parser.add_argument("subcommand_args", nargs=argparse.REMAINDER)
    args = vars(parser.parse_args(args))
    if args["subcommand"] == "lb":
        lb(args=args["subcommand_args"])


def lb(args=sys.argv):
    parser = argparse.ArgumentParser(
        description="Access and modify public and private Advent of Code leaderboards."
    )
    parser.add_argument(
        "-y",
        "--year",
        nargs=1,
        metavar="YEAR",
        help="Specify a year other than the most recent event.",
    )
    priv_glob = parser.add_mutually_exclusive_group()
    priv_glob.add_argument(
        "--id",
        metavar="ID",
        help="Specify a private leaderboard id other than your own. Cannot be used with '-g, --global'",
    )
    priv_glob.add_argument(
        "-g",
        "--global",
        default=False,
        nargs="?",
        metavar="DAY",
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
    print(args)


if __name__ == "__main__":
    start()
