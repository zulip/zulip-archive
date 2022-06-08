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
    assert_equal(url.sanitize_stream(stream_name="foo bar", stream_id=7), "7-foo-bar")

    assert_equal(
        url.sanitize_topic(topic_name="pick a place for lunch"),
        "pick.20a.20place.20for.20lunch",
    )


def test_validator():
    validator = common.stream_validator(Settings(included_streams=["*"]))

    assert_equal(validator("foo", False), True)

    validator = common.stream_validator(Settings(included_streams=["foo", "bar"]))
    assert_equal(validator("foo", False), True)
    assert_equal(validator("bar", False), True)
    assert_equal(validator("baz", False), False)

    validator = common.stream_validator(
        Settings(included_streams=["*"], excluded_streams=["bad", "worse"])
    )
    assert_equal(validator("good", False), True)
    assert_equal(validator("bad", False), False)
    assert_equal(validator("worse", False), False)

    # edge case: excluded takes precedence over included
    validator = common.stream_validator(
        Settings(included_streams=["foo"], excluded_streams=["foo"])
    )
    assert_equal(validator("foo", False), False)

    validator = common.stream_validator(
        Settings(included_streams=["baz"], excluded_streams=['bar']))
    assert_equal(validator("foo", True), True)
    assert_equal(validator("bar", True), False)


if __name__ == "__main__":
    test_sanitize()
    test_validator()
