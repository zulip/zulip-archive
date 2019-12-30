'''
For historical reasons we generate some of our content in markdown,
which we then pass off to a static website engine like Jekyll to
render into HTML.

We may want to move toward just emitting pure HTML.
'''


from .url import (
    sanitize_stream,
    sanitize_topic,
    )

from .zulip_data import (
    num_topics_string,
    sorted_streams,
    sorted_topics,
    topic_info_string,
    )

def stream_list_page(streams):
    content = f'''\
---

## Streams:

{stream_list(streams)}
'''
    return content

def stream_list(streams):
    '''
    produce a list like this:

    * stream_name (n topics)
    * stream_name (n topics)
    * stream_name (n topics)
    '''

    def item(stream_name, stream_data):
        stream_id = stream_data['id']
        sanitized_name = sanitize_stream(stream_name, stream_id)
        url = f'stream/{sanitized_name}/index.html'
        stream_topic_data = stream_data['topic_data']
        num_topics = num_topics_string(stream_topic_data)
        return f'* [{stream_name}]({url}) ({num_topics})'

    return '\n\n'.join(
        item(stream_name, streams[stream_name])
        for stream_name
        in sorted_streams(streams))

def topic_list_page(stream_name, stream_url, topic_data):

    content = f'''\
## Stream: [{stream_name}]({stream_url})
---

### Topics:

{topic_list(topic_data)}
'''
    return content

def topic_list(topic_data):
    '''
    produce a list like this:

    * topic name (n messages, latest: <date>)
    * topic name (n messages, latest: <date>)
    * topic name (n messages, latest: <date>)
    '''

    def item(topic_name, message_data):
        link = f'[{escape_pipes(topic_name)}](topic/{sanitize_topic(topic_name)}.html)'
        topic_info = topic_info_string(message_data)
        return f'* {link} ({topic_info})'

    return '\n'.join(
        item(topic_name, topic_data[topic_name])
        for topic_name
        in sorted_topics(topic_data))

# escape | character with \|
def escape_pipes(s):
    return s.replace('|','\|').replace(']','\]').replace('[','\[')

