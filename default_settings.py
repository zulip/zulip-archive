# Welcome to default_settings.py!  You will want to modify these values
# for your own needs and then copy them to settings.py.  Copying them
# in the same directory is the mostly likely choice here:
#
#    cp default_settings settings.py
#    <edit> settings.py
#
# If you prefer to keep the settings elsewhere, just make sure they
# are in your Python path.

import os
from pathlib import Path

'''
You generally want to start in debug mode to test out the archive,
and then set PROD_ARCHIVE to turn on production settings here.  In
production you usually change two things--the site_url and your
html_directory.
'''

if os.getenv('PROD_ARCHIVE'):
    DEBUG = False
else:
    DEBUG = True

'''
Set the site url.  The default below is good for local
Jekyll testing, but you will definitely need to set your own
value for prod.
'''

if DEBUG:
    site_url = 'http://127.0.0.1:4000'
else:
    site_url = os.getenv('SITE_URL')
    if not site_url:
        raise Exception("You need to configure site_url for prod")

'''
Set the zulip icon url.  Folks can press the icon to see a
message in the actual Zulip instance.
'''

if DEBUG:
    zulip_icon_url = 'http://127.0.0.1:4000/assets/img/zulip2.png'
else:
    # Set this according to how you serve your prod assets.
    zulip_icon_url = os.getenv("ZULIP_ICON_URL", None)


'''
Set the HTML title of your Zulip archive here.
'''
title = 'Zulip Chat Archive'  # Modify me!

'''
Set the path prefix of your URLs for Jekyll.

For example, you might want your main page to have
the path of archive/index.html
'''
html_root = 'archive'  # Modify me!

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
if DEBUG:
    html_directory = Path('./archive')  # Modify me!
else:
    raise Exception('''
        You need to set html_directory for prod, and it
        should be a different location than DEBUG mode,
        since files will likely have different urls in
        anchor tags.
        ''')

'''
You may only want to include certain streams.  If you
use '*' in included_streams, that gets all your streams,
except that excluded_streams takes precedence.

Note that we only ever read in **public** streams.  You
can make the settings more restrictive than that, but not
the opposite direction.
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
