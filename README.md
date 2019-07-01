# zulip_archive
A tool for archiving and displaying Zulip chat channels.

The script `archive.py` has two functions:
* It builds a json archive of messages from a Zulip chat room.
* It generates static markdown/html to display these messages.

This is particularly useful when used in combination with Jekyll, to compile the html/markdown to a functional website. An example of this can be seen at the [leanprover-community Zulip chat archive](https://leanprover-community.github.io/archive/).

## Directions for use

* The script requires Python 3.
* Edit the configuration options, making sure that `client` points to a valid Zulip bot configuration.
* Optionally, modify the display generation to fit your needs. The defaults are based on the [leanprover-community Jekyll setup](https://github.com/leanprover-community/leanprover-community.github.io).
* Run `python3 archive.py` with the following options:
  * `-t` builds a fresh archive. This will download every message from the Zulip chat and might take a long time. Must be run at least once before using `-i`.
  * `-i` updates the archives with messages posted since the last scrape.
  * `-b` generates the markdown/html output.
  * `-f` updates the git repository containing the script, and `-p` pushes the generated files. Useful if the script is generating a static site hosted using GitHub Pages.