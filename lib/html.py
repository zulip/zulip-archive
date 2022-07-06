"""
All the functions in this file should produce pure HTML, as
opposed to Markdown or other similar languages.

Some folks want to work with systems that don't necessarily
support markdown (or deal with incompabilities between
different flavors of markdown), so when possible, we should
strive for pure HTML in our output in the future.

(Producing pure HTML doesn't have to be a burden--we can
add helpers/converters as necessary.)
"""

import html

from .date_helper import format_date1

from .url import (
    sanitize_stream,
    sanitize,
)

from .url import (
    archive_message_url,
    archive_stream_url,
    archive_topic_url,
    zulip_post_url,
)

from .zulip_data import (
    num_topics_string,
    sorted_streams,
    sorted_topics,
    topic_info_string,
)


def topic_page_links_html(
    site_url,
    html_root,
    zulip_url,
    sanitized_stream_name,
    sanitized_topic_name,
    stream_name,
    topic_name,
):
    stream_url = archive_stream_url(site_url, html_root, sanitized_stream_name)
    topic_url = archive_topic_url(
        site_url, html_root, sanitized_stream_name, sanitized_topic_name
    )

    return f"""\
<h2>Stream: <a href="{html.escape(stream_url)}">{html.escape(stream_name)}</a></h2>
<h3>Topic: <a href="{html.escape(topic_url)}">{html.escape(topic_name)}</a></h3>

<hr>

<base href="{html.escape(zulip_url)}">
"""


def format_message_html(
    site_url,
    html_root,
    zulip_url,
    zulip_icon_url,
    stream_name,
    stream_id,
    topic_name,
    msg,
):
    msg_id = str(msg["id"])

    zulip_link_html = link_to_zulip_html(
        zulip_url,
        zulip_icon_url,
        stream_id,
        stream_name,
        topic_name,
        msg_id,
    )

    user_name = msg["sender_full_name"]
    date = format_date1(msg["timestamp"])
    msg_content_html = msg["content"]
    anchor_url = archive_message_url(
        site_url,
        html_root,
        sanitize_stream(stream_name, stream_id),
        sanitize(topic_name),
        msg_id,
    )
    anchor_html = '<a name="{0}"></a>'.format(html.escape(msg_id))
    out_html = f"""
{anchor_html}
<h4>{zulip_link_html} {html.escape(user_name)} <a href="{html.escape(anchor_url)}">({html.escape(date)})</a>:</h4>
{msg_content_html}
"""
    return out_html


def link_to_zulip_html(
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
        img_tag_html = f'<img src="{html.escape(zulip_icon_url)}" alt="view this post on Zulip" style="width:20px;height:20px;">'
    else:
        img_tag_html = ""
    zulip_link_html = (
        f'<a href="{html.escape(post_link)}" class="zl">{img_tag_html}</a>'
    )
    return zulip_link_html


def last_updated_footer_html(stream_info):
    last_updated = format_date1(stream_info["time"])
    date_footer_html = f"\n<hr><p>Last updated: {html.escape(last_updated)} UTC</p>"
    return date_footer_html


def stream_list_page_html(streams):
    content_html = f"""\
<hr>

<h2>Streams:</h2>

{stream_list_html(streams)}
"""
    return content_html


def stream_list_html(streams):
    """
    produce a list like this:

    * stream_name (n topics)
    * stream_name (n topics)
    * stream_name (n topics)
    """

    def item_html(stream_name, stream_data):
        stream_id = stream_data["id"]
        sanitized_name = sanitize_stream(stream_name, stream_id)
        url = f"stream/{sanitized_name}/index.html"
        stream_topic_data = stream_data["topic_data"]
        num_topics = num_topics_string(stream_topic_data)
        return f'<li> <a href="{html.escape(url)}">{html.escape(stream_name)}</a> ({html.escape(str(num_topics))}) </li>'

    the_list = "\n\n".join(
        item_html(stream_name, streams[stream_name])
        for stream_name in sorted_streams(streams)
    )
    return "<ul>\n" + the_list + "\n</ul>"


def topic_list_page_html(stream_name, stream_url, topic_data):

    content = f"""\
<h2> Stream: <a href="{html.escape(stream_url)}">{html.escape(stream_name)}</a></h2>
<hr>

<h3>Topics:</h3>

{topic_list_html(topic_data)}
"""
    return content


def topic_list_html(topic_data):
    """
    produce a list like this:

    * topic name (n messages, latest: <date>)
    * topic name (n messages, latest: <date>)
    * topic name (n messages, latest: <date>)
    """

    def item_html(topic_name, message_data):
        link_html = f'<a href="topic/{html.escape(sanitize(topic_name))}.html">{html.escape(topic_name)}</a>'
        topic_info = topic_info_string(message_data)
        return f"<li> {link_html} ({html.escape(topic_info)}) </li>"

    the_list_html = "\n".join(
        item_html(topic_name, topic_data[topic_name])
        for topic_name in sorted_topics(topic_data)
    )
    return "<ul>\n" + the_list_html + "\n</ul>"
