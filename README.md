# Zulip HTML archive

[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Generates an HTML archive of a configured set of streams within a
[Zulip](https://zulip.com) organization. It is common to archive all [public](https://zulip.com/help/stream-permissions) or [web-public](https://zulip.com/help/public-access-option) streams.

Example: [Lean Prover
archive](https://leanprover-community.github.io/archive/).

`zulip-archive` works by downloading Zulip message history via the
API, storing it in JSON files, maintaining its local archive with
incremental updates, and turning those JSON files into the HTML
archive.

This archive tool is often used in addition to enabling the [public access option](https://zulip.com/help/public-access-option) for your organization, which lets administrators configure selected streams to be web-public. Web-public streams can be viewed by anyone on the Internet without creating an account in your organization. The public access option does not yet support search engine indexing, which makes this archive tool a good option if it's important for your organization's chat history to appear in search results. It is easy to configure `zulip-archive` to automatically archive all web-public streams in your organization.

### Contents
* [Running zulip-archive as a GitHub action](#running-zulip-archive-as-a-github-action)
* [Running zulip-archive without GitHub actions](#running-zulip-archive-without-github-actions)
* [Why archive](#why-archive)
* [Contributing and future plans](#contributing-and-future-plans)

## Running zulip-archive as a GitHub action

Running `zulip-archive` as a GitHub action is easiest way to get up and running. The action will periodically sync a GitHub repository with the latest messages, and publish the archive website using GitHub pages. Follow the steps below to set up a `zulip-archive` GitHub action in a few minutes.

### Step 1 - Create a repository for running the action

It's best to use a dedicated repository for running the action. You can create a new repository at https://github.com/new/.

### Step 2 - Generate credentials

The GitHub action requires a Zulip API key in order to run. The key is used for fetching messages in public streams in your Zulip organization. It is strongly recommended that you [create a bot](https://zulip.com/help/add-a-bot-or-integration) and use its zuliprc, rather than using your personal zuliprc.

### Step 3 - Store credentials as secrets in the repository

The credentials for your bot need to be stored in the repository as secrets, so that the action can access them during run time. You can create secrets in your repository at `https://github.com/<username>/<repo-name>/settings/secrets`, where `<username>` is your GitHub username, and `<repo-name>` is the name of the repository you are using.

You will need to create the following secret. Use the credentials generated in the above step as the value of each secret.

|Secret name   | Value                                                |
|--------------|------------------------------------------------------|
|zuliprc       | The file content of the zuliprc obtained from step 2 |

### Step 4 - Enable GitHub Pages or set up base URL

Go to `https://github.com/<username>/<repo-name>/settings/pages`, select `main` (or a branch of your choosing), and `/` as the folder. Save the changes. The base URL of the generated site will be resolved to GitHub Pages, i.e., `https://<username>.github.io/<repo-name>` or the configured custom domain name.

Alternatively, you can configure the `base_url` option to populate the base URL. This option could be useful in situation when you are not using GitHub Pages.

### Step 5 - Configure the streams you want to index

You will need to configure which streams will be indexed by `zulip-archive` by creating a `streams.yaml` file in the repository you are using for the GitHub action. As a starting point, you can make a copy of the default configuration file: `cp default_streams.yaml streams.yaml`

To index all the [web-public streams](https://zulip.com/help/public-access-option) in your organization, set the following as the content of your `streams.yaml` file.

```yaml
included:
  - 'web-public:*'
```

To index all the [public streams](https://zulip.com/help/stream-permissions), set the following as the content of your `streams.yaml` file. Note that public streams include all web-public streams.

```yaml
included:
  - '*'
```

You can exclude specific public streams by placing them under the `excluded` key.

```yaml
included:
  - '*'

excluded:
  - general
  - development help
```

Alternatively, you can specify only the streams that you want to index.

```yaml
included:
  - python
  - data structures
  - javascript
```

### Step 6 - Enable the zulip-archive action

Enable the action by creating a file called `.github/workflows/main.yaml`:

#### Sample `main.yaml` file

```yaml
on:
  schedule:
   - cron: '*/20 * * * *'

jobs:
  publish_archive_job:
    runs-on: ubuntu-latest
    name: A job to publish zulip-archive in GitHub pages
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    - name: Run archive
      id: archive
      uses: zulip/zulip-archive@master
      with:
        zulip_organization_url: ${{ secrets.zulip_organization_url }}
        zulip_bot_email: ${{ secrets.zulip_bot_email }}
        zulip_bot_key: ${{ secrets.zulip_bot_key }}
        # Using the GitHub Token that is provided automatically by GitHub Actions
        # (no setup needed).
        github_token: ${{ secrets.GITHUB_TOKEN }}
        delete_history: true
        archive_branch: main
```

#### Configure run frequency

The above file tells GitHub to run the `zulip-archive` action every 20 minutes. You can [adjust](https://en.wikipedia.org/wiki/Cron) the `cron` key to modify the schedule as you feel appropriate.

If you Zulip organization history is very large (not the case for most users), it is recommended that you initially increase the time between runs to an hour or longer (e.g., `'0 * * * *'`). This is is because the initial archive run that fetches the messages for the first time will take a long time, and you don't want the second cron job to start before the first run is completed. After the initial run, you can shorten the cron job period as desired.

#### Configure `delete_history` option

If you are running frequent updates with a busy Zulip organization,
the Git repository that you use to run the action will grow very
quickly. In this situation, it is recommended that you set the `delete_history` option to
`true`. This will overwrite the Git _history_ in the repository, but
keep all the _content_. If you are using the repository for more than
just the Zulip archive (not recommended), you may want to set the `delete_history` flag to `false`, but be
warned that the repository size may explode.

### Step 7 - Verify that everything works

Finally, verify that everything is working as expected. You can track the status of the action by visiting `https://github.com/<github-username>/<repo-name>/actions`. Once the initial run is completed, you should be able to visit the archive by opening the link provided at the end of the action run log. The link will generally be of the form `<github-username>.github.io/<repo-name>`, or `<your-personal-domain>/<repo-name>` if you have configured your own personal domain to point to GitHub pages.

If you configure `base_url` option, you can track the status of the action by visiting the URL instead.

## Running zulip-archive without GitHub actions

For most users, running `zulip-archive` as GitHub actions should be good enough. If you want to run `zulip-archive` in your own server or do something else, see the [instructions](instructions.md) docs. The [hosting docs](hosting.md) also offer a few suggestions for good ways to host the output of this tool.

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
  Zulip data](https://zulip.com/help/export-your-organization),
  but the other tool may not be able to import it.  In such a case,
  you can use this archive tool to keep the old conversations
  accessible. (Contrast this to scenarios where your provider locks
  you in to a solution, even when folks are dissatisfied with the
  tool, because they own the data.)

* You may also want to publish your conversations outside of Zulip for
  branding reasons or to integrate with other data.  You can modify
  the tools here as needed for that.  You own your own data.


## Contributing and future plans

Feedback, issues, and pull requests are encouraged!  Our goal is for
this project to support the needs of any community looking for an HTML
archive of their Zulip organization's history, through just
configuration changes.  So please report even minor inconveniences,
either via a GitHub issue or by posting in the
[#integrations](https://chat.zulip.org/#narrow/stream/127-integrations/) stream
in the [Zulip development community](https://zulip.com/development-community/).

This project is licensed under the MIT license.

Author: [Robert Y. Lewis](https://robertylewis.com/) ([@robertylewis](https://github.com/robertylewis))
