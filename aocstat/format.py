def format_priv_lb(lb):
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
    res += " " * (l_offset + 9) + "1" * 10 + "2" * 6 + "\n"
    # append the '123456...' line
    res += (
        " " * (l_offset)
        + "".join(
            [str(i) for i in range(1, 10)]
            + [str(i) for i in range(10)]
            + [str(i) for i in range(6)]
        )
        + "\n"
    )

    for i, member in enumerate(members):
        score = lb["members"][member]["local_score"]
        # setup axis
        res += (
            " " * (rank_offset - len(str(i + 1)))
            + str(i + 1)
            + ") "
            + " " * (score_offset - len(str(score)))
            + str(score)
            + " "
        )
        # add stars
        completion = lb["members"][member]["completion_day_level"]
        for day in range(1, 26):
            if str(day) in completion:
                if str("2") in completion[str(day)]:
                    res += "*"
                else:
                    res += "."
            else:
                res += " "
        res += "  "
        # add names
        res += lb["members"][member]["name"] + "\n"

    print(res)
    # append members row by row
