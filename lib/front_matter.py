'''
This code is used to produce "front matter" for Jekyll.

    https://jekyllrb.com/docs/front-matter/

If you are not using Jekyll to serve your archive, then
you should be able to ignore this entire module!

Jekyll front matter is YAML.  It includes basic directives
like the following:

    ---
    layout: archive
    title: Zulip Chat Archive
    permalink: archive/index.html
    ---

The Jekyll code reads those lines to set up layout and
create nice URLs for your pages.
'''
from .url import (
    sanitize_stream,
    sanitize_topic,
    )

def write_main_page_header(outfile, html_root, title):
    outfile.writelines([
        '---\n',
        'layouts: archive\n',
        'title: {}\n'.format(title),
        'permalink: {}/index.html\n'.format(html_root),
        '---\n\n',
        ])

def write_stream_topics_header(outfile, site_url, html_root, title, stream_name, stream):
    sanitized_stream_name = sanitize_stream(stream_name, stream['id'])

    permalink = 'permalink: {0}/stream/{1}/index.html'.format(
        html_root,
        sanitized_stream_name,
    )

    outfile.writelines([
        '---\n',
        'layouts: archive\n',
        'title: {}\n'.format(title),
        permalink,
        '\n---\n\n',
        ])


def write_topic_messages_header(outfile, site_url, html_root, zulip_url, title, stream_name, stream_id, topic_name):
    sanitized_stream_name = sanitize_stream(stream_name, stream_id)
    sanitized_topic_name = sanitize_topic(topic_name)
    permalink = 'permalink: {0}/stream/{1}/topic/{2}.html'.format(
        html_root,
        sanitized_stream_name,
        sanitized_topic_name,
    )

    outfile.writelines([
        '---\n',
        'layouts: archive\n',
        'title: {}\n'.format(title),
        permalink,
        '\n---\n\n',
        ])
