import json
import os.path as op
import pickle
import webbrowser as wb

import requests as rq
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
                elif selection == "5":
                    wd = webdriver.Safari()
            except Exception:
                print(
                    "\nYou don't have a driver installed for that browser, please try again.\n"
                )
                return get_cookie(cache_invalid=cache_invalid)

            wd.get("https://adventofcode.com/2022/auth/login")
            print("\nPlease authenticate yourself with one of the methods given.")

            timeout = False
            try:
                WebDriverWait(wd, timeout=1000, poll_frequency=1).until(
                    lambda d: "[Log Out]"
                    in [x.text for x in d.find_elements(By.TAG_NAME, "a")]
                )
            except TimeoutException:
                print("\nTimed out waiting for authentication.\n")
                wd.quit()

            cookie = wd.get_cookie("session")["value"]
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


def get_board(id, cache):
    # check the cache directory for board at id
    # if no cache, pull from api
    pass
