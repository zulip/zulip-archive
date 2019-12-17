import os
from zlib import adler32

def exit_immediately(s):
    print('\nERROR\n', s)
    exit(1)

# Safely open dir/filename, creating dir if it doesn't exist
def open_outfile(dir, filename, mode):
    if not dir.exists():
        os.makedirs(str(dir))
    return (dir / filename).open(mode, encoding='utf-8')

## String cleaning functions

# remove non-alnum ascii symbols from string
def sanitize(s):
    return "".join(filter(str.isalnum, s.encode('ascii', 'ignore').decode('utf-8')))

# create a unique sanitized identifier for a topic
def sanitize_topic(topic_name):
    i = str(adler32(topic_name.encode('utf-8')) % (10 ** 5)).zfill(5)
    return i + sanitize(topic_name)

# create a unique sanitized identifier for a stream
def sanitize_stream(stream_name, stream_id):
    return str(stream_id) + sanitize(stream_name)

