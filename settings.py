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
