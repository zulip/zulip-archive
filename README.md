# Zulip HTML archive

Generates an HTML archive of a configured set of streams within a
[Zulip](https://zulipchat.com) organization (usually all public
streams).  The [hosting docs](hosting.md) offer a few suggestions for
good ways to host the output of this tool.

Example: [Lean Prover
archive](https://leanprover-community.github.io/archive/).

`zulip-archive` works by downloading Zulip message history via the
API, storing it in JSON files, maintaining its local archive with
incremental updates, and turning those JSON files into the HTML
archive.

## Why archive?

The best place to participate actively in a Zulip community is an app
that tracks unread messages, formats messages properly, and is
designed for efficient interaction.  However, there are several use
cases where this HTML archive tool is a valuable complement to the
Zulip apps:

* A public HTML archive can be indexed by search engines and doesn't
  require authentication to access.  For open source projects and
  other open communities, this provides a convenient search and
  browsing experience for users who may not want to sign up an account
  just to find previous answers to common questions.

* It's common to set up Zulip instances for one-time events such as
  conferences, retreats, or hackathons.  Once the event ends, you may
  want to shut down the Zulip instance for operational convenience,
  but still want an archive of the communications.

* You may also decide to shut down a Zulip instance, whether to move
  to another communication tool, to deduplicate instances, or because
  your organization is shutting down.  You can always [export your
  Zulip data](https://zulipchat.com/help/export-your-organization),
  but the other tool may not be able to import it.  In such a case,
  you can use this archive tool to keep the old conversations
  accessible. (Contrast this to scenarios where your provider locks
  you in to a solution, even when folks are dissatisfied with the
  tool, because they own the data.)

* You may also want to publish your conversations outside of Zulip for
  branding reasons or to integrate with other data.  You can modify
  the tools here as needed for that.  You own your own data.

## Instructions

See the [instructions](instructions.md) to learn how to build
your Zulip archive.

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

Ideally the "web public" feature will be a better solution for the
most common use case of this tool.  But we expect `zulip-archive` to
be maintained for the foreseeable future, as it supports a broader set
of use cases.

This project is licensed under the MIT license.

Author: [Robert Y. Lewis](https://robertylewis.com/) ([@robertylewis](https://github.com/robertylewis))
