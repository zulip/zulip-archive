"""
This library helps populate a series of JSON files from a
running Zulip instance.

Conceptually it just moves data in one direction:

    Zulip -> file system (JSON files)

This is probably the most technical part of the archive codebase
for now.  Conceptually, it's just connecting to Zulip with the
Python API for Zulip and getting recent messages.

Some of the details are about getting incremental updates from
Zulip.  See `populate_incremental`, but the gist of it is that
we read `latest_id` from the JSON and then use that as the
`anchor` in the API request to Zulip.

About the data:

    The json format for stream_index.json is something like below:

    {
        'time': <the last time stream_index.md was updated>,
        'streams': {
            stream_name: {
                'id': stream_id,
                'latest_id': id of latest post in stream,
                'topic_data': {
                    topic_name: {
                        topic_size: num posts in topic,
                        latest_date: time of latest post }}}}}

    stream_index.json is created in the top level of the JSON directory.

    This directory also contains a subdirectory for each archived stream.

    In each stream subdirectory, there is a json file for each topic in that stream.

    This json file is a list of message objects,
    as desribed at https://zulipchat.com/api/get-messages
"""

import json
import time
from datetime import datetime
from pathlib import Path
from .common import (
        exit_immediately,
        open_outfile,
        )
from .url import (
        sanitize_stream,
        sanitize_topic,
        )

def dump_json(js, outfile):
    json.dump(js, outfile, ensure_ascii=False, sort_keys=True, indent=4)

# Takes a list of messages. Returns a dict mapping topic names to lists of messages in that topic.
def separate_results(list):
    map = {}
    for m in list:
        if m['subject'] not in map:
            map[m['subject']] = [m]
        else:
            map[m['subject']].append(m)
    return map

# Retrieves all messages matching request from Zulip, starting at post id anchor.
# As recommended in the Zulip API docs, requests 1000 messages at a time.
# Returns a list of messages.
def request_all(client, request, anchor=0):
    request['anchor'] = anchor
    request['num_before'] = 0
    request['num_after'] = 1000
    response = safe_request(client.get_messages, request)
    msgs = response['messages']
    while not response['found_newest']:
        request['anchor'] = response['messages'][-1]['id'] + 1
        response = safe_request(client.get_messages, request)
        msgs = msgs + response['messages']
    return msgs

# runs client.cmd(args). If the response is a rate limit error, waits
# the requested time and then retries the request.
def safe_request(cmd, *args, **kwargs):
    rsp = cmd(*args, **kwargs)
    while rsp['result'] == 'error':
        print("timeout hit: {}".format(rsp['retry-after']))
        time.sleep(float(rsp['retry-after']) + 1)
        rsp = cmd(*args, **kwargs)
    return rsp

def get_streams(client):
    # In the future, we may want to change this to
    # include_web_public=True, for organizations that might want to
    # use the upcoming web_public flag; but at the very least we
    # should only include public streams.
    response = safe_request(client.get_streams,
                            include_public=True,
                            include_subscribed=False)
    return response['streams']

# Retrieves all messages from Zulip and builds a cache at json_root.
def populate_all(
        client,
        json_root,
        is_valid_stream_name,
        ):
    all_streams = get_streams(client)

    streams = [s for s in all_streams if is_valid_stream_name(s['name'])]

    streams_data = {}

    for s in streams:
        stream_name = s['name']
        stream_id = s['stream_id']

        print(stream_name)

        topics = safe_request(client.get_stream_topics, stream_id)['topics']

        latest_id = 0  # till we know better

        topic_data = {}

        for t in topics:
            topic_name = t['name']

            request = {
                'narrow': [
                    {'operator': 'stream', 'operand': stream_name},
                    {'operator': 'topic', 'operand': topic_name}
                ],
                'client_gravatar': True,
                'apply_markdown': True
            }

            messages = request_all(client, request)

            topic_count = len(messages)
            last_message = messages[-1]
            latest_date = last_message['timestamp']

            topic_data[topic_name] = dict(
                size=topic_count,
                latest_date=latest_date)

            latest_id = max(latest_id, last_message['id'])

            dump_topic_messages(json_root, s, topic_name, messages)

        stream_data = dict(
            id=stream_id,
            latest_id=latest_id,
            topic_data=topic_data,
            )

        streams_data[stream_name] = stream_data

    js = dict(
        streams=streams_data,
        time=time.time()
        )
    dump_stream_index(json_root, js)

# Retrieves only new messages from Zulip, based on timestamps from the last update.
# Raises an exception if there is no index at json_root/stream_index.json
def populate_incremental(
        client,
        json_root,
        is_valid_stream_name,
        ):
    streams = get_streams(client)
    stream_index = json_root / Path('stream_index.json')

    if not stream_index.exists():
        error_msg = '''
    You are trying to incrementally update your index, but we cannot find
    a stream index at {}.

    Most likely, you have never built the index.  You can use the -t option
    of this script to build a full index one time.

    (It's also possible that you have built the index but modified the configuration
    or moved files in your file system.)
            '''.format(stream_index)
        exit_immediately(error_msg)

    f = stream_index.open('r', encoding='utf-8')
    js = json.load(f, encoding='utf-8')
    f.close()

    for s in (s for s in streams if is_valid_stream_name(s['name'])):
        print(s['name'])
        if s['name'] not in js['streams']:
            js['streams'][s['name']] = {'id':s['stream_id'], 'latest_id':0, 'topic_data':{}}
        request = {'narrow':[{'operator':'stream', 'operand':s['name']}], 'client_gravatar': True,
                   'apply_markdown': True}
        new_msgs = request_all(client, request, js['streams'][s['name']]['latest_id']+1)
        if len(new_msgs) > 0:
            js['streams'][s['name']]['latest_id'] = new_msgs[-1]['id']
        nm = separate_results(new_msgs)
        for topic_name in nm:
            p = json_root / Path(sanitize_stream(s['name'], s['stream_id'])) / Path(sanitize_topic(topic_name) + '.json')
            topic_exists = p.exists()
            old = []
            if topic_exists:
                f = p.open('r', encoding='utf-8')
                old = json.load(f)
                f.close()
            m = nm[topic_name]
            new_topic_data = {'size': len(m)+len(old),
                                'latest_date': m[-1]['timestamp']}
            js['streams'][s['name']]['topic_data'][topic_name] = new_topic_data
            dump_topic_messages(json_root, s, topic_name, old+m)

    js['time'] = time.time()
    dump_stream_index(json_root, js)

def dump_stream_index(json_root, js):
    if not ('streams' in js and 'time' in js):
        raise Exception('programming error')

    out = open_outfile(json_root, Path('stream_index.json'), 'w')
    dump_json(js, out)
    out.close()

def dump_topic_messages(json_root, stream_data, topic_name, message_data):
    stream_name = stream_data['name']
    stream_id = stream_data['stream_id']
    sanitized_stream_name = sanitize_stream(stream_name, stream_id)
    stream_dir = json_root / Path(sanitized_stream_name)

    sanitized_topic_name = sanitize_topic(topic_name)
    topic_fn = sanitized_topic_name + '.json'

    out = open_outfile(stream_dir, topic_fn, 'w')
    msgs = [slim_message(m) for m in message_data]
    dump_json(msgs, out)
    out.close()

def slim_message(msg):
    fields = [
        'content',
        'id',
        'sender_full_name',
        'timestamp',
        ]
    return { k : v for k, v in msg.items() if k in fields }
