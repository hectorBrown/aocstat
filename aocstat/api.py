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
from bs4 import BeautifulSoup, NavigableString
from selenium import webdriver
from selenium.common.exceptions import (StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

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


def get_year():
    """Returns the year of the most recent AOC event.

    Returns:
        year (int): The year of the most recent AOC event.
    """
    today = dt.date.today()
    return today.year if today.month == 12 else today.year - 1


def get_day(year):
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


def get_id():
    """Gets user id from cache unless it doesn't exist yet, otherwise makes a request.

    Returns:
        id (int): User id.
    """
    if op.exists(f"{data_dir}/id"):
        with open(f"{data_dir}/id", "rb") as f:
            return pickle.load(f)

    cookie = get_cookie()
    req = rq.get(
        f"https://adventofcode.com/{get_year()}/settings",
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


def get_priv_lb(id=None, yr=None, force_update=False, ttl=900):
    """Gets a private board, from cache as long as cache was obtained `< ttl` ago.

    Args:
        id (int, optional): Board id. Defaults to None: gets user ID from cache or request.
        yr (int, optional): Year. Defaults to None: uses current year.
        force_update (bool, optional): Skip cache regardless of ttl and get board from server. Defaults to False.
        ttl (int, optional): Cache ttl. Defaults to 900.

    Returns:
        board (dict): Raw leaderboard data.
    """

    if yr is None:
        yr = get_year()

    if id is None:
        id = get_id()

    if op.exists(f"{data_dir}/lb_{yr}_{id}") and not force_update:
        cached_lb = None
        with open(f"{data_dir}/lb_{yr}_{id}", "rb") as f:
            cached_lb = pickle.load(f)
        if time.time() - cached_lb["time"] <= ttl:
            return json.loads(cached_lb["content"])

    # TODO: read cache if no internet connection
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

    return json.loads(lb.content)


def get_glob_lb(yr=None, day=None):
    # TODO: read cache if no internet connection

    if yr is None:
        yr = get_year()

    if day is None:  # overall lb
        lb_raw = rq.get("https://adventofcode.com/2022/leaderboard")
        lb_soup = BeautifulSoup(lb_raw.content, "html.parser")
        entries_soup = lb_soup.find_all("div", {"class": "leaderboard-entry"})
        lb = {"members": {}, "day": None}
        last_pos = None

        for entry_soup in entries_soup:
            entry = {}
            id = int(entry_soup.get("data-user-id"))

            lb_pos = entry_soup.find("span", {"class": "leaderboard-position"})
            if lb_pos is not None:
                pos = int(re.findall(r"\d*\)", lb_pos.contents[0])[0][:-1])
                entry["rank"] = pos
                last_pos = pos
            else:
                entry["rank"] = last_pos

            entry["total_score"] = int(
                entry_soup.find("span", {"class": "leaderboard-totalscore"}).contents[0]
            )

            name_link = entry_soup.find(
                "a", {"href": re.compile(r"^https:\/\/github\.com\/.+$")}
            )
            if name_link is not None:
                entry["name"] = name_link.contents[-1]
            else:
                anon_name = entry_soup.find("span", {"class": "leaderboard-anon"})
                if anon_name is not None:
                    entry["name"] = anon_name.contents[0]
                else:
                    aoc_support_link = entry_soup.find(
                        "a", {"title": "Advent of Code Supporter"}
                    )
                    if aoc_support_link is not None:
                        entry["name"] = entry_soup.contents[-2]
                    else:
                        entry["name"] = entry_soup.contents[-1]
            lb["members"][id] = entry

        return lb

    else:  # lb by day
        # TODO : implement global lb by day
        pass


def purge_cache():
    """Purges the cache."""
    for file in os.listdir(data_dir):
        if not file == ".gitkeep":
            os.remove(f"{data_dir}/{file}")
