import aocstat.api as api
import os
import datetime as dt
import bs4
import pytest
import pickle
import appdirs as ad


def test_get_most_recent_year():
    assert api.get_most_recent_year() == (
        dt.datetime.now().year
        if dt.datetime.now().month == 12
        else dt.datetime.now().year - 1
    )


def test_get_most_recent_day():
    assert api.get_most_recent_day(2025) == 12
    assert api.get_most_recent_day(2024) == 25
    with pytest.raises(ValueError):
        api.get_most_recent_day(dt.datetime.now().year + 1)


def test_parse_leaderboard_entry():
    entry_soup = bs4.BeautifulSoup(
        '<div class="leaderboard-entry" data-user-id="0000"><span class="leaderboard-position"> 10)</span> <span class="leaderboard-time">Dec 01  00:00:43</span> <a href="https://github.com/joebloggs" target="_blank"><span class="leaderboard-userphoto"><img height="20" src="https://avatars.githubusercontent.com/u/00000?v=4"/></span>joebloggs</a> <a class="supporter-badge" href="/2024/support" title="Advent of Code Supporter">(AoC++)</a> <a class="sponsor-badge" href="/2024/sponsors/redirect?url=https%3A%2F%2Fwww%2Ejanestreet%2Ecom%2F" onclick="if(ga)ga(\'send\',\'event\',\'sponsor\',\'badge\',this.href);" rel="noopener" target="_blank" title="Member of sponsor: Jane Street">(Sponsor)</a></div>',
        "html.parser",
    )
    last_pos = 9
    entry, last_pos_out = api._parse_leaderboard_entry(entry_soup, last_pos)
    assert last_pos_out == 10
    assert entry["supporter"]
    assert entry["sponsor"]
    assert not entry["anon"]
    assert entry["link"] == "https://github.com/joebloggs"
    assert entry["time"] == "Dec 01  00:00:43"


def test_get_glob_lb():
    res = api.get_glob_lb(2024, "1:1")
    file = open("./tests/test_data/glob_lb_2024_1_1.pkl", "rb")
    names = pickle.load(file)
    assert [res[0]["members"][id]["name"] for id in res[0]["members"]] == names  # type:ignore


def test_purge_cache():
    data_dir = ad.user_data_dir(appname="aocstat", appauthor=False)
    api.purge_cache()
    assert set(os.listdir(data_dir)) == {".gitkeep"} or os.listdir(data_dir) == []
