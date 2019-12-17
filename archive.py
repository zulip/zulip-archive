#!/usr/bin/env python3
#
# The workflow (timing for the leanprover Zulip chat, on my slow laptop):
# - populate_all() builds a json file in `settings.json_directory` for each topic,
#   containing message data and an index json file mapping streams to their topics.
#   This uses the Zulip API and takes ~10 minutes to crawl the whole chat.
# - populate_incremental() assumes there is already a json cache and collects only new messages.
# - write_markdown() builds markdown files in `settings.html_directory`
# - See hosting.md for suggestions on hosting.
#

from datetime import datetime
from pathlib import Path
from shutil import copyfile
from typing import Optional
import configparser
import zulip, os, json, urllib, argparse

from lib.common import (
    open_outfile,
    sanitize_stream,
    sanitize_topic,
    exit_immediately
    )

from lib.populate import (
    populate_all,
    populate_incremental
    )


try:
    import settings
except ModuleNotFoundError:
    # TODO: Add better instructions.
    exit_immediately('Please create a settings.py file.')

NO_JSON_DIR_ERROR_WRITE = '''
We cannot find a place to write JSON files.

Please run the below command:

mkdir {}'''

NO_JSON_DIR_ERROR_READ = '''
We cannot find a place to read JSON files.

Please run the below command:

mkdir {}

And then fetch the JSON:

python archive.py -t'''

NO_HTML_DIR_ERROR = '''
We cannot find a place to write HTML files.

Please run the below command:

mkdir {}'''

def get_json_directory(for_writing):
    json_dir = settings.json_directory

    if not json_dir.exists():
        # I use posix paths here, since even on Windows folks will
        # probably be using some kinda Unix-y shell to run mkdir.
        if for_writing:
            error_msg = NO_JSON_DIR_ERROR_WRITE.format(json_dir.as_posix())
        else:
            error_msg = NO_JSON_DIR_ERROR_READ.format(json_dir.as_posix())

        exit_immediately(error_msg)

    if not json_dir.is_dir():
        exit_immediately(str(json_dir) + ' needs to be a directory')

    return settings.json_directory

def get_html_directory():
    html_dir = settings.html_directory

    if not html_dir.exists():
        error_msg = NO_HTML_DIR_ERROR.format(html_dir.as_posix())

        exit_immediately(error_msg)

    if not html_dir.is_dir():
        exit_immediately(str(html_dir) + ' needs to be a directory')

    return settings.html_directory

# Globals

client = None
zulip_url = None
site_url = None
stream_whitelist = None
stream_blacklist = None
archive_title = None
html_root = None
md_index = None

def read_config():
    global client
    global zulip_url
    global site_url
    global stream_whitelist
    global stream_blacklist
    global archive_title
    global html_root
    global md_index

    def get_config(section: str, key: str, default_value: Optional[str]=None) -> Optional[str]:
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

    # user-facing path for the index
    html_root = get_config("archive", "html_root", "archive")

    md_index = Path("index.md")


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
def write_stream_index(md_root, streams, date_footer):
    outfile = open_outfile(md_root, md_index, 'w+')
    write_stream_index_header(outfile)
    for s in sorted(streams, key=lambda s: len(streams[s]['topic_data']), reverse=True):
        num_topics = len(streams[s]['topic_data'])
        outfile.write("* [{0}]({1}/index.html) ({2} topic{3})\n\n".format(
            s,
            sanitize_stream(s, streams[s]['id']),
            num_topics,
            '' if num_topics == 1 else 's'))
    outfile.write(date_footer)
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
def write_topic_index(md_root, stream_name, stream, date_footer):
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
    outfile.write(date_footer)
    outfile.close()

# formats the header for a topic page.
def write_topic_header(outfile, stream_name, stream_id, topic_name):
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
    outfile.write('\n<head><link href="/style.css" rel="stylesheet"></head>\n')

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
def write_topic(json_root, md_root, stream_name, stream, topic_name, date_footer):
    json_path = json_root / Path(sanitize_stream(stream_name, stream['id'])) / Path (sanitize_topic(topic_name) + '.json')
    f = json_path.open('r', encoding='utf-8')
    messages = json.load(f)
    f.close()
    o = open_outfile(md_root / Path(sanitize_stream(stream_name, stream['id'])), Path(sanitize_topic(topic_name) + '.html'), 'w+')
    write_topic_header(o, stream_name, stream['id'], topic_name)
    o.write('\n{% raw %}\n')
    write_topic_body(messages, stream_name, stream['id'], topic_name, o)
    o.write('\n{% endraw %}\n')
    o.write(date_footer)
    o.close()



## Nothing after this point should need to be modified.

# escape | character with \|
def escape_pipes(s):
    return s.replace('|','\|').replace(']','\]').replace('[','\[')

def test_valid(s):
    return s['name'] not in stream_blacklist and (True if stream_whitelist == [] else s['name'] in stream_whitelist)

## Display

# Create a link to a post on Zulip
def structure_link(stream_id, stream_name, topic_name, post_id):
    sanitized = urllib.parse.quote(
        '{0}-{1}/topic/{2}/near/{3}'.format(stream_id, stream_name, topic_name, post_id))
    return zulip_url + '#narrow/stream/' + sanitized

# absolute url of a stream directory
def format_stream_url(stream_id, stream_name):
    return urllib.parse.urljoin(site_url, html_root, sanitize_stream(stream_name, stream_id))

def write_css(md_root):
    copyfile('style.css', md_root / 'style.css')

# writes all markdown files to md_root, based on the archive at json_root.
def write_markdown(json_root, md_root):
    f = (json_root / Path('stream_index.json')).open('r', encoding='utf-8')
    stream_info = json.load(f, encoding='utf-8')
    f.close()
    streams = stream_info['streams']
    date_footer = '\n<hr><p>Last updated: {} UTC</p>'.format(stream_info['time'])
    write_stream_index(md_root, streams, date_footer)
    write_css(md_root)
    for s in streams:
        print('building: ', s)
        write_topic_index(md_root, s, streams[s], date_footer)
        for t in streams[s]['topic_data']:
            write_topic(json_root, md_root, s, streams[s], t, date_footer)

parser = argparse.ArgumentParser(description='Build an html archive of the Zulip chat.')
parser.add_argument('-b', action='store_true', default=False, help='Build .md files')
parser.add_argument('-t', action='store_true', default=False, help='Make a clean json archive')
parser.add_argument('-i', action='store_true', default=False, help='Incrementally update the json archive')

results = parser.parse_args()

if results.t and results.i:
    print('Cannot perform both a total and incremental update. Use -t or -i.')
    exit(1)

if not (results.t or results.i or results.b):
    print('\nERROR!\n\nYou have not specified any work to do.\n')
    parser.print_help()
    exit(1)

json_root = get_json_directory(for_writing=results.t)

if results.b:
    md_root = get_html_directory()

read_config()

if results.t:
    populate_all(
        client,
        json_root,
        test_valid
        )

elif results.i:
    populate_incremental(
        client,
        json_root,
        test_valid
        )

if results.b:
    write_markdown(json_root, md_root)
