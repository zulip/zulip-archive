"""
The functions here should be specific to how we store
Zulip data, without getting specific about HTML/Markdown
syntax.

The goal here is to have some functions that are resuable
for folks who may want to emit differently structured
HTML or markdown.
"""

from .date_helper import format_date1


def sorted_streams(streams):
    """
    Streams are sorted so that streams with the most topics
    go to the top.
    """
    return sorted(streams, key=lambda s: len(streams[s]["topic_data"]), reverse=True)


def sorted_topics(topic_data):
    """
    Topics are sorted so that the most recently updated
    topic is at the top of the list.
    """
    return sorted(
        topic_data, key=lambda tn: topic_data[tn]["latest_date"], reverse=True
    )


def num_topics_string(stream_topic_data):
    """
    example: "5 topics"
    """
    num_topics = len(stream_topic_data)
    plural = "" if num_topics == 1 else "s"
    return f"{num_topics} topic{plural}"


def topic_info_string(message_data):
    """
    n messages, latest: <date>
    """
    cnt = message_data["size"]
    plural = "" if cnt == 1 else "s"
    latest_date = message_data["latest_date"]
    date = format_date1(latest_date)
    return f"{cnt} message{plural}, latest: {date}"
