# Welcome to settings.py!  You will want to modify these values
# for your own needs.

from pathlib import Path

'''
When we get content from your Zulip instance, we first create
JSON files that include all of the content data from the Zulip
instance.  Having the data in JSON makes it easy to incrementally
update your data as new messages come in.

You will want to put this in a permanent location outside of
your repo.  Here we assume a sibling directory named zulip_json, but
you may prefer another directory structure.
'''

json_directory = Path('../zulip_json')  # Modify me!

'''
We write HTML to here.
'''
html_directory = Path('./archive')  # Modify me!

'''
You may only want to include certain streams.  If you
use '*' in included_streams, that gets all your streams,
except that excluded_streams takes precedence.
'''

# Modify as needed:
included_streams = [
    '*', # for all streams
    # 'general',
    # 'public',
    ]

'''
add streams here that may be "public" on your Zulip
instance, but which you don't want to publish in the
archive
'''
excluded_streams = [
    # 'stream name1',
    # 'stream name2',
    ]
