The code in this repo helps you extract content from a Zulip
instance and build the basic HTML structure, but it leaves it
to you to actually host the data on some server.

In other words, Zulip is not opinionated about you serve
the HTML (and in some ways the entire mission of this project
is to empower you to put your data where you want).

Here are some convenient options for serving the HTML:

### Jekyll

[Jekyll](https://jekyllrb.com/) is a popular tool for
serving static content.

The archive script generates index pages in markdown that are
designed for a Jekyll build, so you can do something like this
from within this directory (where you checked out code):

```
gem install jekyll bundler
jekyll serve
```

With the default configuration you should be able to see
your archive at http://127.0.0.1:4000/archive/

If you have a large archive that you update regularly,
you may want to run `jekyll serve --incremental`.

### GitHub

You can use GitHub Pages to serve your HTML.  We recommend
configuring your `md_root` to point into your local copy of
your `username.github.io` repo (e.g. `alice.github.io`) and
then push from there.

Some customers will want to just use the same repo for both
this tooling and the content from their Zulip instance.  We
don't recommend this approach long term, since it can complicate
staying up to date with patches from this repo.  If you are
still interested in this approach, despite the warnings, you
may find the `github.py` script to be useful.
