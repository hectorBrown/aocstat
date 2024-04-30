import math
import re
import shutil
import time

import aocstat.api as api


def format_priv_lb(lb, cached):
    """Return a string representing a leaderboard `lb`.

    Args:
        lb (dict): Leaderboard to represent.

    Returns:
        lb_str (str): A 'pretty' string representing the leaderboard.
    """
    res = ""
    if cached:
        res += f"\033[0;37mLeaderboard cached at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cached))}\n"
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
                    "\033[0;92m"
                    if i < api.get_most_recent_day(int(lb["event"]))
                    else "\033[0;37m"
                )
                + (str(day_labels_1[i]) if day_labels_1[i] is not None else " ")
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
                (
                    "\033[0;92m"
                    if i < api.get_most_recent_day(int(lb["event"]))
                    else "\033[0;37m"
                )
                + str(day_labels_2[i])
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
            "\033[0;97m"
            + " " * (rank_offset - len(str(i + 1)))
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
                    res += "\033[1;93m* "
                else:
                    res += "\033[1;94m* "
            elif day <= api.get_most_recent_day(int(lb["event"])):
                res += "\033[1;90m* "
            else:
                res += "  "
        res += "  "
        # add names
        res += (
            ("\033[1;96m" if user_id == int(member) else "\033[0;97m")
            + lb["members"][member]["name"]
            + "\n"
        )

    return res


def format_glob_lb(lb, cached):
    """Return a string representing a global leaderboard `lb`.

    Args:
        lb (dict): Leaderboard to represent.
        cached (int | bool): Unix timestamp of the last time the leaderboard was cached. False if not cached.

    Returns:
        lb_str (str): A 'pretty' string representing the leaderboard.
    """

    res = ""
    if cached:
        res += f"\033[0;37mLeaderboard cached at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cached))}\n"
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
            else "\033[0;37m" + entry["time"] + "\033[0;97m"
        )
        rank = entry["rank"]
        # setup axis
        res += (
            "\033[0;97m"
            + " " * (rank_offset - len(str(rank)))
            + str(rank)
            + ") "
            + " " * (score_offset - len(str(score)))
            + score
            + "  "
        )
        # add name
        colour = None
        if user_id == member:
            colour = "\033[1;96m"
        elif entry["anon"]:
            colour = "\033[0;37m"
        else:
            colour = "\033[0;32m"

        res += colour + entry["name"].strip() + "\n"

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
