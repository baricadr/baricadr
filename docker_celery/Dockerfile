FROM alpine:3.13.4

MAINTAINER "Anthony Bretaudeau <anthony.bretaudeau@inrae.fr>"

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0

COPY . /baricadr
WORKDIR /baricadr

RUN apk add --no-cache \
    python3 \
    bash \
    nano \
    py-psutil \
    postgresql-libs && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    apk add --no-cache --virtual .build-deps gcc g++ musl-dev python3-dev postgresql-dev && \
    pip3 install -r /baricadr/requirements_celery.txt && \
    apk --purge del .build-deps && \
    rm -r /root/.cache

# Rclone install
ENV PLATFORM_ARCH="amd64"
ENV C_FORCE_ROOT='true'
ARG RCLONE_VERSION="1.54.0"
RUN  cd /tmp && \
    wget -q https://downloads.rclone.org/v${RCLONE_VERSION}/rclone-v${RCLONE_VERSION}-linux-${PLATFORM_ARCH}.zip && \
    unzip /tmp/rclone-v${RCLONE_VERSION}-linux-${PLATFORM_ARCH}.zip && \
    mv /tmp/rclone-*-linux-${PLATFORM_ARCH}/rclone /usr/bin

ENTRYPOINT celery -A baricadr.tasks.celery worker --loglevel=info
