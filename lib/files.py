'''

There are two major phases of this system:

    1. Build JSON files from Zulip data.
    2. Build static website from JSON.

Both phases write to directories with some directories.
Here is an example structure for the JSON piece:

    <json_root>
        stream_index.json
        213222general
            47413hello.json
            48863swimmingturtles.json
            51687topicdemonstration.json
            74282newstreams.json
        213224python
            47413hello.json
            95106streamevents.json

And then here is what your website output might
look like:

    <md_root>
        index.md
        style.css
        213222general
            index.md
            47413hello.html
            48863swimmingturtles.html
            51687topicdemonstration.html
            74282newstreams.html
        213224python
            index.md
            47413hello.html
            95106streamevents.html

In the examples above we have two streams:

    general:
        hello
        swimming turtles
        topic demonstration
        new streams

    python:
        hello
        stream events

We "sanitize" the directory names to avoid escaping issues
with spaces (hence the number prefix).  FWIW the number prefix
for streams corresponds to the Zulip stream id, whereas the topic
prefix is a random hash.  All that really matters is that they are
unique.
'''

import json

from pathlib import Path

from .common import open_outfile

def read_zulip_stream_info(json_root):
    '''
    stream_index.json

    This JSON goes two levels deep, showing every stream, and
    then within each stream, a bit of info for every topic in
    the stream.  To get actual messages within a topic, you go
    to other files deeper in the directory structure.
    '''
    f = (json_root / Path('stream_index.json')).open('r', encoding='utf-8')
    stream_info = json.load(f, encoding='utf-8')
    f.close()
    return stream_info

def read_zulip_messages_for_topic(
        json_root,
        sanitized_stream_name,
        sanitized_topic_name
        ):
    '''
    <stream>/<topic>.json

    This JSON has info for all the messags in a topic.
    '''
    json_path = json_root / Path(sanitized_stream_name) / Path (sanitized_topic_name + '.json')
    f = json_path.open('r', encoding='utf-8')
    messages = json.load(f)
    f.close()
    return messages

def open_main_page(md_root):
    outfile = open_outfile(md_root, Path('index.md'), 'w+')
    return outfile

def open_stream_topics_page(md_root, sanitized_stream_name):
    directory = md_root / Path('stream/'+sanitized_stream_name)
    outfile = open_outfile(directory, Path('index.md'), 'w+')
    return outfile

def open_topic_messages_page(md_root, sanitized_stream_name, sanitized_topic_name):
    directory = md_root / Path(sanitized_stream_name+'/topic')
    outfile = open_outfile(directory, Path(sanitized_topic_name + '.html'), 'w+')
    return outfile

