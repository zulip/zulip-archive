# requires python 3
#
# The workflow (timing on my laptop):
# - populate_all() builds a json file in `json_root` for each topic, containing message data,
#   and an index json file mapping streams to their topics.
#   This uses the Zulip API and takes ~10 minutes to crawl the whole chat.
# - populate_incremental() assumes there is already a json cache and collects only new messages.
# - write_markdown() builds markdown files in `md_index` from the json. This takes ~15 seconds.
# - This markdown can be pushed directly to GitHub or built locally with `jekyll serve --incremental`.
#   Building locally takes about 1 minute.
#
# The json format for stream_index.md is:
# { 'time': the last time stream_index.md was updated,
#   'streams': { stream_name: { 'id': stream_id,
#                               'latest_id': id of latest post in stream,
#                               'topic_data': { topic_name: { topic_size: num posts in topic,
#                                                            latest_date: time of latest post }}}}}

from datetime import date, datetime
from pathlib import Path
from zlib import adler32
import zulip, string, os, time, json, urllib, argparse, subprocess

json_root = Path("./_json")
md_root = Path("archive")
md_index = Path("index.md")
html_root = Path("archive")
last_updated_path = Path("_includes/archive_update.html")
site_url = "https://leanprover-community.github.io/"
stream_blacklist = ['rss', 'travis', 'announce']

# config_file should point to a Zulip api config
client = zulip.Client(config_file="./.zuliprc")

## String cleaning functions

# remove non-alnum ascii symbols from string
def sanitize(s):
    return "".join(filter(str.isalnum, s.encode('ascii', 'ignore').decode('utf-8')))

# create a unique sanitized identifier for a topic
def sanitize_topic(topic_name):
    i = str(adler32(topic_name.encode('utf-8')) % (10 ** 5)).zfill(5)
    return i + sanitize(topic_name)

# create a unique sanitized identifier for a stream
def sanitize_stream(stream_name, stream_id):
    return str(stream_id) + sanitize(stream_name)

# escape | character with \|
def escape_pipes(s):
    return s.replace('|','\|').replace(']','\]').replace('[','\[')

## retrieve information from Zulip

# runs client.cmd(args). If the response is a rate limit error, waits the requested time and tries again.
def safe_request(cmd, args):
    rsp = cmd(*args)
    while rsp['result'] == 'error':
        print("timeout hit: {}".format(rsp['retry-after']))
        time.sleep(float(rsp['retry-after']) + 1)
        rsp = cmd(*args)
    return rsp

# Safely open dir/filename, creating dir if it doesn't exist
def open_outfile(dir, filename, mode):
    if not dir.exists():
        dir.mkdir()
    return (dir / filename).open(mode, encoding='utf-8')

# Retrieves all messages matching request from Zulip, starting at post id anchor.
# As recommended in the Zulip API docs, requests 1000 messages at a time.
# Returns a list of messages.
def request_all(request, anchor=0):
    request['anchor'] = anchor
    request['num_before'] = 0
    request['num_after'] = 1000
    response = safe_request(client.get_messages, [request])
    msgs = response['messages']
    while not response['found_newest']:
        request['anchor'] = response['messages'][-1]['id'] + 1
        response = safe_request(client.get_messages, [request])
        msgs = msgs + response['messages']
    return msgs

# Takes a list of messages. Returns a dict mapping topic names to lists of messages in that topic.
def separate_results(list):
    map = {}
    for m in list:
        if m['subject'] not in map:
            map[m['subject']] = [m]
        else:
            map[m['subject']].append(m)
    return map

# Retrieves only new messages from Zulip, based on timestamps from the last update.
# Raises an exception if there is no index at json_root/stream_index.json
def populate_incremental():
    streams = safe_request(client.get_streams, [])['streams']
    stream_index = json_root / Path('stream_index.json')
    if not stream_index.exists():
        raise Exception('stream index does not exist at {}\nCannot update incrementally without an index.'.format(stream_index))
    f = stream_index.open('r', encoding='utf-8')
    stream_index = json.load(f, encoding='utf-8')
    f.close()
    for s in (s for s in streams if s['name'] not in stream_blacklist):
        print(s['name'])
        if s['name'] not in stream_index['streams']:
            stream_index['streams'][s['name']] = {'id':s['stream_id'], 'latest_id':0, 'topic_data':{}}
        request = {'narrow':[{'operator':'stream', 'operand':s['name']}], 'client_gravatar': True,
                   'apply_markdown': True}
        new_msgs = request_all(request, stream_index['streams'][s['name']]['latest_id']+1)
        if len(new_msgs) > 0:
            stream_index['streams'][s['name']]['latest_id'] = new_msgs[-1]['id']
        nm = separate_results(new_msgs)
        for t in nm:
            p = json_root / Path(sanitize_stream(s['name'], s['stream_id'])) / Path(sanitize_topic(t) + '.json')
            topic_exists = p.exists()
            old = []
            if topic_exists:
                f = p.open('r', encoding='utf-8')
                old = json.load(f)
                f.close()
            m = nm[t]
            new_topic_data = {'size': len(m)+len(old),
                                'latest_date': m[-1]['timestamp']}
            stream_index['streams'][s['name']]['topic_data'][t] = new_topic_data
            out = open_outfile(json_root / Path(sanitize_stream(s['name'], s['stream_id'])),
                               Path(sanitize_topic(t) + '.json'), 'w')
            json.dump(old+m, out, ensure_ascii=False)
            out.close()
    stream_index['time'] = datetime.utcfromtimestamp(time.time()).strftime('%b %d %Y at %H:%M')
    out = open_outfile(json_root, Path('stream_index.json'), 'w')
    json.dump(stream_index, out, ensure_ascii = False)
    out.close()

# Retrieves all messages from Zulip and builds a cache at json_root.
def populate_all():
    streams = safe_request(client.get_streams, [])['streams']
    ind = {}
    for s in (s for s in streams if s['name'] not in stream_blacklist):
        print(s['name'])
        topics = safe_request(client.get_stream_topics, [s['stream_id']])['topics']
        nind = {'id': s['stream_id'], 'latest_id':0}
        tpmap = {}
        for t in topics:
            request = {
                'narrow': [{'operator': 'stream', 'operand': s['name']},
                           {'operator': 'topic', 'operand': t['name']}],
                'client_gravatar': True,
                'apply_markdown': True
            }
            m = request_all(request)
            tpmap[t['name']] = {'size': len(m),
                                'latest_date': m[-1]['timestamp']}
            nind['latest_id'] = max(nind['latest_id'], m[-1]['id'])
            out = open_outfile(json_root / Path(sanitize_stream(s['name'], s['stream_id'])),
                               Path(sanitize_topic(t['name']) + '.json'), 'w')
            json.dump(m, out, ensure_ascii=False)
            out.close()
        nind['topic_data'] = tpmap
        ind[s['name']] = nind
    js = {'streams':ind, 'time':datetime.utcfromtimestamp(time.time()).strftime('%b %d %Y at %H:%M')}
    out = open_outfile(json_root, Path('stream_index.json'), 'w')
    json.dump(js, out, ensure_ascii = False)
    out.close()




## Display

# Create a link to a post on Zulip
def structure_link(stream_id, stream_name, topic_name, post_id):
    sanitized = urllib.parse.quote(
        '{0}-{1}/topic/{2}/near/{3}'.format(stream_id, stream_name, topic_name, post_id))
    return 'https://leanprover.zulipchat.com/#narrow/stream/' + sanitized

# absolute url of a stream directory
def format_stream_url(stream_id, stream_name):
    return site_url + str(html_root) + '/' + sanitize_stream(stream_name, stream_id)

# formats a single post
def format_message(name, date, msg, link, anchor_name, anchor_url):
    #return u'<a name="{4}"></a>\n #### [![view this post on Zulip]({5}/assets/img/zulip2.png)]({3}) [ {0} ({1})]({6}):\n{2}'.format(name, date, msg, link, anchor_name, site_url, anchor_url)
    anchor = '<a name="{0}"></a>'.format(anchor_name)
    zulip_link = '<a href="{0}" class="zl"><img src="{1}" alt="view this post on Zulip"></a>'.format(link, site_url+'assets/img/zulip2.png')
    local_link = '<a href="{0}">{1} ({2})</a>'.format(anchor_url, name, date)
    return '{0}\n<h4>{1} {2}:</h4>\n{3}'.format(anchor, zulip_link, local_link, msg)
    #return u'<a name="{4}"></a>\n #### [![view this post on Zulip]({5}/assets/img/zulip2.png)]({3}) [ {0} ({1})]({6}):\n{2}'.format(name, date, msg, link, anchor_name, site_url, anchor_url)

# writes the body of a topic page (ie, a list of messages)
def write_topic(messages, stream_name, stream_id, topic_name, outfile):
    for c in messages:
        name = c['sender_full_name']
        date = datetime.utcfromtimestamp(c['timestamp']).strftime('%b %d %Y at %H:%M')
        msg = c['content']
        link = structure_link(stream_id, stream_name, topic_name, c['id'])
        anchor_name = str(c['id'])
        anchor_link = '{0}{4}/{1}/{2}.html#{3}'.format(
            site_url,
            sanitize_stream(stream_name, stream_id),
            sanitize_topic(topic_name),
            anchor_name,
            html_root)
        outfile.write(format_message(name, date, msg, link, anchor_name, anchor_link))
        outfile.write('\n\n')

# writes an index page for a given stream, printing a list of the topics in that stream.
# `s_name`: the name of the stream. `s`: a json object as described in the header
def write_topic_index(s_name, s):
    directory = md_root / Path(sanitize_stream(s_name, s['id']))
    outfile = open_outfile(directory, md_index, 'w+')
    header = ("---\nlayout: archive\ntitle: Lean Prover Zulip Chat Archive\npermalink: {2}/{1}/index.html\n---\n\n" +
            "## Stream: [{0}]({3}/index.html)\n\n---\n\n### Topics:\n\n").format(
                s_name,
                sanitize_stream(s_name, s['id']),
                html_root,
                format_stream_url(s['id'], s_name))
    outfile.write(header)
    for topic_name in sorted(s['topic_data'], key=lambda tn: s['topic_data'][tn]['latest_date'], reverse=True): #s['topic_data']:
        t = s['topic_data'][topic_name]
        outfile.write("* [{0}]({1}.html) ({2} message{4}, latest: {3})\n\n".format(
            escape_pipes(topic_name),
            sanitize_topic(topic_name),
            t['size'],
            datetime.utcfromtimestamp(t['latest_date']).strftime('%b %d %Y at %H:%M'),
            '' if t['size'] == 1 else 's'
        ))
    outfile.write('\n{% include archive_update.html %}')
    outfile.close()

# writes the index page listing all streams.
# `streams`: a dict mapping stream names to stream json objects as described in the header.
def write_stream_index(streams):
    outfile = (md_root / md_index).open('w+', encoding='utf-8')
    outfile.write("---\nlayout: archive\ntitle: Lean Prover Zulip Chat Archive\npermalink: {}/index.html\n---\n\n---\n\n## Streams:\n\n".format(html_root))
    for s in sorted(streams, key=lambda s: len(streams[s]['topic_data']), reverse=True):
        num_topics = len(streams[s]['topic_data'])
        outfile.write("* [{0}]({1}/index.html) ({2} topic{3})\n\n".format(
            s,
            sanitize_stream(s, streams[s]['id']),
            num_topics,
            '' if num_topics == 1 else 's'))
    outfile.write('\n{% include archive_update.html %}')
    outfile.close()

# formats the header for a topic page.
def format_topic_header(stream_name, stream_id, topic_name):
    return ("---\nlayout: archive\ntitle: Lean Prover Zulip Chat Archive \npermalink: {4}/{2}/{3}.html\n---\n\n" +
            '<h2>Stream: <a href="{5}/index.html">{0}</a>\n<h3>Topic: <a href="{5}/{3}.html">{1}</a></h3>\n\n<hr>\n\n<base href="https://leanprover.zulipchat.com">').format(
                stream_name,
                topic_name,
                sanitize_stream(stream_name, stream_id),
                sanitize_topic(topic_name),
                html_root,
                format_stream_url(stream_id, stream_name))

# writes a topic page.
def get_topic_and_write(stream_name, stream, topic):
    json_path = json_root / Path(sanitize_stream(stream_name, stream['id'])) / Path (sanitize_topic(topic) + '.json')
    f = json_path.open('r', encoding='utf-8')
    messages = json.load(f)
    f.close()
    o = open_outfile(md_root / Path(sanitize_stream(stream_name, stream['id'])), Path(sanitize_topic(topic) + '.html'), 'w+')
    o.write(format_topic_header(stream_name, stream['id'], topic))
    o.write('\n{% raw %}\n')
    write_topic(messages, stream_name, stream['id'], topic, o)
    o.write('\n{% endraw %}\n')
    o.close()

# updates the "last updated" footer message to time `t`.
def write_last_updated(t):
    f = last_updated_path.open('w+')
    f.write('<p>Last updated: {} UTC</p>'.format(t))
    f.close()

# writes all markdown files to md_root, based on the archive at json_root.
def write_markdown():
    f = (json_root / Path('stream_index.json')).open('r', encoding='utf-8')
    stream_info = json.load(f, encoding='utf-8')
    f.close()
    streams = stream_info['streams']
    write_last_updated(str(stream_info['time'])) #(datetime.utcfromtimestamp(time.time()))
    write_stream_index(streams)
    for s in streams:
        print('building: ', s)
        write_topic_index(s, streams[s])
        for t in streams[s]['topic_data']:
            get_topic_and_write(s, streams[s], t)

# resets the current repository to match origin/master
def github_pull():
    print(subprocess.check_output(['git','fetch','origin','master']))
    print(subprocess.check_output(['git','reset','--hard','origin/master']))

# commits changes in archive/ and pushes the current repository to origin/master
def github_push():
    print(subprocess.check_output(['git','add','archive/*']))
    print(subprocess.check_output(['git','add','_includes/archive_update.html']))
    print(subprocess.check_output(['git','commit','-m','auto update: {}'.format(datetime.utcfromtimestamp(time.time()).strftime('%b %d %Y at %H:%M UTC'))]))
    print(subprocess.check_output(['git','push']))

parser = argparse.ArgumentParser(description='Build an html archive of the leanprover Zulip chat.')
parser.add_argument('-b', action='store_true', default=False, help='Build .md files')
parser.add_argument('-t', action='store_true', default=False, help='Make a clean json archive')
parser.add_argument('-i', action='store_true', default=False, help='Incrementally update the json archive')
parser.add_argument('-f', action='store_true', default=False, help='Pull from GitHub before updating. (Warning: could overwrite this script.)')
parser.add_argument('-p', action='store_true', default=False, help='Push results to GitHub.')

results = parser.parse_args()

if results.t and results.i:
    print('Cannot perform both a total and incremental update. Use -t or -i.')
    exit()
if results.t:
    populate_all()
elif results.i:
    populate_incremental()
if results.f:
    github_pull()
if results.b:
    write_markdown()
if results.p:
    github_push()