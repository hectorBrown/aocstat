import argparse
import time
import importlib.metadata
import subprocess as sp
import os.path as op
import os
import pydoc
import shutil
import sys

import aocstat.api as api
import aocstat.config as config
import aocstat.format as fmt

# make ANSI colour work on win
if sys.platform == "win32":
    sp.run("", shell=True)


def start(args=sys.argv[1:]):
    # TODO: day > 12 is invalid for years 2025 and after
    if not op.exists(api.data_dir):
        os.mkdir(api.data_dir)
    if not op.exists(config.config_dir):
        os.mkdir(config.config_dir)

    parser = argparse.ArgumentParser(
        description="Interact with Advent of Code from your terminal."
    )
    parser.add_argument(
        "subcommand",
        choices=["lb", "purge", "config", "pz"],
        help="Subcommand to use. Available options are 'lb' (leaderboard), 'purge' (purge cache), 'config' (view and edit config values), or 'pz' (interact with the puzzles).",
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
    elif args["subcommand"] == "pz":
        _pz(args=args["subcommand args"])


def _lb(args=sys.argv[1:]):
    # TODO: add leaderboard selection
    parser = argparse.ArgumentParser(
        prog="aocstat lb", description="Interact with Advent of Code leaderboards."
    )
    parser.add_argument(
        "subcommand",
        choices=["priv", "glob"],
        help="Choose whether to interact with private or global leaderboards. Available options are 'priv' and 'glob'.",
    )
    parser.add_argument("subcommand args", nargs=argparse.REMAINDER)
    args = vars(parser.parse_args(args))
    if args["subcommand"] == "global":
        _glob_lb(args["subcommand args"])
    else:
        _priv_lb(args["subcommand args"])


def _priv_lb(args):
    parser = argparse.ArgumentParser(
        prog="aocstat lb",
        description="Interact with private Advent of Code leaderboards.",
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
        "--no-pager",
        action="store_true",
        default=False,
        help="Use a pager to view the output. Defaults to on for output longer than the terminal height (except for displaying input).",
    )
    parser.add_argument(
        "--no-colour",
        action="store_true",
        help="Disable ANSI colour output.",
    )

    parser.add_argument(
        "--id",
        metavar="ID",
        choices=api.get_lb_ids(),
        type=int,
        help="Specify a private leaderboard id.",
        default=api.get_default_lb_id(),
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
    ids = api.get_lb_ids()
    if ids:
        _lb = api.get_priv_lb(
            id=args["id"], yr=args["year"], force_update=args["force"]
        )
        output = fmt.format_priv_lb(*_lb, ansi_on=not args["no_colour"])
    else:
        output = "You have no private leaderboard to display."

    if args["columns"] is not None:
        output = fmt.columnize(output, args["columns"])
    _dynamic_page(output, args["no_pager"])


def _glob_lb(args):
    parser = argparse.ArgumentParser(
        prog="aocstat lb",
        description="Interact with the global Advent of Code leaderboards.",
    )

    def year_type(arg):
        if int(arg) >= 2015 and int(arg) < 2025:
            return int(arg)
        else:
            raise argparse.ArgumentTypeError(
                "The year must be after 2014, and before 2025."
            )

    parser.add_argument(
        "-y",
        "--year",
        action="store",
        metavar="YEAR",
        type=year_type,
        help="Specify a year other than the most recent event.",
        default=2024,
    )

    parser.add_argument(
        "-d",
        "--day",
        default=1,
        choices=range(1, 26),
        type=int,
        help="A day number in the form ('[1..25]:[1,2]'), will default to 1.",
    )

    parser.add_argument(
        "-p",
        "--part",
        default=1,
        choices=range(1, 3),
        type=int,
        help="A part number (either 1 or 2), will default to 1.",
    )

    parser.add_argument(
        "--no-pager",
        action="store_true",
        default=False,
        help="Use a pager to view the output. Defaults to on for output longer than the terminal height (except for displaying input).",
    )
    parser.add_argument(
        "--no-colour",
        action="store_true",
        help="Disable ANSI colour output.",
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
    _lb = api.get_glob_lb(yr=args["year"], day=args["day"], part=args["part"])
    output = fmt.format_glob_lb(*_lb, ansi_on=not args["no_colour"])

    if args["columns"] is not None:
        output = fmt.columnize(output, args["columns"])
    _dynamic_page(output, args["no_pager"])


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
            prog=f"aocstat config {args1['subcommand']}",
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


def _puzzle_parser(subcommand):
    parser = argparse.ArgumentParser(
        f"aocstat pz {subcommand}", "Interact with Advent of Code puzzles."
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
        type=year_type,
        help="Year of puzzle. Default is the most recent year.",
        default=api.get_most_recent_year(),
    )

    parser.add_argument(
        "-d",
        "--day",
        action="store",
        type=int,
        default=None,
        help="Day of puzzle. Default is the current day.",
    )
    parser.add_argument(
        "-p",
        "--part",
        action="store",
        choices=[1, 2],
        type=int,
        default=1,
        help="Part of puzzle. Default is 1.",
    )

    if subcommand == "submit":
        parser.add_argument(
            "answer",
            type=str,
        )
        parser.add_argument(
            "-a",
            "--auto-wait",
            help="Automatically wait and resubmit if you submitted an answer too recently.",
            action="store_true",
        )
    elif subcommand == "view":
        parser.add_argument(
            "-w",
            "--width",
            action="store",
            type=int,
            default=80,
            help="Width of the output. Default is 80 characters. Set to 0 for no wrapping.",
        )
        parser.add_argument(
            "-c",
            "--columns",
            default=None,
            const=1,
            type=int,
            action="store",
            nargs="?",
            help="Print the output in multiple columns with the specified padding.",
        )
        parser.add_argument(
            "--no-pager",
            action="store_true",
            default=False,
            help="Use a pager to view the output. Defaults to on for output longer than the terminal height (except for displaying input).",
        )
        parser.add_argument(
            "--no-colour",
            action="store_true",
            help="Disable ANSI colour output.",
        )
    return parser


def _pz(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        prog="aocstat pz", description="Interact with Advent of Code puzzles."
    )
    parser.add_argument(
        "subcommand",
        choices=["view", "input", "submit"],
        help="Subcommand to use. Available options are 'view' (view puzzle instructions), 'input' (get puzzle input), or 'submit' (submit puzzle answer).",
    )
    parser.add_argument("subcommand args", nargs=argparse.REMAINDER)
    args = vars(parser.parse_args(args))
    if args["subcommand"] == "view":
        _pz_view(args["subcommand args"])
    if args["subcommand"] == "input":
        _pz_input(args["subcommand args"])
    if args["subcommand"] == "submit":
        _pz_submit(args["subcommand args"])


def _pz_view(args):
    parser = _puzzle_parser("view")
    args = vars(parser.parse_args(args))
    if args["day"] is not None and args["day"] > api.get_most_recent_day(args["year"]):
        parser.error("Day cannot be in the future.")
    if args["day"] is None:
        args["day"] = api.get_most_recent_day(args["year"])
    puzzle = None
    try:
        puzzle = api.get_puzzle(yr=args["year"], day=args["day"], part=args["part"])
    except ValueError:
        parser.error("The puzzle you are trying to view is not available to you yet.")
    if puzzle is None:
        parser.error("You have to complete the previous part to view this puzzle.")
    output = fmt.format_puzzle(
        puzzle,
        args["day"],
        args["year"],
        args["part"],
        ansi_on=not args["no_colour"],
    )
    if args["width"] > 0:
        output = fmt.wrap_text(output, args["width"])
    if args["columns"] is not None:
        output = fmt.columnize(output, args["columns"])

    _dynamic_page(output, args["no_pager"])


def _pz_input(args):
    parser = _puzzle_parser("input")
    args = vars(parser.parse_args(args))
    if args["day"] is not None and args["day"] > api.get_most_recent_day(args["year"]):
        parser.error("Day cannot be in the future.")
    if args["day"] is None:
        args["day"] = api.get_most_recent_day(args["year"])
    input = api.get_input(yr=args["year"], day=args["day"])
    output = input
    print(output, end="")


def _pz_submit(args):
    parser = _puzzle_parser("submit")
    input_args = args
    args = vars(parser.parse_args(args))
    if args["day"] is not None and args["day"] > api.get_most_recent_day(args["year"]):
        parser.error("Day cannot be in the future.")
    if args["day"] is None:
        args["day"] = api.get_most_recent_day(args["year"])

    output = None
    correct, timeout, too_high = api.submit_answer(
        args["year"], args["day"], args["answer"]
    )
    if correct is None:
        parser.error("You have completed every part for this day.")
    elif timeout:
        if args["auto_wait"]:
            print("You submitted an answer too recently.")
            _countdown(timeout)
            print("\nSubmitting answer...")
            _pz_submit(input_args)
            return None
        else:
            parser.error(
                f"You submitted an answer for this puzzle too recently. Please wait before submitting again. You have {fmt.format_time(timeout)} left to wait."
            )
    elif not correct:
        if too_high:
            output = "That's not the right answer. Your answer is too high."
        else:
            output = "That's not the right answer. Your answer is too low."
    elif correct:
        output = "That's the right answer! Congratulations!"

    if output is None:
        raise ValueError("Output is None, something went wrong.")

    print(output)


def _dynamic_page(output, no_pager):
    if len(output.split("\n")) > shutil.get_terminal_size().lines and not no_pager:
        pydoc.pager(output)
    else:
        print(output)


def _countdown(seconds):
    max_len = len(f"Waiting {fmt.format_time(seconds)}")
    for i in range(seconds, 0, -1):
        output = f"Waiting {fmt.format_time(i)}"
        if len(output) < max_len:
            output += " " * (max_len - len(output))

        print(f"{output}\r", end="", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    start()
