FROM alpine:3.8

MAINTAINER "Anthony Bretaudeau <anthony.bretaudeau@inra.fr>"

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0

COPY . /queue
WORKDIR /queue

RUN apk add --no-cache \
    python3 \
    bash \
    nano && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    pip3 install -r /queue/requirements_celery.txt && \
    rm -r /root/.cache

USER nobody

ENTRYPOINT celery -A celery_worker.celery worker --loglevel=info
