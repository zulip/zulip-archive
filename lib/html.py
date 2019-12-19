'''
This module emits the HTML (plus some markdown, and, indirectly,
some YAML) for your archive.

This module is probably the most likely module to be forked if
you have unique requirements for how your archive should look.

If you are interest in porting this system away from Python to your
language of choice, this is probably the best place to start.

As I write this today (December 2019), we are mostly testing with
Jekyll, so the output is geared toward a Jekyll system, which
is what GitHub Pages uses, too.  We will try to make this more
flexible as we go.
'''

import json
import urllib

from datetime import datetime
from pathlib import Path
from shutil import copyfile

from .common import (
    open_outfile,
    sanitize_stream,
    sanitize_topic,
    )

from .front_matter import (
    write_stream_index_header,
    write_topic_index_header,
    write_topic_header,
    )

# Here are some more comments from the initial implementation:
#
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


# writes the index page listing all streams.
# `streams`: a dict mapping stream names to stream json objects as described in the header.
def write_stream_index(md_root, site_url, html_root, title, streams, date_footer):
    outfile = open_outfile(md_root, Path('index.md'), 'w+')
    write_stream_index_header(outfile, html_root, title)

    outfile.write('---\n\n')
    outfile.write('## Streams:\n\n')
    for s in sorted_streams(streams):
        num_topics = len(streams[s]['topic_data'])
        outfile.write("* [{0}]({1}/index.html) ({2} topic{3})\n\n".format(
            s,
            sanitize_stream(s, streams[s]['id']),
            num_topics,
            '' if num_topics == 1 else 's'))
    outfile.write(date_footer)
    outfile.close()

def sorted_streams(streams):
    '''
    Streams are sorted so that streams with the most topics
    go to the top.
    '''
    return sorted(
        streams,
        key=lambda s: len(streams[s]['topic_data']),
        reverse=True
        )

# writes an index page for a given stream, printing a list of the topics in that stream.
# `stream_name`: the name of the stream.
# `stream`: a stream json object as described in the header
def write_topic_index(md_root, site_url, html_root, title, stream_name, stream, date_footer):
    sanitized_stream_name = sanitize_stream(stream_name, stream['id'])
    directory = md_root / Path(sanitized_stream_name)
    outfile = open_outfile(directory, Path('index.md'), 'w+')
    write_topic_index_header(outfile, site_url, html_root, title, stream_name, stream)

    stream_url = format_stream_url(site_url, html_root, sanitized_stream_name)

    outfile.writelines([
        f'## Stream: [{stream_name}]({stream_url})',
        '\n---\n\n',
        '### Topics:\n\n',
        ])

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
    sanitized_stream_name = sanitize_stream(stream_name, stream['id'])
    sanitized_topic_name = sanitize_topic(topic_name)

    json_path = json_root / Path(sanitized_stream_name) / Path (sanitized_topic_name + '.json')
    f = json_path.open('r', encoding='utf-8')
    messages = json.load(f)
    f.close()

    o = open_outfile(md_root / Path(sanitized_stream_name), Path(sanitized_topic_name + '.html'), 'w+')

    write_topic_header(
        o,
        site_url,
        html_root,
        zulip_url,
        title,
        stream_name,
        stream['id'],
        topic_name,
        )

    write_topic_links(
        o,
        site_url,
        html_root,
        zulip_url,
        sanitized_stream_name,
        sanitized_topic_name,
        stream_name,
        topic_name,
        )

    o.write('\n<head><link href="/style.css" rel="stylesheet"></head>\n')

    o.write('\n{% raw %}\n')
    write_topic_body(site_url, html_root, zulip_url, messages, stream_name, stream['id'], topic_name, o)
    o.write('\n{% endraw %}\n')

    o.write(date_footer)
    o.close()

def write_topic_links(
        outfile,
        site_url,
        html_root,
        zulip_url,
        sanitized_stream_name,
        sanitized_topic_name,
        stream_name,
        topic_name,
        ):
    stream_url = format_stream_url(site_url, html_root, sanitized_stream_name)
    topic_url = format_topic_url(site_url, html_root, sanitized_stream_name, sanitized_topic_name)

    outfile.writelines([
        f'<h2>Stream: <a href="{stream_url}">{stream_name}</a>',
        '\n',
        f'<h3>Topic: <a href="{topic_url}">{topic_name}</a></h3>',
        '\n\n<hr>\n\n',
        '<base href="{}">\n'.format(zulip_url),
        ])


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


def write_css(md_root):
    copyfile('style.css', md_root / 'style.css')


# formats a single post in a topic
# Note: the default expects the Zulip "Z" icon at site_url+'assets/img/zulip2.png'
def format_message(site_url, user_name, date, msg, link, anchor_name, anchor_url):
    anchor = '<a name="{0}"></a>'.format(anchor_name)
    zulip_link = '<a href="{0}" class="zl"><img src="{1}" alt="view this post on Zulip"></a>'.format(link, site_url+'assets/img/zulip2.png')
    local_link = '<a href="{0}">{1} ({2})</a>'.format(anchor_url, user_name, date)
    return '{0}\n<h4>{1} {2}:</h4>\n{3}'.format(anchor, zulip_link, local_link, msg)


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

