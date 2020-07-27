FROM alpine:3.9
LABEL MAINTAINER="wangbilin"

RUN apk --no-cache add git less openssh bash curl && \
# ADD mc /usr/bin/mc
curl --proto '=https' --tlsv1.2 https://dl.min.io/client/mc/release/linux-amd64/mc -sSf -o /usr/bin/mc && \
chmod +x /usr/bin/mc
