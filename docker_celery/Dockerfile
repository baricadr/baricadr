FROM alpine:3.8

MAINTAINER "Anthony Bretaudeau <anthony.bretaudeau@inra.fr>"

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0

COPY . /baricadr
WORKDIR /baricadr

RUN apk add --no-cache \
    python3 \
    bash \
    nano \
    py-psutil && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    pip3 install -r /baricadr/requirements_celery.txt && \
    rm -r /root/.cache

# Rclone install
ENV PLATFORM_ARCH="amd64"
ARG RCLONE_VERSION="1.43"
RUN  cd /tmp && \
    wget -q https://downloads.rclone.org/v${RCLONE_VERSION}/rclone-v${RCLONE_VERSION}-linux-${PLATFORM_ARCH}.zip && \
    unzip /tmp/rclone-v${RCLONE_VERSION}-linux-${PLATFORM_ARCH}.zip && \
    mv /tmp/rclone-*-linux-${PLATFORM_ARCH}/rclone /usr/bin

USER nobody

ENTRYPOINT celery -A baricadr.tasks.celery worker --loglevel=info
