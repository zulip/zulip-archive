'''
All the functions in this file should produce pure HTML, as
opposed to Markdown or other similar languages.

Some folks want to work with systems that don't necessarily
support markdown (or deal with incompabilities between
different flavors of markdown), so when possible, we should
strive for pure HTML in our output in the future.

(Producing pure HTML doesn't have to be a burden--we can
add helpers/converters as necessary.)
'''

from .date_helper import format_date1

from .url import (
    sanitize_stream,
    sanitize_topic,
    )

from .url import (
    archive_message_url,
    archive_stream_url,
    archive_topic_url,
    zulip_post_url,
    )

def topic_page_links(
        site_url,
        html_root,
        zulip_url,
        sanitized_stream_name,
        sanitized_topic_name,
        stream_name,
        topic_name,
        ):
    stream_url = archive_stream_url(site_url, html_root, sanitized_stream_name)
    topic_url = archive_topic_url(site_url, html_root, sanitized_stream_name, sanitized_topic_name)

    return f'''\
<h2>Stream: <a href="{stream_url}">{stream_name}</a>
<h3>Topic: <a href="{topic_url}">{topic_name}</a></h3>

<hr>

<base href="{zulip_url}">
'''

def format_message(
        site_url,
        html_root,
        zulip_url,
        zulip_icon_url,
        stream_name,
        stream_id,
        topic_name,
        msg
        ):
    msg_id = str(msg['id'])

    zulip_link = link_to_zulip(
        zulip_url,
        zulip_icon_url,
        stream_id,
        stream_name,
        topic_name,
        msg_id,
        )

    user_name = msg['sender_full_name']
    date = format_date1(msg['timestamp'])
    msg_content = msg['content']
    anchor_url = archive_message_url(
        site_url,
        html_root,
        sanitize_stream(stream_name, stream_id),
        sanitize_topic(topic_name),
        msg_id
        )
    anchor = '<a name="{0}"></a>'.format(msg_id)
    html = f'''
{anchor}
<h4>{zulip_link} {user_name} <a href="{anchor_url}">({date})</a>:</h4>
{msg_content}
'''
    return html


def link_to_zulip(
        zulip_url,
        zulip_icon_url,
        stream_id,
        stream_name,
        topic_name,
        msg_id,
        ):
    # format a link to the original post where you click on the Zulip icon
    # (if it's available)
    post_link = zulip_post_url(zulip_url, stream_id, stream_name, topic_name, msg_id)
    if zulip_icon_url:
        img_tag = f'<img src="{zulip_icon_url}" alt="view this post on Zulip">'
    else:
        img_tag = ''
    zulip_link = f'<a href="{post_link}" class="zl">{img_tag}</a>'
    return zulip_link

def last_updated_footer(stream_info):
    last_updated = format_date1(stream_info['time'])
    date_footer = f'\n<hr><p>Last updated: {last_updated} UTC</p>'
    return date_footer

