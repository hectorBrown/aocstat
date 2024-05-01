import datetime as dt
import json
import os
import os.path as op
import pickle
import re
import time
import typing
from datetime import timezone

import appdirs as ad
import requests as rq
from bs4 import BeautifulSoup, NavigableString, Tag
from selenium import webdriver
from selenium.common.exceptions import (StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import aocstat.config as config

data_dir = ad.user_data_dir(appname="aocstat", appauthor=False)


def get_cookie(cache_invalid=False):
    """Gets session cookie from cache if present and not marked invalid. Authenticates and caches otherwise.

    Args:
        cache_invalid (bool, optional): Force authentication by setting to `True`. Defaults to False.

    Returns:
        cookie (str): Session cookie.
    """
    if op.exists(f"{data_dir}/cookie") and not cache_invalid:
        with open(f"{data_dir}/cookie", "rb") as f:
            return pickle.load(f)
    else:
        # get cookie with selenium
        print(
            "Please select a browser to use for authentication (must be one you have installed already):\n"
            + "1) Firefox (default)\n"
            + "2) Chrome\n"
            + "3) Edge\n"
            + "4) Internet Explorer\n"
            + "5) Safari\n"
            + "6) 'I'll do it myself'"
        )
        valid_browser = False
        selection = None
        while not valid_browser:
            selection = input("Selection ([1],2,3,4,5,6): ").strip()
            if selection in [""] + [str(x) for x in range(1, 7)]:
                valid_browser = True
            else:
                print(f"'{selection}' isn't a valid selection.")

        cookie = None
        if not selection == "6":
            wd = None
            input("Please press ENTER to open a web browser... ")
            # TODO: stop these from creating logs wherever you auth
            try:
                if selection in ["1", ""]:
                    wd = webdriver.Firefox()
                elif selection == "2":
                    wd = webdriver.Chrome()
                elif selection == "3":
                    wd = webdriver.Edge()
                elif selection == "4":
                    wd = webdriver.Ie()
                elif selection == "5":
                    wd = webdriver.Safari()
            except Exception:
                print(
                    "\nYou don't have a driver installed for that browser, please try again.\n"
                )
                return get_cookie(cache_invalid=cache_invalid)

            wd.get("https://adventofcode.com/2022/auth/login")  # pyright: ignore
            print("\nPlease authenticate yourself with one of the methods given.")

            def logged_in(wd):
                try:
                    links = wd.find_elements(By.TAG_NAME, "a")
                    return "[Log Out]" in [link.text for link in links]
                except StaleElementReferenceException:
                    return False

            try:
                WebDriverWait(wd, timeout=1000, poll_frequency=0.5).until(logged_in)
            except TimeoutException:
                print("\nTimed out waiting for authentication.\n")
                wd.quit()  # pyright: ignore

            cookie = wd.get_cookie("session")["value"]  # pyright: ignore
            wd.quit()  # pyright: ignore
            print("\nAuthenticated.")
        else:
            print(
                "\nBrave!\n"
                + "1) Navigate to 'https://adventofcode.com/2022/auth/login'.\n"
                + "2) Authenticate if necessary.\n"
                + "3) Open the network tools in your browser, refresh the page and examine the GET request for cookies.\n"
                + "4) Copy everything after 'session=' into the field below."
            )
            cookie = input("session=").strip()
            print("\nSaved.")

        with open(f"{data_dir}/cookie", "wb") as f:
            pickle.dump(cookie, f)
        return cookie


def get_most_recent_year():
    """Returns the year of the most recent AOC event.

    Returns:
        year (int): The year of the most recent AOC event.
    """
    today = dt.date.today()
    return today.year if today.month == 12 else today.year - 1


def get_most_recent_day(year):
    """Get the active (i.e. most recently released) day for a given year.

    Args:
        year (int): The year of interest.

    Raises:
        ValueError: If the event in `year` hasn't begun yet.

    Returns:
        day (int): The most recently released day for `year`.
    """
    today = dt.date.today()
    if (today.year == year and today.month != 12) or year > today.year:
        raise ValueError(
            "You are trying to get the active day for an event that hasn't happened yet."
        )
    elif today.year == year:
        return (
            (today.day if dt.datetime.now(timezone.utc).hour >= 5 else today.day - 1)
            if today.day <= 25
            else 25
        )
    else:
        return 25


def get_user_id():
    """Gets user id from cache unless it doesn't exist yet, otherwise makes a request.

    Returns:
        id (int): User id.
    """
    if op.exists(f"{data_dir}/id"):
        with open(f"{data_dir}/id", "rb") as f:
            return pickle.load(f)

    cookie = get_cookie()
    req = rq.get(
        f"https://adventofcode.com/{get_most_recent_year()}/settings",
        cookies={"session": cookie},
    )
    soup = BeautifulSoup(req.content, "html.parser")
    id = int(
        typing.cast(
            NavigableString, soup.find(string=re.compile(r"\(anonymous user #(\d+)\)"))
        ).split("#")[1][:-1]
    )
    with open(f"{data_dir}/id", "wb") as f:
        pickle.dump(id, f)
    return id


def get_priv_lb(id, yr, force_update=False):
    """Gets a private board, from cache as long as cache was obtained `< ttl` ago.

    Args:
        id (int): Board id.
        yr (int): Year of the event.
        force_update (bool): Skip cache regardless of ttl and get board from server. Defaults to False.
        ttl (int): Cache ttl. Defaults to 900.

    Returns:
        board (dict): Raw leaderboard data.
        cached (bool | float): Whether the board was cached or not (i.e. if it was obtained from the server or not). If it was cached, the time it was cached is returned.
    """

    if op.exists(f"{data_dir}/lb_{yr}_{id}") and not force_update:
        cached_lb = None
        with open(f"{data_dir}/lb_{yr}_{id}", "rb") as f:
            cached_lb = pickle.load(f)
        if time.time() - cached_lb["time"] <= config.get("ttl"):
            return (json.loads(cached_lb["content"]), cached_lb["time"])
        elif not connected():
            return (json.loads(cached_lb["content"]), cached_lb["time"])

    cookie = get_cookie()
    lb = rq.get(
        f"https://adventofcode.com/{yr}/leaderboard/private/view/{id}.json",
        cookies={"session": cookie},
    )
    # i.e. is HTML
    if lb.content[0] == "<":
        cookie = get_cookie(cache_invalid=True)
        lb = rq.get(
            f"https://adventofcode.com/{yr}/leaderboard/private/view/{id}.json",
            cookies={"session": cookie},
        )
    with open(f"{data_dir}/lb_{yr}_{id}", "wb") as f:
        lb_tocache = {
            "time": time.time(),
            "content": lb.content,
        }
        pickle.dump(lb_tocache, f)

    return (json.loads(lb.content), False)


def _parse_leaderboard_entry(entry_soup, last_pos):
    entry = {}

    lb_pos = entry_soup.find("span", {"class": "leaderboard-position"})
    if lb_pos is not None:
        pos = int(re.findall(r"\d*\)", lb_pos.contents[0])[0][:-1])
        entry["rank"] = pos
        last_pos = pos
    else:
        # this happens if the user has the same score as the previous user
        entry["rank"] = last_pos

    total_score = entry_soup.find("span", {"class": "leaderboard-totalscore"})
    entry["total_score"] = (
        int(total_score.contents[0]) if total_score is not None else None
    )

    # first we check to see if they have a linked github
    name_link = entry_soup.find(
        "a", {"href": re.compile(r"^https:\/\/(github|twitter)\.com\/.+$")}
    )
    anon_name = entry_soup.find("span", {"class": "leaderboard-anon"})
    time = entry_soup.find("span", {"class": "leaderboard-time"})
    if name_link is not None:
        entry["name"] = name_link.contents[-1]
    else:
        # then to see if they are an anonomous user
        if anon_name is not None:
            entry["name"] = anon_name.contents[0]
        else:
            # if they are not their name should be the only filled plaintext element
            entry["name"] = [
                x.strip()
                for x in entry_soup.contents
                if isinstance(x, NavigableString)
                if x.strip() != ""
            ][0]
    # collect some other data
    entry["supporter"] = bool(entry_soup.find("a", {"class": "supporter-badge"}))
    entry["sponsor"] = bool(entry_soup.find("a", {"class": "sponsor-badge"}))
    entry["anon"] = bool(anon_name)
    entry["link"] = name_link.attrs["href"] if name_link is not None else None
    entry["time"] = time.contents[0] if time is not None else None
    return entry, last_pos


def get_glob_lb(yr, day):
    """Gets the global leaderboard, from the internet as long as the user is connected, and caches it. If the user is not connected, the cached leaderboard is returned.

    Args:
        yr (int): Year of the event.
        day (str): Day of the event in the form 'd:p' where d is the day and p is the part.

    Returns:
        lb (dict): Raw leaderboard data.
        cached (bool | float): Whether the board was cached or not (i.e. if it was obtained from the server or not). If it was cached, the time it was cached is returned.
    """
    if op.exists(f"{data_dir}/glb_{yr}_{day}") and not connected():
        cached_lb = None
        with open(f"{data_dir}/glb_{yr}_{day}", "rb") as f:
            cached_lb = pickle.load(f)
            return (json.loads(cached_lb["content"]), cached_lb["time"])

    lb_raw = (
        rq.get(f"https://adventofcode.com/{yr}/leaderboard")
        if day is None
        else rq.get(
            f"https://adventofcode.com/{yr}/leaderboard/day/{day.split(":")[0]}"
        )
    )
    lb_soup = BeautifulSoup(lb_raw.content, "html.parser")

    if day is None:
        entries_soup = lb_soup.find_all("div", {"class": "leaderboard-entry"})
    else:
        split = lb_soup.find(
            "span", {"class": "leaderboard-daydesc-first"}, recursive=True
        ).parent  # pyright: ignore
        entries_soup = [
            x
            for x in (
                split.previous_siblings  # pyright: ignore
                if day.split(":")[1] == "2"
                else split.next_siblings  # pyright: ignore
            )
            if isinstance(x, Tag)
            if "class" in x.attrs
            if "leaderboard-entry" in x.attrs["class"]
        ]

    lb = {"members": {}, "day": day}
    last_pos = None

    for entry_soup in entries_soup:
        id = int(entry_soup.get("data-user-id"))  # pyright: ignore
        lb["members"][id], last_pos = _parse_leaderboard_entry(entry_soup, last_pos)

    lb["day"] = day

    with open(f"{data_dir}/glb_{yr}_{day}", "wb") as f:
        lb_tocache = {
            "time": time.time(),
            "content": json.dumps(lb),
        }
        pickle.dump(lb_tocache, f)

    return (lb, False)


def get_lb_ids(force_update=False):
    """Gets all private leaderboard ids from cache, as long as cache was obtained `< ttl` ago.

    Args:
        force_update (bool, optional): Skip cache regardless of ttl and get board from server. Defaults to False.

    Returns:
        boards (list(int)): List of board ids.
    """
    if op.exists(f"{data_dir}/lb_ids") and not force_update:
        cached_lb_ids = None
        with open(f"{data_dir}/lb_ids", "rb") as f:
            cached_lb_ids = pickle.load(f)
        if time.time() - cached_lb_ids["time"] <= config.get("ttl"):
            return cached_lb_ids["content"]
        elif not connected():
            return cached_lb_ids["content"]

    cookie = get_cookie()
    lbs_raw = rq.get(
        f"https://adventofcode.com/{get_most_recent_year()}/leaderboard/private",
        cookies={"session": cookie},
    )
    lbs_soup = BeautifulSoup(lbs_raw.content, "html.parser")
    lb_ids = [
        int(link.attrs["href"].split("view/")[1])
        for link in lbs_soup.find_all("a", string="[View]")
    ]
    with open(f"{data_dir}/lb_ids", "wb") as f:
        pickle.dump(
            {
                "time": time.time(),
                "content": lb_ids,
            },
            f,
        )
    return lb_ids


def _parse_puzzle_text(tags, attributes=[]):
    output = []
    for tag in tags:
        if isinstance(tag, NavigableString):
            output.append({"content": tag, "attributes": attributes})
        else:
            child_attrs = attributes + [tag.name]
            if "class" in tag.attrs:
                if "star" in tag.attrs["class"]:
                    child_attrs.append("star")
            output += _parse_puzzle_text(tag.contents, child_attrs)
    return output


def get_puzzle(yr, day, part):
    """Get the puzzle text for a given day and part.

    Args:
        yr (int): Year of the event.
        day (int): Day of the event.
        part (int): Part of the puzzle.

    Returns:
        puzzle (dict): The parsed puzzle text as a dictionary.
    """
    # if op.exists(f"{data_dir}/pz_{yr}_{day}_{part}"):
    #     with open(f"{data_dir}/pz_{yr}_{day}_{part}", "rb") as f:
    #         return pickle.load(f)
    # FIXME: switch caching back on

    cookie = get_cookie()
    puzzle_raw = rq.get(
        f"https://adventofcode.com/{yr}/day/{day}",
        cookies={"session": cookie},
    )

    pz_soup = BeautifulSoup(puzzle_raw.content, "html.parser")
    parts_available = pz_soup.find_all("article", {"class": "day-desc"})

    if len(parts_available) < part:
        raise ValueError("The part you requested is not available yet.")

    part_soup = parts_available[part - 1]

    puzzle = {}
    puzzle["title"] = parts_available[0].contents[0].string.split(": ")[1][:-4]
    puzzle["text"] = _parse_puzzle_text(part_soup.contents[1:])

    with open(f"{data_dir}/pz_{yr}_{day}_{part}", "wb") as f:
        pickle.dump(puzzle, f)
    return puzzle


def purge_cache():
    """Purges the cache."""
    for file in os.listdir(data_dir):
        if not file == ".gitkeep":
            os.remove(f"{data_dir}/{file}")


def connected():
    """Check if the user is connected to Advent of Code."""
    try:
        rq.get("https://adventofcode.com/")
        return True
    except rq.exceptions.ConnectionError:
        return False
