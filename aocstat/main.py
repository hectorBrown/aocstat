import argparse
import os
import os.path as op
import re
import sys

import aocstat.api as api
import aocstat.format as fmt

# make ANSI colour work on win
os.system("")


def start(args=sys.argv[1:]):
    if not op.exists(api.data_dir):
        os.mkdir(api.data_dir)
    parser = argparse.ArgumentParser(
        description="Interact with Advent of Code from your terminal."
    )
    parser.add_argument(
        "subcommand",
        choices=["lb", "purge"],
        help="Subcommand to use. Available options are 'lb' (leaderboard) or 'purge' (purge cache).",
    )
    parser.add_argument("subcommand args", nargs=argparse.REMAINDER)
    args = vars(parser.parse_args(args))
    if args["subcommand"] == "lb":
        lb(args=args["subcommand args"])
    elif args["subcommand"] == "purge":
        purge(args=args["subcommand args"])


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

    def lb_id_type(arg):
        lb_ids = api.get_lb_ids()
        if arg in [str(x) for x in lb_ids]:
            return int(arg)
        else:
            raise argparse.ArgumentTypeError(
                f"Invalid leaderboard id '{arg}'. Must be one of {lb_ids}."
            )

    priv_glob.add_argument(
        "--id",
        metavar="ID",
        type=lb_id_type,
        help="Specify a private leaderboard id other than your own. Cannot be used with '-g, --global'",
        # TODO: set default to your lb if exists otherwise alternate
    )

    def glob_lb_day_type(arg):
        if re.match(r"^(0?[1-9]|1[0-9]|2[0-5]):[12]$", arg):
            return arg
        else:
            raise argparse.ArgumentTypeError(
                "day:part must be in the form 'd:p' where d is the day and p is the part."
            )

    priv_glob.add_argument(
        "-g",
        "--global",
        default=False,
        nargs="?",
        metavar="DAY",
        type=glob_lb_day_type,
        help="View the global leaderboard. optionally include a day number in the form ('[1..25]:[1,2]') where the number after the colon denotes which part to view. Cannot be used with '--id'",
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
    if args["global"] is False:
        # TODO: read config file to get custom ttl
        _lb = api.get_priv_lb(
            id=args["id"], yr=args["year"], force_update=args["force"]
        )
        print(fmt.format_priv_lb(_lb))
    else:
        _lb = api.get_glob_lb(yr=args["year"], day=args["global"])
        print(fmt.format_glob_lb(_lb))


def purge(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description="Purge program cache.")
    parser.parse_args(args)
    api.purge_cache()
    print("Cache purged.")


if __name__ == "__main__":
    start()
