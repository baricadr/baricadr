FROM alpine:3.13

MAINTAINER "Anthony Bretaudeau <anthony.bretaudeau@inra.fr>"

COPY requirements.txt /tmp/requirements.txt

RUN apk add --no-cache \
    python3 \
    bash \
    nano \
    nginx \
    uwsgi \
    uwsgi-python3 \
    supervisor \
    ca-certificates \
    postgresql-libs \
    at \
    postgresql-client \
    tzdata \
    wget curl unzip && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev postgresql-dev && \
    pip3 install -r /tmp/requirements.txt && \
    apk --purge del .build-deps && \
    rm /etc/nginx/conf.d/default.conf && \
    rm -r /root/.cache

# Rclone install, needed for tests
ENV PLATFORM_ARCH="amd64"
ARG RCLONE_VERSION="1.54.0"
RUN  cd /tmp && \
wget -q https://downloads.rclone.org/v${RCLONE_VERSION}/rclone-v${RCLONE_VERSION}-linux-${PLATFORM_ARCH}.zip && \
unzip /tmp/rclone-v${RCLONE_VERSION}-linux-${PLATFORM_ARCH}.zip && \
mv /tmp/rclone-*-linux-${PLATFORM_ARCH}/rclone /usr/bin

COPY docker/nginx.conf /etc/nginx/
COPY docker/nginx_baricadr.conf /etc/nginx/conf.d/
COPY docker/uwsgi.ini /etc/uwsgi/
COPY docker/supervisord.conf /etc/supervisord.conf

COPY . /baricadr
WORKDIR /baricadr

COPY start_baricadr.sh /start_baricadr.sh

ENTRYPOINT "/start_baricadr.sh"
