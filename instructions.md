Creating your Zulip archive takes a few steps to set up.

## Download dependencies

* Clone this repo.
* Download [python3](https://www.python.org/downloads/) if you
  don't already have it.  (We require version 3.6 or higher.)
* Install the Zulip python bindings, with `pip3 install zulip`.
* Download [Jekyll](https://jekyllrb.com/)

## Get a Zulip API key

You will need an API key to get data from Zulip.  Often you
will do this by  [creating a bot](https://zulipchat.com/help/add-a-bot-or-integration),
but you can also use your main user's API key.

* Download a [zuliprc](https://zulipchat.com/api/configuring-python-bindings)
  file to `zuliprc` within this project.

## Customize your settings

* Run this command:

    cp default_settings.py settings.py

* Then read `settings.py` and modify the settings to fit your needs.
  (There are comments in the file that explain each setting.)
* Optionally, modify the code to fit your needs. This repo
  is based on the [leanprover-community Jekyll
  setup](https://github.com/leanprover-community/leanprover-community.github.io).

## Build JSON files from your Zulip instance

* Create a directory to store JSON in (see settings.py for more details).
* Run `python3 archive.py -t` to download a fresh archive. (This may take
  a long time.  You may wish to experiment with just a few streams at
  first--see `settings.py` for details.)

Note: you will be able to update your archive later with
`python archive.py -i` to get more messages.

## Build the HTML/markdown files for Jekyll

Run this command to build your archive

    python archive.py -b

## Test your changes locally

You can use this command to serve your files using Jekyll:

    jekyll serve

Typically you will then view your files at http://127.0.0.1:4000/archive/.

## Add layouts and assets.

You may wish to copy the following assets into your Jekyll directory
structure:

- `layouts/archive.html` -> `_layouts`
- `assets/img/zulip2.png`

## Go to production

Once you are satisfied with your local testing, you will want to host
your archive publicly.  See [hosting.md](hosting.md) for more details.

# Other notes

## archive.py

The main tool to familiarize yourself with is `archive.py`.  It takes these
options:

  * `-t` builds a fresh archive. This will download every message from the Zulip chat and might take a long time. Must be run at least once before using `-i`.
  * `-i` updates the archive with messages posted since the last scrape.
  * `-b` generates the markdown/html output.

## github.py

This repostiory also contains a [hacky tool](github.py) for managing
pushes to a repository hosted by GitHub Pages, which supports the
following options.  Be sure to read the warnings in `github.py`.

* `-f` updates the git repository containing the script
* `-p` pushes the generated files

Contributions are appreciated to make `github.py` no longer hacky.

