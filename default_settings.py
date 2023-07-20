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
import yaml
from pathlib import Path

"""
You generally want to start in debug mode to test out the archive,
and then set PROD_ARCHIVE to turn on production settings here.  In
production you usually change two things--the site_url and your
html_directory.
"""

if os.getenv("PROD_ARCHIVE"):
    DEBUG = False
else:
    DEBUG = True

"""
Set the site url.  The default below is good for local testing, but you will
definitely need to set your own value for prod.
"""

if DEBUG:
    site_url = "http://127.0.0.1:4000"
else:
    site_url = os.getenv("SITE_URL")
    if site_url is None:
        raise Exception("You need to configure site_url for prod")

"""
Set the zulip icon url.  Folks can press the icon to see a
message in the actual Zulip instance.
"""

if DEBUG:
    zulip_icon_url = "http://127.0.0.1:4000/assets/img/zulip.svg"
else:
    # Set this according to how you serve your prod assets.
    zulip_icon_url = os.getenv("ZULIP_ICON_URL", None)


"""
Set the HTML title of your Zulip archive here.
"""
title = "Zulip Chat Archive"  # Modify me!

"""
Set the path prefix of your URLs for your website.

For example, you might want your main page to have
the path of archive/index.html
"""
html_root = os.getenv("HTML_ROOT", "archive")  # Modify me!

"""
When we get content from your Zulip instance, we first create
JSON files that include all of the content data from the Zulip
instance.  Having the data in JSON makes it easy to incrementally
update your data as new messages come in.

You will want to put this in a permanent location outside of
your repo.  Here we assume a sibling directory named zulip_json, but
you may prefer another directory structure.
"""

json_directory = Path(os.getenv("JSON_DIRECTORY", "../zulip_json"))

"""
We write HTML to here.
"""
if DEBUG:
    html_directory = Path("./archive")  # Modify me!
else:
    try:
        html_directory = Path(os.getenv("HTML_DIRECTORY", None))
    except TypeError:
        raise Exception(
            """
            You need to set html_directory for prod, and it
            should be a different location than DEBUG mode,
            since files will likely have different urls in
            anchor tags.
            """
        )


"""
This is where you modify the <head> section of every page.
"""
page_head_html = (
    '<html>\n<head><meta charset="utf-8"><title>Zulip Chat Archive</title></head>\n'
)

"""
This is where you modify the <footer> section of every page.
"""
page_footer_html = "\n</html>"


"""
You may only want to include certain streams.  In `streams.yaml`
file, mention the streams you want to include under `included` section.

Example
---

included:
  - general
  - javascript
  - data structures


A few wildcard operators are supported.

Example
---

included:
  - 'web-public:*'

Using 'web-public:*' includes all the **web-public streams** in the
Zulip organization. Using 'public:*' includes all the **public
streams** in Zulip archive (`*` will do the same thing, for
backwards-compatibility).  You can make the settings more restrictive
than that, but not the opposite direction.

If you want to exclude some public streams, mention them in the
`excluded` category in `streams.yaml`.

Example:
---

excluded:
  - checkins
  - development help

"""

try:
    with open("streams.yaml") as f:
        streams = yaml.load(f, Loader=yaml.BaseLoader)
        if "included" not in streams or not streams["included"]:
            raise Exception(
                "Please specify the streams to be included under `included` section in streams.yaml file"
            )
        included_streams = streams["included"]

        excluded_streams = []
        if "excluded" in streams and streams["excluded"]:
            excluded_streams = streams["excluded"]

except FileNotFoundError:
    raise Exception("Missing streams.yaml file")
