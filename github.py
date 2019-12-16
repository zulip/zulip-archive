#!/usr/bin/env python3

"""
WARNING!

This script includes example code from the Lean Prover community, who
used this repo to store the Zulip content as well as the code.  We
recommend to most folks to create a **separate** repo for your
content, even if you are using Github to serve the content, and expect
to convert this tool to a supported option based on that model.
"""

from datetime import datetime
import time, argparse, subprocess

parser = argparse.ArgumentParser(description='Push/pull repo.')

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

parser.add_argument('-f', action='store_true', default=False, help='Pull from GitHub before updating. (Warning: could overwrite this script.)')
parser.add_argument('-p', action='store_true', default=False, help='Push results to GitHub.')

if results.f:
    github_pull()
if results.p:
    github_push()
