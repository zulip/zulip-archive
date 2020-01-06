# Zulip HTML archive

Generates an HTML archive of a configured set of streams within a
[Zulip](https://zulipchat.com) organization (usually all public
streams).

Example: [Lean Prover
archive](https://leanprover-community.github.io/archive/).

`zulip-archive` works by downloading Zulip message history via the
API, storing it in JSON files, maintaining its local archive with
incremental updates, and turning those JSON files into the HTML
archive.

### Contents
* [Running zulip-archive as a GitHub action](#running-zulip-archive-as-a-github-action)
* [Running zulip-archive by yourselves](#running-zulip-archive-by-yourselves)
* [Why archive](#why-archive)
* [Contributing and future plans](#contributing-and-future-plans)

## Running zulip-archive as a GitHub action

Running `zulip-archive` as a GitHub action is easiest way to get up and running. The action would run periodically, sync the repo with latest messages and publish archive website using GitHub pages. Follow the steps below to setup `zulip-archive` Github action in a few minutes.

### Step 1 - Create a new repository for running action

We recommend using a new repository for running action. If you have not yet created one, goto https://github.com/new/ and create a new repository. 

### Step 2 - Generate credentials

GitHub action needs the following credentials for running.

#### Zulip API Key

Zulip API key is used for fetching the messages of public streams from the Zulip organization. We recommend creating a bot and using it's API key instead of using your own API key. See https://zulipchat.com/help/add-a-bot-or-integration for more details.

#### GitHub Personal Access Token

The token is used by the GitHub action for pushing to the repo and running GitHub page builds. You can generate the token by going to https://github.com/settings/tokens. Make sure to enable `repo` and `workflow` while generating the token.

### Step 3 - Store credentials as secrets in the repository

Now that we have generated the credentials, we need to store them in the repository as secrets so that action can access them during run time. For that goto `https://github.com/<username>/<repo-name>/settings/secrets`. `<username>` is your GitHub username and `<repo-name>` is the name of the repo you just created.

Now create the following 4 secrets. Use the credentials generated in the above step as the value of each secret.

|Secret name                  | Value                        |
|-----------------------------|----------------------------------------------|
|zulip_organization_url       | URL of your Zulip organization.              |
|zulip_bot_email              | The email of the Zulip bot you created       |
|zulip_bot_key                | API key of the Zulip bot you created         |
|github_personal_access_token | The GitHub personal access token you created |


### Step 4 - Configure the streams you want to index
`zulip-archive` by default don't know which all public streams to be indexed. You can tell `zulip-archive` which all streams to be indexed by creating a file called `streams.yaml` in the newly created repository.

If you want to index all the public streams, set the following as the content of `streams.yaml` file.

```yaml
included:
  - '*'
```

You can exclude some of the public streams by placing them under `excluded` key.

```yaml
included:
  - '*'

excluded:
  - general
  - development help
```

Alternatively you can specify only the streams that you want to index.

```yaml
included:
  - python
  - data structures
  - javascript
```

### Step 5 - Enable zulip-archive action

Final step is to enable the action. For that create a file called `.github/workflows/main.yaml` in your repository and pase the following as content.

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
      uses: actions/checkout@v1
    - name: Run archive
      id: archive
      uses: zulip/zulip-archive@master
      with:
        zulip_organization_url: ${{ secrets.zulip_organization_url }}
        zulip_bot_email: ${{ secrets.zulip_bot_email }}
        zulip_bot_key: ${{ secrets.zulip_bot_key }}
        github_personal_access_token: ${{ secrets.github_personal_access_token }}
```

The above file tells GitHub to run the `zulip-archive` action every 20 minutes. You can adjust the `cron` key to modify the schedule as you feel appropriate. If you Zulip organization history is very large (not the case for most users) we recommend to increase the cron period from running every 30 minutes to maybe run every 1 hour (eg `'0 * * * *'`). This is is because the initial archive run that fetches the messages for the first time takes a lot of time and we don't want the second cron job to start before finishing the first run is over. After the initial run is over you can shorten the cron job period if necessary.

### Step 6 - Verify everything works

Final step is to verify that everything is working as it is supposed to be. You would have to wait for some time since the action is scheduled to run every 20 minutes (or the time you have configured it to be in above step.) You can track the status of the action by visiting `https://github.com/<github-username>/<repo-name>/actions`. Once the action completes running, you would be able to visit the archive by opening the link mentioned in the action run log at the end. The link would be usually be of the form `<github-username>.github.io/<repo-name>` or `<your-personal-domain>/<repo-name>` if you have configured your own personal domain to point to GitHub pages.


## Running zulip-archive by yourselves

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
  Zulip data](https://zulipchat.com/help/export-your-organization),
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
