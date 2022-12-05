import json
import os.path as op


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
