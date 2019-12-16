# Zulip HTML archive

Generates an HTML archive of a configured set of streams within a
[Zulip](https://zulipchat.com) organization (usually all public
streams).  This is particularly useful when used in combination with Jekyll, to
compile the html/markdown to a functional website.

Example: [Lean Prover
archive](https://leanprover-community.github.io/archive/).

`zulip-archive` works by downloading Zulip message history via the
API, storing it in JSON files, maintaining its local archive with
incremental updates, and turning those JSON files into the HTML
archive.

## Instructions

* The script requires Python 3.
* Install the Zulip python bindings, with `pip3 install zulip`.
* [Create a bot](https://zulipchat.com/help/add-a-bot-or-integration)
  and download its
  [zuliprc](https://zulipchat.com/api/configuring-python-bindings)
  file to `zulip-archive/zuliprc` within this project.
* Extend the `zuliprc` file with an `archive` section like this:
    ```
    [archive]
    # root_url is used for internal links in the archive.
    # A file:/// path is useful for inspecting on the local filesystem.
    root_url=file:///path/to/zulip-archive
    # A whitelist of streams; if specified, only these streams will be included.
    stream_whitelist=announce
    # A blacklist of streams; these streams will never be included.
    stream_blacklist=hidden, other hidden
    # The title of the archive
    title=Lean Prover Zulip Chat Archive
    ```
* Optionally, modify the display generation code to fit your needs. The
  defaults are based on the [leanprover-community Jekyll
  setup](https://github.com/leanprover-community/leanprover-community.github.io).

* Run `python3 archive.py -t` to download a fresh archive.

The tool supports the following options:

  * `-t` builds a fresh archive. This will download every message from the Zulip chat and might take a long time. Must be run at least once before using `-i`.
  * `-i` updates the archive with messages posted since the last scrape.
  * `-b` generates the markdown/html output.
  * `-f` updates the git repository containing the script, and `-p`
  pushes the generated files. Useful if the script is generating a static site hosted using GitHub Pages.

## Contributing and future plans

Feedback, issues, and pull requests are encouraged!  Our goal is for
this project to support the needs of any community looking for an HTML
archive of their Zulip organization's history, through just
configuration changes.  So please report even minor inconveniences,
either via a GitHub issue or by posting in
[#integrations](https://chat.zulip.org/#narrow/stream/127-integrations/)
in the [Zulip development community](https://chat.zulip.org).

Once `zulip-archive` is more stable and polished, we expect to merge
it into the
[python-zulip-api](https://github.com/zulip/python-zulip-api) project
and moves its documentation to live [with other
integrations](https://zulipchat.com/integrations/) for a more
convenient installation experience.  But at the moment, it's
convenient for it to have a dedicated repository for greater
visibility.

There are also [plans](https://github.com/zulip/zulip/issues/13172) to
allow organizations to configure "web public" streams that people can
access without signing up for a Zulip account, while still using
in-app features like full-text search and real-time update.

Ideally the "web public" feature will satisfy most use cases, but we
will continue to provide `zulip-archive` for other scenarios:

- If you need to shut down a Zulip community, you can archive the
streams for posterity.
- You may want to publish the content "outside" of Zulip with
your own branding or integrate with other systems.
- You may want a local copy of the archive for offline reading.
- You may have some use case that we didn't foresee (but please tell us about it).

This project is licensed under the MIT license.

Author: [Robert Y. Lewis](https://robertylewis.com/) ([@robertylewis](https://github.com/robertylewis))
