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
    stream_validator,
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
    exit_immediately('''
    We can't find settings.py.

    Please copy default_settings.py to settings.py
    and then edit the settings.py file to fit your use case.

    For testing, you can often leave the default settings,
    but you will still want to review them first.
    ''')

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

def get_client_info():
    config_file = './zuliprc'
    client = zulip.Client(config_file=config_file)

    # It would be convenient if the Zulip client object
    # had a `site` field, but instead I just re-read the file
    # directly to get it.
    config = configparser.RawConfigParser()
    config.read(config_file)
    zulip_url = config.get('api', 'site')

    return client, zulip_url

# When generating displayable md/html, we create the following structure inside md_root:
# * index.md displays a list of all streams
# * for each stream str, str/index.md displays a list of all topics in str
# * for each topic top in a stream str, str/top.html displays the posts in top.
#
# Some sanitization is needed to ensure that urls are unique and acceptable.
# Use sanitize_stream(stream_name, stream_id) in place of str above.
# Use sanitize_topic(topic_name) in place of top.
#
# The topic display must be an html file, since we use the html provided by Zulip.
# The index pages are generated in markdown by default, but this can be changed to html.
# The default settings are designed for a Jekyll build.

# writes the Jekyll header info for the index page listing all streams.
def write_stream_index_header(outfile, html_root, title):
    outfile.writelines([
        '---\n',
        'layout: archive\n',
        'title: {}\n'.format(title),
        'permalink: {}/index.html\n'.format(html_root),
        '---\n\n',
        '---\n\n',
        '## Streams:\n\n',
        ])

# writes the index page listing all streams.
# `streams`: a dict mapping stream names to stream json objects as described in the header.
def write_stream_index(md_root, site_url, html_root, title, streams, date_footer):
    outfile = open_outfile(md_root, Path('index.md'), 'w+')
    write_stream_index_header(outfile, html_root, title)
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
def write_topic_index_header(outfile, site_url, html_root, title, stream_name, stream):
    sanitized_stream_name = sanitize_stream(stream_name, stream['id'])
    stream_url = format_stream_url(site_url, html_root, sanitized_stream_name)

    permalink = 'permalink: {0}/{1}/index.html'.format(
        html_root,
        sanitized_stream_name,
    )

    strm = f'## Stream: [{stream_name}]({stream_url})'

    outfile.writelines([
        '---\n',
        'layout: archive\n',
        'title: {}\n'.format(title),
        permalink,
        '\n---\n\n',
        strm,
        '\n---\n\n',
        '### Topics:\n\n',
        ])

# writes an index page for a given stream, printing a list of the topics in that stream.
# `stream_name`: the name of the stream.
# `stream`: a stream json object as described in the header
def write_topic_index(md_root, site_url, html_root, title, stream_name, stream, date_footer):
    directory = md_root / Path(sanitize_stream(stream_name, stream['id']))
    outfile = open_outfile(directory, Path('index.md'), 'w+')
    write_topic_index_header(outfile, site_url, html_root, title, stream_name, stream)
    for topic_name in sorted(stream['topic_data'], key=lambda tn: stream['topic_data'][tn]['latest_date'], reverse=True):
        t = stream['topic_data'][topic_name]
        outfile.write("* [{0}]({1}.html) ({2} message{3}, latest: {4})\n".format(
            escape_pipes(topic_name),
            sanitize_topic(topic_name),
            t['size'],
            '' if t['size'] == 1 else 's',
            datetime.utcfromtimestamp(t['latest_date']).strftime('%b %d %Y at %H:%M'),
        ))
    outfile.write(date_footer)
    outfile.close()

# formats the header for a topic page.
def write_topic_header(outfile, site_url, html_root, zulip_url, title, stream_name, stream_id, topic_name):
    sanitized_stream_name = sanitize_stream(stream_name, stream_id)
    sanitized_topic_name = sanitize_topic(topic_name)
    stream_url = format_stream_url(site_url, html_root, sanitized_stream_name)
    topic_url = format_topic_url(site_url, html_root, sanitized_stream_name, sanitized_topic_name)

    permalink = 'permalink: {0}/{1}/{2}.html'.format(
        html_root,
        sanitized_stream_name,
        sanitized_topic_name,
    )

    strm = f'<h2>Stream: <a href="{stream_url}">{stream_name}</a>'

    tpc = f'<h3>Topic: <a href="{topic_url}">{topic_name}</a></h3>'

    outfile.writelines([
        '---\n',
        'layout: archive\n',
        'title: {}\n'.format(title),
        permalink,
        '\n---\n\n',
        strm,
        '\n',
        tpc,
        '\n\n<hr>\n\n',
        '<base href="{}">\n'.format(zulip_url),
        ])
    outfile.write('\n<head><link href="/style.css" rel="stylesheet"></head>\n')

# formats a single post in a topic
# Note: the default expects the Zulip "Z" icon at site_url+'assets/img/zulip2.png'
def format_message(site_url, user_name, date, msg, link, anchor_name, anchor_url):
    anchor = '<a name="{0}"></a>'.format(anchor_name)
    zulip_link = '<a href="{0}" class="zl"><img src="{1}" alt="view this post on Zulip"></a>'.format(link, site_url+'assets/img/zulip2.png')
    local_link = '<a href="{0}">{1} ({2})</a>'.format(anchor_url, user_name, date)
    return '{0}\n<h4>{1} {2}:</h4>\n{3}'.format(anchor, zulip_link, local_link, msg)


# writes the body of a topic page (ie, a list of messages)
# `messages`: a list of message json objects, as defined in the Zulip API
def write_topic_body(site_url, html_root, zulip_url, messages, stream_name, stream_id, topic_name, outfile):
    for c in messages:
        name = c['sender_full_name']
        date = datetime.utcfromtimestamp(c['timestamp']).strftime('%b %d %Y at %H:%M')
        msg = c['content']
        link = structure_link(zulip_url, stream_id, stream_name, topic_name, c['id'])
        anchor_name = str(c['id'])
        anchor_link = '{0}/{1}/{2}.html#{3}'.format(
            urllib.parse.urljoin(site_url, html_root),
            sanitize_stream(stream_name, stream_id),
            sanitize_topic(topic_name),
            anchor_name)
        outfile.write(format_message(site_url, name, date, msg, link, anchor_name, anchor_link))
        outfile.write('\n\n')


# writes a topic page.
# `stream`: a stream json object as defined in the header
def write_topic(
        json_root,
        md_root,
        site_url,
        html_root,
        title,
        zulip_url,
        stream_name,
        stream,
        topic_name,
        date_footer,
        ):
    json_path = json_root / Path(sanitize_stream(stream_name, stream['id'])) / Path (sanitize_topic(topic_name) + '.json')
    f = json_path.open('r', encoding='utf-8')
    messages = json.load(f)
    f.close()
    o = open_outfile(md_root / Path(sanitize_stream(stream_name, stream['id'])), Path(sanitize_topic(topic_name) + '.html'), 'w+')
    write_topic_header(o, site_url, html_root, zulip_url, title, stream_name, stream['id'], topic_name)
    o.write('\n{% raw %}\n')
    write_topic_body(site_url, html_root, zulip_url, messages, stream_name, stream['id'], topic_name, o)
    o.write('\n{% endraw %}\n')
    o.write(date_footer)
    o.close()

# escape | character with \|
def escape_pipes(s):
    return s.replace('|','\|').replace(']','\]').replace('[','\[')

# Create a link to a post on Zulip
def structure_link(zulip_url, stream_id, stream_name, topic_name, post_id):
    sanitized = urllib.parse.quote(
        '{0}-{1}/topic/{2}/near/{3}'.format(stream_id, stream_name, topic_name, post_id))
    return zulip_url + '#narrow/stream/' + sanitized

def format_stream_url(site_url, html_root, sanitized_stream_name):
    path = f'{html_root}/{sanitized_stream_name}/index.html'
    return urllib.parse.urljoin(site_url, path)

def format_topic_url(site_url, html_root, sanitized_stream_name, sanitized_topic_name):
    path = f'{html_root}/{sanitized_stream_name}/{sanitized_topic_name}.html'
    return urllib.parse.urljoin(site_url, path)

def write_css(md_root):
    copyfile('style.css', md_root / 'style.css')

# writes all markdown files to md_root, based on the archive at json_root.
def write_markdown(json_root, md_root, site_url, html_root, title, zulip_url):
    f = (json_root / Path('stream_index.json')).open('r', encoding='utf-8')
    stream_info = json.load(f, encoding='utf-8')
    f.close()
    streams = stream_info['streams']
    date_footer = '\n<hr><p>Last updated: {} UTC</p>'.format(stream_info['time'])
    write_stream_index(md_root, site_url, html_root, title, streams, date_footer)
    write_css(md_root)

    for s in streams:
        print('building: ', s)
        write_topic_index(md_root, site_url, html_root, title, s, streams[s], date_footer)
        for t in streams[s]['topic_data']:
            write_topic(
                json_root,
                md_root,
                site_url,
                html_root,
                title,
                zulip_url,
                s,
                streams[s],
                t,
                date_footer,
                )

def run():
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

    if results.t or results.i:
        is_valid_stream_name = stream_validator(settings)

    client, zulip_url = get_client_info()

    if results.t:
        populate_all(
            client,
            json_root,
            is_valid_stream_name,
            )

    elif results.i:
        populate_incremental(
            client,
            json_root,
            is_valid_stream_name,
            )

    if results.b:
        write_markdown(
            json_root,
            md_root,
            settings.site_url,
            settings.html_root,
            settings.title,
            zulip_url
            )

if __name__ == '__main__':
    run()
