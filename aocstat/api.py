import datetime as dt
import json
import os
import os.path as op
import pickle
import re
import time

import requests as rq
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


def get_cookie(cache_invalid=False):
    """Gets session cookie from cache if present and not marked invalid. Authenticates and caches otherwise.

    Args:
        cache_invalid (bool, optional): Force authentication by setting to `True`. Defaults to False.

    Returns:
        cookie (str): Session cookie.
    """
    if op.exists("aocstat/cache/cookie") and not cache_invalid:
        with open("aocstat/cache/cookie", "rb") as f:
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
            selection = input("Selection ([1],2,3,4,5,6): ")
            if selection in [""] + [str(x) for x in range(1, 7)]:
                valid_browser = True
            else:
                print("'{}' isn't a valid selection.")

        cookie = None
        if not selection == "6":
            wd = None
            input("Please press ENTER to open a web browser... ")
            try:
                if selection in ["1", ""]:
                    wd = webdriver.Firefox()
                elif selection == "2":
                    wd = webdriver.Chrome()
                elif selection == "3":
                    wd = webdriver.Edge()
                elif selection == "4":
                    wd = webdriver.Ie()
                else:
                    wd = webdriver.Safari()
            except Exception:
                print(
                    "\nYou don't have a driver installed for that browser, please try again.\n"
                )
                return get_cookie(cache_invalid=cache_invalid)

            wd.get("https://adventofcode.com/2022/auth/login")
            print("\nPlease authenticate yourself with one of the methods given.")

            def logged_in(wd):
                links = wd.find_elements(By.TAG_NAME, "a")
                return "[Log Out]" in [link.text for link in links]

            try:
                WebDriverWait(wd, timeout=1000, poll_frequency=1).until(logged_in)
            except TimeoutException:
                print("\nTimed out waiting for authentication.\n")
                wd.quit()

            cookie = wd.get_cookie("session")["value"]  # type: ignore
            wd.quit()
            print("\nAuthenticated.\n")
        else:
            print(
                "\nBrave!\n"
                + "1) Navigate to 'https://adventofcode.com/2022/auth/login'.\n"
                + "2) Authenticate if necessary.\n"
                + "3) Open the network tools in your browser, refresh the page and examine the GET request for cookies.\n"
                + "4) Copy everything after 'session=' into the field below."
            )
            cookie = input("session=")
            print("\nSaved.\n")

        with open("aocstat/cache/cookie", "wb") as f:
            pickle.dump(cookie, f)
        return cookie


def get_id():
    """Gets user id from cache unless it doesn't exist yet, otherwise makes a request.

    Returns:
        id (int): User id.
    """
    if op.exists("aocstat/cache/id"):
        with open("aocstat/cache/id", "rb") as f:
            return pickle.load(f)

    cookie = get_cookie()
    req = rq.get(
        f"https://adventofcode.com/{dt.date.today().year}/settings",
        cookies={"session": cookie},
    )
    soup = BeautifulSoup(req.content, "html.parser")
    id = int(
        soup.find(string=re.compile("\(anonymous user #(\d+)\)")).split("#")[1][  # type: ignore
            :-1
        ]
    )
    with open("aocstat/cache/id", "wb") as f:
        pickle.dump(id, f)
    return id


def get_priv_lb(id=None, yr=None, force_update=False, req_freq=900):
    """Gets a private board, from cache as long as the last request was made `< req_freq` ago.

    Args:
        id (int, optional): Board id. Defaults to None: gets user ID from cache or request.
        yr (int, optional): Year. Defaults to None: uses current year.
        force_update (bool, optional): Skip cache regardless of ttl and get board from server. Defaults to False.
        req_freq (int, optional): Lower bound on period between requests in seconds. Defaults to 900.

    Returns:
        board (dict): Raw leaderboard data.
    """

    if yr is None:
        yr = dt.date.today().year

    if id is None:
        id = get_id()

    if (
        op.exists("aocstat/cache/priv_req")
        and op.exists(f"aocstat/cache/lb_{yr}_{id}")
        and not force_update
    ):
        cached_lb = None
        req_time = None
        with open(f"aocstat/cache/lb_{yr}_{id}", "rb") as f:
            cached_lb = pickle.load(f)
        with open("aocstat/cache/priv_req", "rb") as f:
            req_time = pickle.load(f)

        if time.time() - req_time <= req_freq:
            return cached_lb

    cookie = get_cookie()
    lb = rq.get(
        f"https://adventofcode.com/{yr}/leaderboard/private/view/{id}.json",
        cookies={"session": cookie},
    )
    if lb.content[0] == "<":  # i.e. is HTML
        cookie = get_cookie(cache_invalid=True)
        lb = rq.get(
            f"https://adventofcode.com/{yr}/leaderboard/private/view/{id}.json",
            cookies={"session": cookie},
        )

    lb_content = json.loads(lb.content)

    with open(f"aocstat/cache/lb_{yr}_{id}", "wb") as f:
        pickle.dump(lb_content, f)
    with open("aocstat/cache/priv_req", "wb") as f:
        pickle.dump(time.time(), f)

    return lb_content


def purge_cache():
    """Purges the cache."""
    for file in os.listdir("aocstat/cache/"):
        if not file == ".gitkeep":
            os.remove(f"aocstat/cache/{file}")
