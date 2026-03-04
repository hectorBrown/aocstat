import time
import subprocess as sp
import os.path as op
import os
import pydoc
import shutil
import sys

import aocstat.api as api
import aocstat.config as config
import aocstat.format as fmt
import aocstat.parse as parse

# make ANSI colour work on win
if sys.platform == "win32":
    sp.run("", shell=True)


def start(args=sys.argv[1:]):
    if not op.exists(api.data_dir):
        os.mkdir(api.data_dir)
    if not op.exists(config.config_dir):
        os.mkdir(config.config_dir)

    args = parse.parse_base(args)

    if args["subcommand"] == "lb":
        _lb(args=args["subcommand args"])
    elif args["subcommand"] == "purge":
        _purge(args=args["subcommand args"])
    elif args["subcommand"] == "config":
        _config(args=args["subcommand args"])
    elif args["subcommand"] == "pz":
        _pz(args=args["subcommand args"])


def _lb(args=sys.argv[1:]):
    args = parse.parse_lb(args)
    if args["subcommand"] == "glob":
        _glob_lb(args["subcommand args"])
    elif args["subcommand"] == "priv":
        _priv_lb(args["subcommand args"])
    else:
        _select_lb(args["subcommand args"])


def _select_lb(args):
    args = parse.parse_select_lb(args)
    lb_ids = api.get_lb_ids()
    lbs = [
        api.get_priv_lb(lb_id, api.get_most_recent_year(), force_update=args["force"])[
            0
        ]
        for lb_id in lb_ids
    ]
    print("Select a private leaderboard to set as default:")
    for local_id, lb in enumerate(lbs):
        print(
            f"{local_id}: {[lb['members'][member]['name'] for member in lb['members']]}"
        )
    valid = False
    selection = None
    while not valid:
        selection = input("Enter the number of the leaderboard you want to select: ")
        try:
            selection = int(selection)
            if selection < 0 or selection >= len(lb_ids) or selection is None:
                raise ValueError()
            else:
                valid = True
        except ValueError:
            print("Invalid selection, please enter a valid number.")
    config.set("default_lb_id", lb_ids[selection])  # type:ignore
    print("Selected leaderboard set as default.")


def _priv_lb(args):
    args = parse.parse_priv_lb(args)
    ids = api.get_lb_ids()
    if ids:
        _lb = api.get_priv_lb(
            id=args["id"], yr=args["year"], force_update=args["force"]
        )
        output = fmt.format_priv_lb(
            *_lb, year=args["year"], ansi_on=not args["no_colour"]
        )
    else:
        output = "You have no private leaderboard to display."

    if args["columns"] is not None:
        output = fmt.columnize(output, args["columns"])
    _dynamic_page(output, args["no_pager"])


def _glob_lb(args):
    args = parse.parse_glob_lb(args)
    _lb = api.get_glob_lb(yr=args["year"], day=args["day"], part=args["part"])
    output = fmt.format_glob_lb(*_lb, ansi_on=not args["no_colour"])

    if args["columns"] is not None:
        output = fmt.columnize(output, args["columns"])
    _dynamic_page(output, args["no_pager"])


def _purge(args=sys.argv[1:]):
    args = parse.parse_purge(args)
    api.purge_cache()
    print("Cache purged.")


def _config(args=sys.argv[1:]):
    args = parse.parse_config(args)
    if args["subcommand"] == "list":
        _config_list(args["subcommand args"])
    elif args["subcommand"] == "get":
        _config_get(args["subcommand args"])
    elif args["subcommand"] == "set":
        _config_set(args["subcommand args"])
    elif args["subcommand"] == "reset":
        _config_reset(args["subcommand args"])


def _config_list(args):
    args = parse.parse_config_list(args)
    for key in config.DEFAULTS:
        print(f"{key}: {config.get(key)}")


def _config_get(args):
    args = parse.parse_config_get(args)
    print(config.get(args["key"]))


def _config_set(args):
    args = parse.parse_config_set(args)
    try:
        config.set(args["key"], args["value"])
    except TypeError:
        print(config.TYPE_ERRS[args["key"]])


def _config_reset(args):
    args = parse.parse_config_reset(args)
    if not args["key"]:
        for key in config.DEFAULTS:
            config.reset(key)
    else:
        config.reset(args["key"])


def _pz(args=sys.argv[1:]):
    args = parse.parse_pz(args)
    if args["subcommand"] == "view":
        _pz_view(args["subcommand args"])
    if args["subcommand"] == "input":
        _pz_input(args["subcommand args"])
    if args["subcommand"] == "ex":
        _pz_example(args["subcommand args"])
    if args["subcommand"] == "submit":
        _pz_submit(args["subcommand args"])


def _pz_example(args):
    args = parse.parse_pz_ex(args)
    example = api.get_puzzle_example(
        year=args["year"], day=args["day"], number=args["number"]
    )
    print(example, end="")


def _pz_view(args):
    args = parse.parse_pz_view(args)
    if args["set_prog"]:
        api.set_prog(args["year"], args["day"], args["part"])
    puzzle = None
    puzzle = api.get_puzzle(yr=args["year"], day=args["day"], part=args["part"])
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
    args = parse.parse_pz_input(args)
    input = api.get_puzzle_input(yr=args["year"], day=args["day"])
    output = input
    print(output, end="")


def _pz_submit(args):
    input_args = args
    args = parse.parse_pz_input(args)
    if args["set_prog"]:
        api.set_prog(args["year"], args["day"], args["part"])

    output = None
    correct, timeout, too_high = api.submit_answer(
        args["year"], args["day"], args["answer"]
    )
    if timeout:
        if args["auto_wait"]:
            print("You submitted an answer too recently.")
            _countdown(timeout)
            print("\nSubmitting answer...")
            _pz_submit(input_args)
            return None
        else:
            print(
                f"You submitted an answer for this puzzle too recently. Please wait before submitting again. You have {fmt.format_time(timeout)} left to wait."
            )
    elif not correct:
        if too_high:
            output = "That's not the right answer. Your answer is too high."
        else:
            output = "That's not the right answer. Your answer is too low."
    elif correct:
        output = "That's the right answer! Congratulations!"
        api.step_progress()

    if output is None:
        raise ValueError("Output is None, something went wrong.")

    print(output)


def _dynamic_page(output, no_pager):
    if len(output.split("\n")) > shutil.get_terminal_size().lines and not no_pager:
        pydoc.pager(fmt.recolour_for_pager(output))
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
