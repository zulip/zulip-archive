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

## Why archive?

The best place to view Zulip content is within Zulip itself,
but some of your customers or collaborators may only wish to
see the content, without using the tool.  (They may only
need to read the conversation, not participate in it.
They may simply be overwhelmed with all the other communication
tools they already use and resistant to trying out another
tool.)

Publishing an archive outside of your active Zulip
instance reduces the friction for those people.

It's also common to set up Zulip instances
for one-time events such as conferences, retreats, or
hackathons.  Once the event ends, you may decide to shut
down the Zulip instance, but participants may want to be
able to go back and read the conversations later for reference.

You may also decide to shut down Zulip instances to move to
another communication tool.  You can always export your Zulip
data, but the other tool may not be able to import it.  In such
a case, you can use the archive tool to keep the old conversations
accessible. (Contrast this to scenarios where your provider
locks you in to a solution, even when folks are dissatisfied
with the tool, because they own the data.)

You may also want to publish your conversations outside of Zulip for
branding reasons or to integrate with other data.  You can modify
the tools here as needed for that.  You own your own data.

Finally, you may want search engines to find your Zulip content.

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
will continue to provide `zulip-archive` for scenarios that don't
quite fit under the new feature.

This project is licensed under the MIT license.

Author: [Robert Y. Lewis](https://robertylewis.com/) ([@robertylewis](https://github.com/robertylewis))
