import json
import os.path as op

import appdirs as ad

config_dir = ad.user_config_dir(appname="aocstat", appauthor=False)

DEFAULTS = {
    "ttl": 900,
}


def get(key):
    """Gets the value of `key` from the config file. If `key` is not found, returns the default value.

    Args:
        key (string): Key to get from config file.

    Returns:
        value: Value of `key` in config file, or default value if not found.
    """
    config = _read_config(op.join(config_dir, "config.json"))
    if config is None:
        return DEFAULTS[key] if key in DEFAULTS else None
    else:
        return (
            config[key] if key in config else DEFAULTS[key] if key in DEFAULTS else None
        )


def set(key, value):
    """Sets the value of `key` in the config file.

    Args:
        key (string): Key to set in config file.
        value: Value to set `key` to in config file.
    """
    _write_config(op.join(config_dir, "config.json"), {key: value})


def _read_config(path):
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
        except json.decoder.JSONDecodeError as e:
            raise json.decoder.JSONDecodeError(
                "Improperly formatted config file.",
                doc=e.doc,
                pos=e.pos,
            )


def _write_config(path, data):
    """Writes `data` to JSON config file at `path`. Preserves existing keys not included in `data`, updates those in both `data` and at `path`, creates those only in `data`.

    Args:
        path (string): Path to config file.
        data (dict): Dictionary of data to add to config file.
    """
    curr = _read_config(path)
    curr = {} if curr is None else curr
    for key in data:
        curr[key] = data[key]
    json.dump(curr, indent=4, fp=path)
