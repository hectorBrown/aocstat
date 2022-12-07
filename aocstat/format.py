import aocstat.api as api


def format_priv_lb(lb):
    """Return a string representing a leaderboard `lb`.

    Args:
        lb (dict): Leaderboard to represent.

    Returns:
        lb_str (str): A 'pretty' string representing the leaderboard.
    """
    res = ""
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
                ("\033[0;92m" if i < api.get_day(int(lb["event"])) else "\033[0;37m")
                + (str(day_labels_1[i]) if not day_labels_1[i] is None else " ")
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
                ("\033[0;92m" if i < api.get_day(int(lb["event"])) else "\033[0;37m")
                + str(day_labels_2[i])
                + " "
                for i in range(25)
            ]
        )
        + "\n"
    )

    # append members row by row
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
            elif day <= api.get_day(int(lb["event"])):
                res += "\033[0;37m* "
            else:
                res += "  "
        res += "  "
        # add names
        user_id = api.get_id()
        res += (
            ("\033[1;96m" if user_id == int(member) else "\033[0;97m")
            + lb["members"][member]["name"]
            + "\n"
        )

    return res
