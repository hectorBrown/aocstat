import json
import os.path as op

import appdirs as ad

config_dir = ad.user_config_dir(appname="aocstat", appauthor=False)

DEFAULTS = {
    "ttl": 900,
}
# types defined so that they raise an error if the value is not of the correct type, but return value in correct type if it is castable
TYPES = {
    "ttl": lambda x: int(x),
}
TYPE_ERRS = {
    "ttl": "Value of 'ttl' must be an integer.",
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
    write_value = None
    try:
        write_value = TYPES[key](value)
    except:  # noqa
        raise TypeError(TYPE_ERRS[key])

    _write_config(op.join(config_dir, "config.json"), {key: write_value})


def reset(key):
    """Resets the value of `key` in the config file to the default value.

    Args:
        key (string): Key to reset in config file.
    """
    config = _read_config(op.join(config_dir, "config.json"))
    if config is not None and key in config:
        _write_config(op.join(config_dir, "config.json"), {key: DEFAULTS[key]})


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
    with open(path, "w") as f:
        json.dump(curr, indent=4, fp=f)
