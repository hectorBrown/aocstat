import aocstat.config as config


def test_get_set():
    previous = {}
    new_vals = {
        "ttl": 10293,
    }
    for value in config.TYPES:
        previous[value] = config.get(value)
        config.set(value, new_vals[value])
        assert config.get(value) == new_vals[value]
        config.reset(value)
        assert config.get(value) == config.DEFAULTS["ttl"]
        config.set(value, previous[value])
