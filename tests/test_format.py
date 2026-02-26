import aocstat.format as format


def test_wrap_text():
    text = "a" * 100
    output = format.wrap_text(text, 10)
    assert all([len(line) <= 10 for line in output.split("\n")])
