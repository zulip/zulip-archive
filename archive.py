#!/usr/bin/env python3

'''
This is the main program for the Zulip archive system.  For help:

    python archive.py -h

Note that this actual file mostly does the following:

    parse command line arguments
    check some settings from settings.py
    complain if you haven't made certain directories

The actual work is done in two main libraries:

    lib/html.py
    lib/populate.py
'''


# The workflow (timing for the leanprover Zulip chat, on my slow laptop):
# - populate_all() builds a json file in `settings.json_directory` for each topic,
#   containing message data and an index json file mapping streams to their topics.
#   This uses the Zulip API and takes ~10 minutes to crawl the whole chat.
# - populate_incremental() assumes there is already a json cache and collects only new messages.
# - write_markdown() builds markdown files in `settings.html_directory`
# - See hosting.md for suggestions on hosting.
#

import argparse
import configparser
import zulip

from lib.common import (
    stream_validator,
    exit_immediately
    )

# Most of the heavy lifting is done by the following modules:

from lib.populate import (
    populate_all,
    populate_incremental
    )

from lib.html import (
    write_markdown
    )

try:
    import settings
except ModuleNotFoundError:
    # TODO: Add better instructions.
    exit_immediately('''
    We can't find settings.py.

    Please copy default_settings.py to settings.py
    and then edit the settings.py file to fit your use case.

    For testing, you can often leave the default settings,
    but you will still want to review them first.
    ''')

NO_JSON_DIR_ERROR_WRITE = '''
We cannot find a place to write JSON files.

Please run the below command:

mkdir {}'''

NO_JSON_DIR_ERROR_READ = '''
We cannot find a place to read JSON files.

Please run the below command:

mkdir {}

And then fetch the JSON:

python archive.py -t'''

NO_HTML_DIR_ERROR = '''
We cannot find a place to write HTML files.

Please run the below command:

mkdir {}'''

def get_json_directory(for_writing):
    json_dir = settings.json_directory

    if not json_dir.exists():
        # I use posix paths here, since even on Windows folks will
        # probably be using some kinda Unix-y shell to run mkdir.
        if for_writing:
            error_msg = NO_JSON_DIR_ERROR_WRITE.format(json_dir.as_posix())
        else:
            error_msg = NO_JSON_DIR_ERROR_READ.format(json_dir.as_posix())

        exit_immediately(error_msg)

    if not json_dir.is_dir():
        exit_immediately(str(json_dir) + ' needs to be a directory')

    return settings.json_directory

def get_html_directory():
    html_dir = settings.html_directory

    if not html_dir.exists():
        error_msg = NO_HTML_DIR_ERROR.format(html_dir.as_posix())

        exit_immediately(error_msg)

    if not html_dir.is_dir():
        exit_immediately(str(html_dir) + ' needs to be a directory')

    return settings.html_directory

def get_client_info():
    config_file = './zuliprc'
    client = zulip.Client(config_file=config_file)

    # It would be convenient if the Zulip client object
    # had a `site` field, but instead I just re-read the file
    # directly to get it.
    config = configparser.RawConfigParser()
    config.read(config_file)
    zulip_url = config.get('api', 'site')

    return client, zulip_url

def run():
    parser = argparse.ArgumentParser(description='Build an html archive of the Zulip chat.')
    parser.add_argument('-b', action='store_true', default=False, help='Build .md files')
    parser.add_argument('-t', action='store_true', default=False, help='Make a clean json archive')
    parser.add_argument('-i', action='store_true', default=False, help='Incrementally update the json archive')

    results = parser.parse_args()

    if results.t and results.i:
        print('Cannot perform both a total and incremental update. Use -t or -i.')
        exit(1)

    if not (results.t or results.i or results.b):
        print('\nERROR!\n\nYou have not specified any work to do.\n')
        parser.print_help()
        exit(1)

    json_root = get_json_directory(for_writing=results.t)

    if results.b:
        md_root = get_html_directory()

    if results.t or results.i:
        is_valid_stream_name = stream_validator(settings)

    client, zulip_url = get_client_info()

    if results.t:
        populate_all(
            client,
            json_root,
            is_valid_stream_name,
            )

    elif results.i:
        populate_incremental(
            client,
            json_root,
            is_valid_stream_name,
            )

    if results.b:
        write_markdown(
            json_root,
            md_root,
            settings.site_url,
            settings.html_root,
            settings.title,
            zulip_url
            )

if __name__ == '__main__':
    run()
