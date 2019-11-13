#!/usr/bin/env python3
#
# The workflow (timing for the leanprover Zulip chat, on my slow laptop):
# - populate_all() builds a json file in `json_root` for each topic, containing message data,
#   and an index json file mapping streams to their topics.
#   This uses the Zulip API and takes ~10 minutes to crawl the whole chat.
# - populate_incremental() assumes there is already a json cache and collects only new messages.
# - write_markdown() builds markdown files in `md_root` from the json. This takes ~15 seconds.
# - This markdown can be pushed directly to GitHub or built locally with `jekyll serve --incremental`.
#   Building locally takes about 1 minute.
#
# The json format for stream_index.json is:
# { 'time': the last time stream_index.md was updated,
#   'streams': { stream_name: { 'id': stream_id,
#                               'latest_id': id of latest post in stream,
#                               'topic_data': { topic_name: { topic_size: num posts in topic,
#                                                            latest_date: time of latest post }}}}}
#
# stream_index.json is created in the json_root directory.
# This directory also contains a subdirectory for each archived stream.
# In each stream subdirectory, there is a json file for each topic in that stream.
# This json file is a list of message objects, as desribed at https://zulipchat.com/api/get-messages
#

from datetime import datetime
from pathlib import Path
from shutil import copyfile
from typing import Any, Optional
from zlib import adler32
import configparser
import zulip, os, time, json, urllib, argparse, subprocess


# Globals

client = None
config_file = None
zulip_url = None
site_url = None
stream_whitelist = None
stream_blacklist = None
archive_title = None
md_root = None
html_root = None
md_index = None
last_updated_dir = None
last_updated_file = None

def read_config():
    global client
    global config_file
    global zulip_url
    global site_url
    global stream_whitelist
    global stream_blacklist
    global archive_title
    global json_root
    global md_root
    global html_root
    global md_index
    global last_updated_dir
    global last_updated_file

    def get_config(section: str, key: str, default_value: Optional[Any]=None) -> Optional[Any]:
        if config_file.has_option(section, key):
            return config_file.get(section, key)
        return default_value

    ## Configuration options
    # config_file should point to a Zulip api config
    client = zulip.Client(config_file="./zuliprc")

    # With additional options supported for the below.
    config_file = configparser.RawConfigParser()
    config_file.read("./zuliprc")

    # The Zulip server's public URL is required in zuliprc already
    zulip_url = get_config("api", "site")
    # The user-facing root url. Only needed for md/html generation.
    site_url = get_config("archive", "root_url", "file://" + os.path.abspath(os.path.dirname(__file__)))

    # Streams in stream_blacklist are ignored.
    # If stream_whitelist is nonempty, only streams that appear there and not in
    # stream_blacklist will be archived.
    stream_blacklist_str = get_config("archive", "stream_blacklist", "")
    stream_whitelist_str = get_config("archive", "stream_whitelist", "")
    if stream_whitelist_str != "":
        stream_whitelist = stream_whitelist_str.split(",")
    else:
        stream_whitelist = []

    if stream_blacklist_str != "":
        stream_blacklist = stream_blacklist_str.split(",")
    else:
        stream_blacklist = []

    # The title of the archive
    archive_title = get_config("archive", "title", "Zulip Chat Archive")

    # directory to store the generated .json files
    json_root = Path(get_config("archive", "json_root", "./_json"))
    # directory to store the generated .md and .html files
    md_root = Path(get_config("archive", "md_root", "./archive"))
    # user-facing path for the index
    html_root = get_config("archive", "html_root", "archive")

    # These options these should be little reason to need to update.
    md_index = Path("index.md") # name for the index files
    last_updated_dir = Path("_includes") # directory to store update timestamp
    last_updated_file = Path("archive_update.html") # filename for update timestamp


## Customizable display functions.

# When generating displayable md/html, we create the following structure inside md_root:
# * md_root/md_index displays a list of all streams
# * for each stream str, md_root/str/md_index displays a list of all topics in str
# * for each topic top in a stream str, md_root/str/top.html displays the posts in top.
#
# Some sanitization is needed to ensure that urls are unique and acceptable.
# Use sanitize_stream(stream_name, stream_id) in place of str above.
# Use sanitize_topic(topic_name) in place of top.
#
# The topic display must be an html file, since we use the html provided by Zulip.
# The index pages are generated in markdown by default, but this can be changed to html.
# The default settings are designed for a Jekyll build.

# writes the Jekyll header info for the index page listing all streams.
def write_stream_index_header(outfile):
    outfile.writelines(['---\n', 'layout: archive\n', 'title: {}\n'.format(archive_title)])
    outfile.write('permalink: {}/index.html\n'.format(html_root))
    outfile.writelines(['---\n\n', '---\n\n', '## Streams:\n\n'])

# writes the index page listing all streams.
# `streams`: a dict mapping stream names to stream json objects as described in the header.
def write_stream_index(streams):
    outfile = open_outfile(md_root, md_index, 'w+')
    write_stream_index_header(outfile)
    for s in sorted(streams, key=lambda s: len(streams[s]['topic_data']), reverse=True):
        num_topics = len(streams[s]['topic_data'])
        outfile.write("* [{0}]({1}/index.html) ({2} topic{3})\n\n".format(
            s,
            sanitize_stream(s, streams[s]['id']),
            num_topics,
            '' if num_topics == 1 else 's'))
    outfile.write('\n{% include ' + str(last_updated_file) + ' %}')
    outfile.close()

# writes the Jekyll header info for the index page for a given stream.
def write_topic_index_header(outfile, stream_name, stream):
    permalink = 'permalink: {1}/{0}/index.html'.format(
        sanitize_stream(stream_name, stream['id']), html_root
    )
    strm = '## Stream: [{0}]({1}/index.html)'.format(
        stream_name, format_stream_url(stream['id'], stream_name)
    )
    outfile.writelines(['---\n', 'layout: archive\n', 'title: {}\n'.format(archive_title),
                        permalink, '\n---\n\n', strm, '\n---\n\n', '### Topics:\n\n'])

# writes an index page for a given stream, printing a list of the topics in that stream.
# `stream_name`: the name of the stream.
# `stream`: a stream json object as described in the header
def write_topic_index(stream_name, stream):
    directory = md_root / Path(sanitize_stream(stream_name, stream['id']))
    outfile = open_outfile(directory, md_index, 'w+')
    write_topic_index_header(outfile, stream_name, stream)
    for topic_name in sorted(stream['topic_data'], key=lambda tn: stream['topic_data'][tn]['latest_date'], reverse=True):
        t = stream['topic_data'][topic_name]
        outfile.write("* [{0}]({1}.html) ({2} message{4}, latest: {3})\n".format(
            escape_pipes(topic_name),
            sanitize_topic(topic_name),
            t['size'],
            datetime.utcfromtimestamp(t['latest_date']).strftime('%b %d %Y at %H:%M'),
            '' if t['size'] == 1 else 's'
        ))
    outfile.write('\n{% include ' + str(last_updated_file) + ' %}')
    outfile.close()

# formats the header for a topic page.
def write_topic_header(outfile, stream_name, stream_id, topic_name):
    outfile.write('<head><link href="/style.css" rel="stylesheet"></head>')
    permalink = 'permalink: {0}/{1}/{2}.html'.format(
        html_root,
        sanitize_stream(stream_name, stream_id),
        sanitize_topic(topic_name)
    )
    strm = '<h2>Stream: <a href="{1}/index.html">{0}</a>'.format(
        stream_name,
        format_stream_url(stream_id, stream_name)
    )
    tpc = '<h3>Topic: <a href="{2}/{1}.html">{0}</a></h3>'.format(
        topic_name,
        sanitize_topic(topic_name),
        format_stream_url(stream_id, stream_name)
    )
    outfile.writelines(['---\n', 'layout: archive\n', 'title: {}\n'.format(archive_title),
                        permalink, '\n---\n\n', strm, '\n', tpc, '\n\n<hr>\n\n', '<base href="{}">\n'.format(zulip_url)])

# formats a single post in a topic
# Note: the default expects the Zulip "Z" icon at site_url+'assets/img/zulip2.png'
def format_message(user_name, date, msg, link, anchor_name, anchor_url):
    anchor = '<a name="{0}"></a>'.format(anchor_name)
    zulip_link = '<a href="{0}" class="zl"><img src="{1}" alt="view this post on Zulip"></a>'.format(link, site_url+'assets/img/zulip2.png')
    local_link = '<a href="{0}">{1} ({2})</a>'.format(anchor_url, user_name, date)
    return '{0}\n<h4>{1} {2}:</h4>\n{3}'.format(anchor, zulip_link, local_link, msg)


# writes the body of a topic page (ie, a list of messages)
# `messages`: a list of message json objects, as defined in the Zulip API
def write_topic_body(messages, stream_name, stream_id, topic_name, outfile):
    for c in messages:
        name = c['sender_full_name']
        date = datetime.utcfromtimestamp(c['timestamp']).strftime('%b %d %Y at %H:%M')
        msg = c['content']
        link = structure_link(stream_id, stream_name, topic_name, c['id'])
        anchor_name = str(c['id'])
        anchor_link = '{0}/{1}/{2}.html#{3}'.format(
            urllib.parse.urljoin(site_url, html_root),
            sanitize_stream(stream_name, stream_id),
            sanitize_topic(topic_name),
            anchor_name)
        outfile.write(format_message(name, date, msg, link, anchor_name, anchor_link))
        outfile.write('\n\n')


# writes a topic page.
# `stream`: a stream json object as defined in the header
def write_topic(stream_name, stream, topic_name):
    json_path = json_root / Path(sanitize_stream(stream_name, stream['id'])) / Path (sanitize_topic(topic_name) + '.json')
    f = json_path.open('r', encoding='utf-8')
    messages = json.load(f)
    f.close()
    o = open_outfile(md_root / Path(sanitize_stream(stream_name, stream['id'])), Path(sanitize_topic(topic_name) + '.html'), 'w+')
    write_topic_header(o, stream_name, stream['id'], topic_name)
    o.write('\n{% raw %}\n')
    write_topic_body(messages, stream_name, stream['id'], topic_name, o)
    o.write('\n{% endraw %}\n')
    o.write('\n{% include ' + str(last_updated_file) + ' %}')
    o.close()



## Nothing after this point should need to be modified.

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

# escape | character with \|
def escape_pipes(s):
    return s.replace('|','\|').replace(']','\]').replace('[','\[')


## retrieve information from Zulip

# runs client.cmd(args). If the response is a rate limit error, waits
# the requested time and then retries the request.
def safe_request(cmd, *args, **kwargs):
    rsp = cmd(*args, **kwargs)
    while rsp['result'] == 'error':
        print("timeout hit: {}".format(rsp['retry-after']))
        time.sleep(float(rsp['retry-after']) + 1)
        rsp = cmd(*args, **kwargs)
    return rsp

def get_streams():
    # In the future, we may want to change this to
    # include_web_public=True, for organizations that might want to
    # use the upcoming web_public flag; but at the very least we
    # should only include public streams.
    response = safe_request(client.get_streams,
                            include_public=True,
                            include_subscribed=False)
    return response['streams']

# Safely open dir/filename, creating dir if it doesn't exist
def open_outfile(dir, filename, mode):
    if not dir.exists():
        os.makedirs(str(dir))
    return (dir / filename).open(mode, encoding='utf-8')

# Retrieves all messages matching request from Zulip, starting at post id anchor.
# As recommended in the Zulip API docs, requests 1000 messages at a time.
# Returns a list of messages.
def request_all(request, anchor=0):
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

# Takes a list of messages. Returns a dict mapping topic names to lists of messages in that topic.
def separate_results(list):
    map = {}
    for m in list:
        if m['subject'] not in map:
            map[m['subject']] = [m]
        else:
            map[m['subject']].append(m)
    return map

def test_valid(s):
    return s['name'] not in stream_blacklist and (True if stream_whitelist == [] else s['name'] in stream_whitelist)

# Retrieves only new messages from Zulip, based on timestamps from the last update.
# Raises an exception if there is no index at json_root/stream_index.json
def populate_incremental():
    streams = get_streams()
    stream_index = json_root / Path('stream_index.json')
    if not stream_index.exists():
        raise Exception('stream index does not exist at {}\nCannot update incrementally without an index.'.format(stream_index))
    f = stream_index.open('r', encoding='utf-8')
    stream_index = json.load(f, encoding='utf-8')
    f.close()
    for s in (s for s in streams if test_valid(s)):
        print(s['name'])
        if s['name'] not in stream_index['streams']:
            stream_index['streams'][s['name']] = {'id':s['stream_id'], 'latest_id':0, 'topic_data':{}}
        request = {'narrow':[{'operator':'stream', 'operand':s['name']}], 'client_gravatar': True,
                   'apply_markdown': True}
        new_msgs = request_all(request, stream_index['streams'][s['name']]['latest_id']+1)
        if len(new_msgs) > 0:
            stream_index['streams'][s['name']]['latest_id'] = new_msgs[-1]['id']
        nm = separate_results(new_msgs)
        for t in nm:
            p = json_root / Path(sanitize_stream(s['name'], s['stream_id'])) / Path(sanitize_topic(t) + '.json')
            topic_exists = p.exists()
            old = []
            if topic_exists:
                f = p.open('r', encoding='utf-8')
                old = json.load(f)
                f.close()
            m = nm[t]
            new_topic_data = {'size': len(m)+len(old),
                                'latest_date': m[-1]['timestamp']}
            stream_index['streams'][s['name']]['topic_data'][t] = new_topic_data
            out = open_outfile(json_root / Path(sanitize_stream(s['name'], s['stream_id'])),
                               Path(sanitize_topic(t) + '.json'), 'w')
            json.dump(old+m, out, ensure_ascii=False)
            out.close()
    stream_index['time'] = datetime.utcfromtimestamp(time.time()).strftime('%b %d %Y at %H:%M')
    out = open_outfile(json_root, Path('stream_index.json'), 'w')
    json.dump(stream_index, out, ensure_ascii = False)
    out.close()

# Retrieves all messages from Zulip and builds a cache at json_root.
def populate_all():
    streams = get_streams()
    ind = {}
    for s in (s for s in streams if test_valid(s)):
        print(s['name'])
        topics = safe_request(client.get_stream_topics, s['stream_id'])['topics']
        nind = {'id': s['stream_id'], 'latest_id':0}
        tpmap = {}
        for t in topics:
            request = {
                'narrow': [{'operator': 'stream', 'operand': s['name']},
                           {'operator': 'topic', 'operand': t['name']}],
                'client_gravatar': True,
                'apply_markdown': True
            }
            m = request_all(request)
            tpmap[t['name']] = {'size': len(m),
                                'latest_date': m[-1]['timestamp']}
            nind['latest_id'] = max(nind['latest_id'], m[-1]['id'])
            out = open_outfile(json_root / Path(sanitize_stream(s['name'], s['stream_id'])),
                               Path(sanitize_topic(t['name']) + '.json'), 'w')
            json.dump(m, out, ensure_ascii=False)
            out.close()
        nind['topic_data'] = tpmap
        ind[s['name']] = nind
    js = {'streams':ind, 'time':datetime.utcfromtimestamp(time.time()).strftime('%b %d %Y at %H:%M')}
    out = open_outfile(json_root, Path('stream_index.json'), 'w')
    json.dump(js, out, ensure_ascii = False)
    out.close()



## Display

# Create a link to a post on Zulip
def structure_link(stream_id, stream_name, topic_name, post_id):
    sanitized = urllib.parse.quote(
        '{0}-{1}/topic/{2}/near/{3}'.format(stream_id, stream_name, topic_name, post_id))
    return zulip_url + '#narrow/stream/' + sanitized

# absolute url of a stream directory
def format_stream_url(stream_id, stream_name):
    return urllib.parse.urljoin(site_url, html_root, sanitize_stream(stream_name, stream_id))

# updates the "last updated" footer message to time `t`.
def write_last_updated(t):
    f = open_outfile(last_updated_dir, last_updated_file, 'w+')
    f.write('<hr><p>Last updated: {} UTC</p>'.format(t))
    f.close()

def write_css():
    copyfile('style.css', md_root / 'style.css')

# writes all markdown files to md_root, based on the archive at json_root.
def write_markdown():
    f = (json_root / Path('stream_index.json')).open('r', encoding='utf-8')
    stream_info = json.load(f, encoding='utf-8')
    f.close()
    streams = stream_info['streams']
    write_last_updated(str(stream_info['time']))
    write_stream_index(streams)
    write_css()
    for s in streams:
        print('building: ', s)
        write_topic_index(s, streams[s])
        for t in streams[s]['topic_data']:
            write_topic(s, streams[s], t)



# resets the current repository to match origin/master
def github_pull():
    print(subprocess.check_output(['git','fetch','origin','master']))
    print(subprocess.check_output(['git','reset','--hard','origin/master']))

# commits changes in archive/ and pushes the current repository to origin/master
def github_push():
    print(subprocess.check_output(['git','add','archive/*']))
    print(subprocess.check_output(['git','add','_includes/archive_update.html']))
    print(subprocess.check_output(['git','commit','-m','auto update: {}'.format(datetime.utcfromtimestamp(time.time()).strftime('%b %d %Y at %H:%M UTC'))]))
    print(subprocess.check_output(['git','push']))

parser = argparse.ArgumentParser(description='Build an html archive of the Zulip chat.')
parser.add_argument('-b', action='store_true', default=False, help='Build .md files')
parser.add_argument('-t', action='store_true', default=False, help='Make a clean json archive')
parser.add_argument('-i', action='store_true', default=False, help='Incrementally update the json archive')
parser.add_argument('-f', action='store_true', default=False, help='Pull from GitHub before updating. (Warning: could overwrite this script.)')
parser.add_argument('-p', action='store_true', default=False, help='Push results to GitHub.')

results = parser.parse_args()

read_config()

if results.t and results.i:
    print('Cannot perform both a total and incremental update. Use -t or -i.')
    exit()
if results.t:
    populate_all()
elif results.i:
    populate_incremental()
if results.f:
    github_pull()
if results.b:
    write_markdown()
if results.p:
    github_push()
