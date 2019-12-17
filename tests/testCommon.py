# For convenience, just run the tests from its own directory
import os
import sys
os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append('../lib')

import common

def assert_equal(v1, v2):
    if v1 != v2:
        print('mismatch')
        print(v1)
        print(v2)
        raise AssertionError

def test_sanitize():
    assert_equal(
        common.sanitize_stream(stream_name='foo bar', stream_id=7),
        '7foobar'
        )

    # The 87695 below is an adler32 hash of the topic name
    assert_equal(
        common.sanitize_topic(topic_name='pick a place for lunch'),
        '87695pickaplaceforlunch'
        )

if __name__ == '__main__':
    test_sanitize()
