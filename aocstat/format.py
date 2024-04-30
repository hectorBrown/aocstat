import math
import re
import shutil
import time

import aocstat.api as api

ANSI_COLOURS = {
    "grey": "\033[0;37m",
    "bright_green": "\033[1;92m",
    "bright_yellow": "\033[1;93m",
    "bright_blue": "\033[1;94m",
    "bright_grey": "\033[1;90m",
    "bright_cyan": "\033[1;96m",
    "bright_white": "\033[1;97m",
    "green": "\033[0;32m",
}


def _colour(text, colour, ansi_on, alt_text=None):
    return (
        (ANSI_COLOURS[colour] + text + "\033[0;97m")
        if ansi_on
        else (text if alt_text is None else alt_text)
    )


# TODO: maybe add aoc++ and sponsor tags to the leaderboards?


def format_priv_lb(lb, cached, ansi_on):
    """Return a string representing a leaderboard `lb`.

    Args:
        lb (dict): Leaderboard to represent.
        cached (int | bool): Unix timestamp of the last time the leaderboard was cached. False if not cached.
        ansi_on (bool): Whether to use ANSI colour codes.

    Returns:
        lb_str (str): A 'pretty' string representing the leaderboard.
    """
    res = ""
    if cached:
        res += _colour(
            f"Leaderboard cached at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cached))}\n",
            "grey",
            ansi_on,
        )
    res += "\n"
    # TODO: allow ordering selection

    # establish left offset from numbering digits & score digits
    members = sorted(
        lb["members"].keys(),
        key=lambda x: lb["members"][x]["local_score"],
        reverse=True,
    )

    rank_offset = len(str(len(members)))
    score_offset = len(str(lb["members"][members[0]]["local_score"]))
    l_offset = rank_offset + 2 + score_offset + 1

    # append the '11111122222' line
    day_labels_1 = [None] * 9 + [1] * 10 + [2] * 6
    res += (
        " " * (l_offset + 1)
        + "".join(
            [
                (
                    _colour(
                        str(day_labels_1[i]),
                        (
                            "bright_green"
                            if i < api.get_most_recent_day(int(lb["event"]))
                            else "grey"
                        ),
                        ansi_on,
                    )
                    if day_labels_1[i] is not None
                    else " "
                )
                + " "
                for i in range(25)
            ]
        )
        + "\n"
    )

    # append the '123456...' line
    day_labels_2 = (
        [i for i in range(1, 10)] + [i for i in range(10)] + [i for i in range(6)]
    )
    res += (
        " " * (l_offset + 1)
        + "".join(
            [
                _colour(
                    str(day_labels_2[i]),
                    (
                        "bright_green"
                        if i < api.get_most_recent_day(int(lb["event"]))
                        else "grey"
                    ),
                    ansi_on,
                )
                + " "
                for i in range(25)
            ]
        )
        + "\n"
    )

    # append members row by row
    user_id = api.get_user_id()
    for i, member in enumerate(members):
        score = lb["members"][member]["local_score"]
        # setup axis
        res += (
            " " * (rank_offset - len(str(i + 1)))
            + str(i + 1)
            + ") "
            + " " * (score_offset - len(str(score)))
            + str(score)
            + "  "
        )
        # add stars
        completion = lb["members"][member]["completion_day_level"]
        for day in range(1, 26):
            if str(day) in completion:
                if str("2") in completion[str(day)]:
                    res += _colour("* ", "bright_yellow", ansi_on)
                else:
                    res += _colour("* ", "bright_blue", ansi_on, alt_text="- ")
            elif day <= api.get_most_recent_day(int(lb["event"])):
                res += _colour("* ", "bright_grey", ansi_on, alt_text=". ")
            else:
                res += "  "
        res += "  "
        # add names
        res += (
            +_colour(
                lb["members"][member]["name"],
                "bright_cyan" if user_id == int(member) else "bright_white",
                ansi_on,
            )
            + "\n"
        )

    return res


def format_glob_lb(lb, cached, ansi_on):
    """Return a string representing a global leaderboard `lb`.

    Args:
        lb (dict): Leaderboard to represent.
        cached (int | bool): Unix timestamp of the last time the leaderboard was cached. False if not cached.
        ansi_on (bool): Whether to use ANSI colour codes.

    Returns:
        lb_str (str): A 'pretty' string representing the leaderboard.
    """

    res = ""
    if cached:
        res += _colour(
            f"Leaderboard cached at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cached))}\n",
            "grey",
            ansi_on,
        )
    res += "\n"
    members = sorted(
        lb["members"].keys(),
        key=lambda x: (
            lb["members"][x]["total_score"]
            if lb["day"] is None
            else 100 - lb["members"][x]["rank"]
        ),
        reverse=True,
    )

    rank_offset = len(str(lb["members"][members[-1]]["rank"]))
    score_offset = len(str(lb["members"][members[0]]["total_score"]))

    # append members row by row
    user_id = api.get_user_id()
    for member in members:
        entry = lb["members"][member]
        score = (
            str(entry["total_score"])
            if lb["day"] is None
            else _colour(entry["time"], "grey", ansi_on)
        )
        rank = entry["rank"]
        # setup axis
        res += (
            " " * (rank_offset - len(str(rank)))
            + str(rank)
            + ") "
            + " " * (score_offset - len(str(score)))
            + score
            + "  "
        )
        # add name
        res += (
            _colour(
                entry["name"].strip(),
                (
                    "bright_cyan"
                    if user_id == member
                    else ("grey" if entry["anon"] else "green")
                ),
                ansi_on,
            )
            + "\n"
        )

    return res


def _term_len(text):
    return len(re.sub(r"\033\[[0-9;]*m", "", text))


def columnize(text, padding):
    """Return a string with columns of text automatically aligned with terminal width.

    Args:
        text (str): Text to columnize.
        padding (int): Padding between columns.

    Returns:
        col_text (str): Columnized text.
    """
    width = shutil.get_terminal_size().columns
    width = 200
    lines = [x for x in text.split("\n") if x != ""]
    col_width = max([_term_len(line) for line in lines]) + padding
    no_cols = width // col_width
    if no_cols == 0:
        no_cols = 1

    col_text = ""
    for i in range(0, math.ceil(len(lines) / no_cols)):
        for j in range(i, len(lines), math.ceil(len(lines) / no_cols)):
            col_text += lines[j] + " " * (col_width - _term_len(lines[j]))
        col_text += "\n"

    return col_text
