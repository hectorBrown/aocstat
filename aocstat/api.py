import json
import os.path as op
import webbrowser as wb

import requests as rq
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait


def read_config(path):
    """Reads JSON config file at `path`, if it doesn't exist, returns `None`.

    Args:
        path (string): Path to config file.

    Returns:
        config (dict): A dictionary that describes the JSON object at `path`.
    """
    if not op.exists(path):
        return None
    with open(path, "r") as f:
        try:
            return json.loads(f.read())
        except json.decoder.JSONDecodeError:
            raise json.decoder.JSONDecodeError(
                f"Improperly formatted config file at '{path}'."
            )


def write_config(path, data):
    """Writes `data` to JSON config file at `path`. Preserves existing keys not included in `data`, updates those in both `data` and at `path`, creates those only in `data`.

    Args:
        path (string): Path to config file.
        data (dict): Dictionary of data to add to config file.
    """
    curr = read_config(path)
    with open(path, "w") as f:
        for key in data:
            curr[key] = data[key]
        f.write(json.dump(curr, indent=4))


def get_cookie(cfg):
    user_cfg = read_config(f"{cfg}/user.cfg")
    user_cfg = [] if user_cfg is None else user_cfg
    if "cookie" in user_cfg:
        return user_cfg["cookie"]
    else:
        # get cookie with selenium
        print(
            "Please select a browser to use for authentication (must be one you have installed already):\n"
            + "1) Firefox (default)\n"
            + "2) Chrome\n"
            + "3) Edge\n"
            + "4) Internet Explorer\n"
            + "5) Safari"
        )
        selection = input("Selection (1,2,3,4,[5]): ")


def get_board(id, cache):
    # check the cache directory for board at id
    # if no cache, pull from api
    pass
