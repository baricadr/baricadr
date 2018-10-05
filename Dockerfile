FROM alpine:3.8

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
    wget curl unzip man man-pages mdocml-apropos && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    pip3 install -r /tmp/requirements.txt && \
    rm /etc/nginx/conf.d/default.conf && \
    rm -r /root/.cache

# Rclone install
ENV PLATFORM_ARCH="amd64"
ARG RCLONE_VERSION="1.43"
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

CMD ["/usr/bin/supervisord"]
