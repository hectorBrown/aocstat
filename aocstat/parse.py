import argparse
import aocstat.config as config
import aocstat.api as api
import importlib.metadata


def __pz_year_arg(parser):
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
        help="Year of the puzzle.",
        default=None,
    )


def __pz_day_arg(parser):
    def day_type(arg):
        if int(arg) >= 1 and int(arg) <= 25:
            return int(arg)
        else:
            raise argparse.ArgumentTypeError("Day must be between 1 and 25.")

    parser.add_argument(
        "-d",
        "--day",
        action="store",
        type=day_type,
        default=None,
        help="Day of puzzle.",
    )


def __pz_part_arg(parser):
    parser.add_argument(
        "-p",
        "--part",
        action="store",
        type=int,
        default=None,
        help="Part of puzzle.",
    )


def __force_update_arg(parser):
    parser.add_argument(
        "-f",
        "--force",
        default=False,
        action="store_true",
        help="Force update leaderboard, even if within the cache ttl. "
        + "Please use responsibly (preferably not at all) and be considerate of others, especially in December!",
    )


def __no_pager_arg(parser):
    parser.add_argument(
        "--no-pager",
        action="store_true",
        default=False,
        help="Don't use a pager to view the output. Otherwise a pager will be used for output longer than the terminal height.",
    )


def __no_colour_arg(parser):
    parser.add_argument(
        "--no-colour",
        action="store_true",
        help="Disable ANSI colour output.",
    )


def __columns_arg(parser):
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


def parse_base(args):
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

    output = vars(parser.parse_args(args))
    return output


def parse_lb(args):
    parser = argparse.ArgumentParser(
        prog="aocstat lb", description="Interact with Advent of Code leaderboards."
    )
    parser.add_argument(
        "subcommand",
        choices=["priv", "glob", "select"],
        help="Choose whether to interact with private or global leaderboards. Available options are 'priv', 'glob', or 'select'.",
    )
    parser.add_argument("subcommand args", nargs=argparse.REMAINDER)
    output = vars(parser.parse_args(args))
    return output


def parse_select_lb(args):
    parser = argparse.ArgumentParser(
        prog="aocstat lb select",
        description="Select a default private Advent of Code leaderboard.",
    )
    __force_update_arg(parser)
    output = vars(parser.parse_args(args))
    return output


def parse_priv_lb(args):
    parser = argparse.ArgumentParser(
        prog="aocstat lb priv",
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
        help="Specify the year of the event.",
        default=api.get_most_recent_year(),
    )
    __no_pager_arg(parser)

    __no_colour_arg(parser)

    parser.add_argument(
        "--id",
        metavar="ID",
        choices=api.get_lb_ids(),
        type=int,
        help="Specify a private leaderboard id.",
        default=api.get_default_lb_id(),
    )

    __force_update_arg(parser)

    __columns_arg(parser)

    output = vars(parser.parse_args(args))
    return output


def parse_glob_lb(args):
    parser = argparse.ArgumentParser(
        prog="aocstat lb glob",
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
        default=None,
        help="Specify the year of the event.",
    )

    def day_type(arg):
        if int(arg) >= 1 and int(arg) <= 25:
            return int(arg)
        else:
            raise argparse.ArgumentTypeError("Day must be between 1 and 25.")

    parser.add_argument(
        "-d",
        "--day",
        default=None,
        type=day_type,
        help="The day of the event.",
    )

    parser.add_argument(
        "-p",
        "--part",
        default=None,
        type=int,
        help="A part number (either 1 or 2).",
    )

    __no_pager_arg(parser)

    __no_colour_arg(parser)

    __force_update_arg(parser)

    __columns_arg(parser)

    output = vars(parser.parse_args(args))
    output["year"], output["day"], output["part"] = api.get_default_puzzle(
        output["year"], output["day"], output["part"]
    )
    if output["day"] > api.get_most_recent_day(args["year"]):
        parser.error("Day cannot be in the future.")
    if output["year"] >= 2025:
        parser.error("Years 2025 and after don't have global leaderboards.")
    return output


def parse_purge(args):
    parser = argparse.ArgumentParser(
        prog="aocstat purge", description="Purge program cache."
    )
    parser.parse_args(args)
    output = vars(parser.parse_args(args))
    return output


def parse_config(args):
    parser = argparse.ArgumentParser(
        prog="aocstat config", description="View and edit config values."
    )
    parser.add_argument(
        "subcommand",
        choices=["list", "get", "set", "reset"],
        help="Subcommand to use. Available options are 'list' (list all config values), 'get' (get a config value), or 'set' (edit a config value).",
    )
    parser.add_argument("subcommand args", nargs=argparse.REMAINDER)
    output = vars(parser.parse_args(args))
    return output


def parse_config_list(args):
    parser = argparse.ArgumentParser(
        prog="aocstat config list", description="List config values."
    )
    parser.parse_args(args)
    output = vars(parser.parse_args(args))
    return output


def parse_config_get(args):
    parser = argparse.ArgumentParser(
        prog="aocstat config get",
        description="View config values.",
    )
    parser.add_argument(
        "key",
        action="store",
        choices=config.DEFAULTS.keys(),
        help="Key to get.",
    )
    output = vars(parser.parse_args(args))
    return output


def parse_config_set(args):
    parser = argparse.ArgumentParser(
        prog="aocstat config set",
        description="Set config values.",
    )
    parser.add_argument(
        "key",
        action="store",
        choices=config.DEFAULTS.keys(),
        help="Key to set.",
    )
    parser.add_argument(
        "value",
        action="store",
        help="Value to set key to.",
    )
    output = vars(parser.parse_args(args))
    return output


def parse_config_reset(args):
    parser = argparse.ArgumentParser(
        prog="aocstat config reset",
        description="Reset config values to defaults.",
    )
    parser.add_argument(
        "-k",
        "--key",
        action="store",
        choices=config.DEFAULTS.keys(),
        help="Key to get or set. If not provided, resets all keys to default values.",
    )
    output = vars(parser.parse_args(args))
    return output


def parse_pz(args):
    parser = argparse.ArgumentParser(
        prog="aocstat pz", description="Interact with Advent of Code puzzles."
    )
    parser.add_argument(
        "subcommand",
        choices=["view", "input", "submit"],
        help="Subcommand to use. Available options are 'view' (view puzzle instructions), 'input' (get puzzle input), or 'submit' (submit puzzle answer).",
    )
    parser.add_argument("subcommand args", nargs=argparse.REMAINDER)
    output = vars(parser.parse_args(args))
    return output


def parse_pz_view(args):
    parser = argparse.ArgumentParser(
        "aocstat pz view", "View Advent of Code puzzle text."
    )

    __pz_year_arg(parser)
    __pz_day_arg(parser)
    __pz_part_arg(parser)

    parser.add_argument(
        "-w",
        "--width",
        action="store",
        type=int,
        default=80,
        help="Width of the output. Default is 80 characters. Set to 0 for no wrapping.",
    )

    __columns_arg(parser)
    __no_pager_arg(parser)
    __no_colour_arg(parser)

    output = vars(parser.parse_args(args))

    output["set_prog"] = not (
        output["year"] is None and output["day"] is None and output["part"] is None
    )

    output["year"], output["day"], output["part"] = api.get_default_puzzle(
        output["year"], output["day"], output["part"]
    )
    if output["day"] > api.get_most_recent_day(output["year"]):
        parser.error("Day cannot be in the future.")

    if api.get_current_part(output["year"], output["day"]) == 1 and output["part"] == 2:
        parser.error(
            "You have to complete the previous part to interact with this puzzle."
        )
    return output


def parse_pz_input(args):
    parser = argparse.ArgumentParser("aocstat pz view", "Get Advent of Code input.")

    __pz_year_arg(parser)
    __pz_day_arg(parser)
    __pz_part_arg(parser)

    output = vars(parser.parse_args(args))

    output["set_prog"] = not (
        output["year"] is None and output["day"] is None and output["part"] is None
    )
    output["year"], output["day"], output["part"] = api.get_default_puzzle(
        output["year"], output["day"], output["part"]
    )
    if output["day"] > api.get_most_recent_day(output["year"]):
        parser.error("Day cannot be in the future.")

    if api.get_current_part(output["year"], output["day"]) == 1 and output["part"] == 2:
        parser.error(
            "You have to complete the previous part to interact with this puzzle."
        )
    return output


def parse_pz_submit(args):
    parser = argparse.ArgumentParser(
        "aocstat pz submit", "Submit Advent of Code answers."
    )

    __pz_year_arg(parser)
    __pz_day_arg(parser)
    __pz_part_arg(parser)

    parser.add_argument("answer", type=str, help="The answer to submit.")
    parser.add_argument(
        "-a",
        "--auto-wait",
        help="Automatically wait and resubmit if you submitted an answer too recently.",
        action="store_true",
    )

    output = vars(parser.parse_args(args))

    output["set_prog"] = not (
        output["year"] is None and output["day"] is None and output["part"] is None
    )
    output["year"], output["day"], output["part"] = api.get_default_puzzle(
        output["year"], output["day"], output["part"]
    )
    if output["day"] > api.get_most_recent_day(output["year"]):
        parser.error("Day cannot be in the future.")

    if api.get_current_part(output["year"], output["day"]) == 1 and output["part"] == 2:
        parser.error(
            "You have to complete the previous part to interact with this puzzle."
        )

    if api.get_current_part(output["year"], output["day"]) == 2 and output["part"] == 1:
        parser.error("You have already completed part 1 of this puzzle.")

    if api.get_current_part(output["year"], output["day"]) is None:
        parser.error("You have already completed every part of this puzzle.")
    return output
