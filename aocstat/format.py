import re
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


def format_glob_lb(lb):
    # TODO: dynamic columns
    # TODO: display time cached when cached
    if lb["day"] is None:
        res = "\n"
        members = sorted(
            lb["members"].keys(),
            key=lambda x: lb["members"][x]["total_score"],
            reverse=True,
        )

        rank_offset = len(str(lb["members"][members[-1]]["rank"]))
        score_offset = len(str(lb["members"][members[0]]["total_score"]))

        # append members row by row
        user_id = api.get_user_id()
        for member in members:
            score = lb["members"][member]["total_score"]
            rank = lb["members"][member]["rank"]
            # setup axis
            res += (
                "\033[0;97m"
                + " " * (rank_offset - len(str(rank)))
                + str(rank)
                + ") "
                + " " * (score_offset - len(str(score)))
                + str(score)
                + "  "
            )
            # add name
            colour = None
            if user_id == member:
                colour = "\033[1;96m"
            elif bool(
                re.search(r"\(anonymous user #\d+\)", lb["members"][member]["name"])
            ):
                colour = "\033[0;37m"
            else:
                colour = "\033[0;32m"

            res += colour + lb["members"][member]["name"] + "\n"

        return res
