import argparse
import importlib.metadata
import os
import os.path as op
import re
import sys

import aocstat.api as api
import aocstat.config as config
import aocstat.format as fmt

# make ANSI colour work on win
os.system("")


def start(args=sys.argv[1:]):
    if not op.exists(api.data_dir):
        os.mkdir(api.data_dir)
    if not op.exists(config.config_dir):
        os.mkdir(config.config_dir)

    parser = argparse.ArgumentParser(
        description="Interact with Advent of Code from your terminal."
    )
    parser.add_argument(
        "subcommand",
        choices=["lb", "purge", "config"],
        help="Subcommand to use. Available options are 'lb' (leaderboard), 'purge' (purge cache), or 'config' (view and edit config values).",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=importlib.metadata.version("aocstat"),
    )
    parser.add_argument("subcommand args", nargs=argparse.REMAINDER)
    args = vars(parser.parse_args(args))
    if args["subcommand"] == "lb":
        _lb(args=args["subcommand args"])
    elif args["subcommand"] == "purge":
        _purge(args=args["subcommand args"])
    elif args["subcommand"] == "config":
        _config(args=args["subcommand args"])


def _lb(args=sys.argv[1:]):
    # TODO: automatically page long output like for puzzle viewing
    parser = argparse.ArgumentParser(
        prog="aocstat lb", description="Interact with Advent of Code leaderboards."
    )

    def year_type(arg):
        if int(arg) >= 2015 and int(arg) <= api.get_most_recent_year():
            return int(arg)
        else:
            raise argparse.ArgumentTypeError(
                "The year must be after 2014, and not in the future."
            )

    parser.add_argument(
        "-y",
        "--year",
        action="store",
        metavar="YEAR",
        type=year_type,
        help="Specify a year other than the most recent event.",
        default=api.get_most_recent_year(),
    )
    parser.add_argument(
        "--no-colour",
        action="store_true",
        help="Disable ANSI colour output.",
    )

    def glob_lb_day_type(arg):
        if re.match(r"^(0?[1-9]|1[0-9]|2[0-5]):[12]$", arg):
            return arg
        else:
            raise argparse.ArgumentTypeError(
                "day:part must be in the form 'd:p' where d is the day and p is the part."
            )

    if api.get_lb_ids():
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
            help="Specify a private leaderboard id. Cannot be used with '-g, --global'",
            default=api.get_lb_ids()[-1],
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
    else:
        parser.add_argument(
            "-d",
            "--day",
            default=None,
            type=glob_lb_day_type,
            dest="global",
            help="A day number in the form ('[1..25]:[1,2]') where the number after the colon denotes which part to view. Will default to the overall leaderboard if not provided.",
        )

    parser.add_argument(
        "-f",
        "--force",
        default=False,
        action="store_true",
        help="Force update leaderboard, even if within the cache ttl. "
        + "Please use responsibly (preferably not at all) and be considerate of others, especially in December!",
    )
    parser.add_argument(
        "-c",
        "--columns",
        default=None,
        const=1,
        type=int,
        action="store",
        nargs="?",
        help="Print the leaderboard in multiple columns with the specified padding.",
    )
    args = vars(parser.parse_args(args))
    if args["global"] is not None:
        if int(args["global"].split(":")[0]) > api.get_most_recent_day(args["year"]):
            parser.error("The day selected is in the future.")
    output = None
    if api.get_lb_ids():
        if args["global"] is False:
            _lb = api.get_priv_lb(
                id=args["id"], yr=args["year"], force_update=args["force"]
            )
            output = fmt.format_priv_lb(*_lb, ansi_on=not args["no_colour"])
        else:
            _lb = api.get_glob_lb(yr=args["year"], day=args["global"])
            output = fmt.format_glob_lb(*_lb, ansi_on=not args["no_colour"])
    else:
        _lb = api.get_glob_lb(yr=args["year"], day=args["global"])
        output = fmt.format_glob_lb(*_lb, ansi_on=not args["no_colour"])
    if args["columns"] is not None:
        output = fmt.columnize(output, args["columns"])
    print(output)


def _purge(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        prog="aocstat purge", description="Purge program cache."
    )
    parser.parse_args(args)
    args = vars(parser.parse_args(args))
    if args:
        parser.error("No arguments allowed with 'purge' subcommand.")
    else:
        api.purge_cache()
        print("Cache purged.")


def _config(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        prog="aocstat config", description="View and edit config values."
    )
    parser.add_argument(
        "subcommand",
        choices=["list", "get", "set", "reset"],
        help="Subcommand to use. Available options are 'list' (list all config values), 'get' (get a config value), or 'set' (edit a config value).",
    )
    parser.add_argument("subcommand args", nargs=argparse.REMAINDER)
    args1 = vars(parser.parse_args(args))
    if args1["subcommand"] == "list":
        if args1["subcommand args"]:
            parser.error("No arguments allowed with 'list' subcommand.")
        else:
            for key in config.DEFAULTS:
                print(f"{key}: {config.get(key)}")
    else:
        parser = argparse.ArgumentParser(
            prog=f"aocstat config {args1["subcommand"]}",
            description="View and edit config values.",
        )
        if args1["subcommand"] == "reset":
            parser.add_argument(
                "-k",
                "--key",
                action="store",
                choices=config.DEFAULTS.keys(),
                help="Key to get or set. If not provided, resets all keys to default values.",
            )
        else:
            parser.add_argument(
                "key",
                action="store",
                choices=config.DEFAULTS.keys(),
                help="Key to get or set.",
            )
            if args1["subcommand"] == "set":
                parser.add_argument(
                    "value",
                    action="store",
                    help="Value to set key to.",
                )
        args2 = vars(parser.parse_args(args1["subcommand args"]))

        if args1["subcommand"] == "get":
            print(config.get(args2["key"]))
        elif args1["subcommand"] == "set":
            try:
                config.set(args2["key"], args2["value"])
            except TypeError:
                raise argparse.ArgumentTypeError(config.TYPE_ERRS[args2["key"]])
        elif args1["subcommand"] == "reset":
            if not args2["key"]:
                for key in config.DEFAULTS:
                    config.reset(key)
            else:
                config.reset(args2["key"])


if __name__ == "__main__":
    start()
