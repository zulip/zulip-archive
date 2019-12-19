'''
This module emits the content for your archive.

It emits markdown, HTML, and YAML, mostly by calling
into other modules.

As I write this today (December 2019), we are mostly testing with
Jekyll, so the output is geared toward a Jekyll system, which
is what GitHub Pages uses, too.  We will try to make this more
flexible as we go.

This module is probably the most likely module to be forked if
you have unique requirements for how your archive should look.

If you are interest in porting this system away from Python to your
language of choice, this is probably the best place to start.
'''

import json

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

from .html import (
    format_message,
    last_updated_footer,
    topic_page_links,
    )

from .markdown import (
    stream_list_page,
    topic_list_page,
    )

from .url import (
    archive_stream_url,
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
def write_markdown(json_root, md_root, site_url, html_root, title, zulip_url, zulip_icon_url):
    f = (json_root / Path('stream_index.json')).open('r', encoding='utf-8')
    stream_info = json.load(f, encoding='utf-8')
    f.close()

    streams = stream_info['streams']
    date_footer = last_updated_footer(stream_info)
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
                zulip_icon_url,
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

    content = stream_list_page(streams)

    outfile.write(content)
    outfile.write(date_footer)
    outfile.close()

def write_topic_index(md_root, site_url, html_root, title, stream_name, stream, date_footer):
    sanitized_stream_name = sanitize_stream(stream_name, stream['id'])
    directory = md_root / Path(sanitized_stream_name)
    outfile = open_outfile(directory, Path('index.md'), 'w+')
    write_topic_index_header(outfile, site_url, html_root, title, stream_name, stream)

    stream_url = archive_stream_url(site_url, html_root, sanitized_stream_name)

    topic_data = stream['topic_data']

    content = topic_list_page(stream_name, stream_url, topic_data)

    outfile.write(content)
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
        zulip_icon_url,
        stream_name,
        stream,
        topic_name,
        date_footer,
        ):
    stream_id = stream['id']

    sanitized_stream_name = sanitize_stream(stream_name, stream_id)
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
        stream_id,
        topic_name,
        )

    topic_links = topic_page_links(
        site_url,
        html_root,
        zulip_url,
        sanitized_stream_name,
        sanitized_topic_name,
        stream_name,
        topic_name,
        )
    o.write(topic_links)

    o.write('\n<head><link href="/style.css" rel="stylesheet"></head>\n')

    o.write('\n{% raw %}\n')

    for msg in messages:
        msg_html = format_message(
                site_url,
                html_root,
                zulip_url,
                zulip_icon_url,
                stream_name,
                stream_id,
                topic_name,
                msg,
                )
        o.write(msg_html)
        o.write('\n\n')

    o.write('\n{% endraw %}\n')

    o.write(date_footer)
    o.close()

def write_css(md_root):
    copyfile('style.css', md_root / 'style.css')

# escape | character with \|
def escape_pipes(s):
    return s.replace('|','\|').replace(']','\]').replace('[','\[')
