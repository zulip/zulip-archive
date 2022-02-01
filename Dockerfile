FROM python:3-alpine

RUN mkdir -p /zulip-archive && apk update && apk add git curl

COPY . /zulip-archive-action/

ENTRYPOINT ["sh", "/zulip-archive-action/entrypoint.sh"]
