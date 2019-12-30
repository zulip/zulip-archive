FROM hackerkid/zulip-archive

RUN mkdir -p /zulip-archive

COPY . /zulip-archive-action/

ENTRYPOINT ["/zulip-archive-action/entrypoint.sh"]
