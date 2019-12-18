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
from .common import (
    sanitize_stream,
    sanitize_topic,
    )

# writes the Jekyll header info for the index page listing all streams.
def write_stream_index_header(outfile, html_root, title):
    outfile.writelines([
        '---\n',
        'layout: archive\n',
        'title: {}\n'.format(title),
        'permalink: {}/index.html\n'.format(html_root),
        '---\n\n',
        ])

# writes the Jekyll header info for the index page for
# a given stream (which lists all the topics)
def write_topic_index_header(outfile, site_url, html_root, title, stream_name, stream):
    sanitized_stream_name = sanitize_stream(stream_name, stream['id'])

    permalink = 'permalink: {0}/{1}/index.html'.format(
        html_root,
        sanitized_stream_name,
    )

    outfile.writelines([
        '---\n',
        'layout: archive\n',
        'title: {}\n'.format(title),
        permalink,
        '\n---\n\n',
        ])


# formats the header for a topic page (which lists all
# the messages for a topic)
def write_topic_header(outfile, site_url, html_root, zulip_url, title, stream_name, stream_id, topic_name):
    sanitized_stream_name = sanitize_stream(stream_name, stream_id)
    sanitized_topic_name = sanitize_topic(topic_name)
    permalink = 'permalink: {0}/{1}/{2}.html'.format(
        html_root,
        sanitized_stream_name,
        sanitized_topic_name,
    )

    outfile.writelines([
        '---\n',
        'layout: archive\n',
        'title: {}\n'.format(title),
        permalink,
        '\n---\n\n',
        ])
