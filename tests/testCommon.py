# For convenience, just run the tests from its own directory
import os
import sys

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append("../lib")

import common
import url


class Settings:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def assert_equal(v1, v2):
    if v1 != v2:
        print("mismatch")
        print(v1)
        print(v2)
        raise AssertionError


def test_sanitize():
    assert_equal(
        url.sanitize_stream(stream_name="foo bar", stream_id=7),
        "7-foo-bar",
    )
    assert_equal(
        url.sanitize_stream(stream_name="foo/bar/turtle[🐢]", stream_id=7),
        "7-foo.2Fbar.2Fturtle.5B.F0.9F.90.A2.5D",
    )

    assert_equal(
        url.sanitize("pick a place for lunch *"),
        "pick.20a.20place.20for.20lunch.20.2A",
    )
    assert_equal(
        url.sanitize("!!cute-turlte/tortoise (🐢)?"),
        ".21.21cute-turlte.2Ftortoise.20.28.F0.9F.90.A2.29.3F",
    )
    assert_equal(
        url.sanitize('"the mighty turtle 🐢"'),
        ".22the.20mighty.20turtle.20.F0.9F.90.A2.22",
    )


def test_validator():
    validator = common.stream_validator(Settings(included_streams=["*"]))

    assert_equal(validator("foo"), True)

    validator = common.stream_validator(Settings(included_streams=["foo", "bar"]))
    assert_equal(validator("foo"), True)
    assert_equal(validator("bar"), True)
    assert_equal(validator("baz"), False)

    validator = common.stream_validator(
        Settings(included_streams=["*"], excluded_streams=["bad", "worse"])
    )
    assert_equal(validator("good"), True)
    assert_equal(validator("bad"), False)
    assert_equal(validator("worse"), False)

    # edge case: excluded takes precedence over included
    validator = common.stream_validator(
        Settings(included_streams=["foo"], excluded_streams=["foo"])
    )
    assert_equal(validator("foo"), False)


if __name__ == "__main__":
    test_sanitize()
    test_validator()
