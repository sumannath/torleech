FROM alpine:3.22
LABEL authors="suman"

WORKDIR /app

COPY . /app/

# Firefox and geckodriver must come from apk: Mozilla's official tarball is
# glibc-linked and will not run under musl, so it cannot be fetched at runtime
# the way it can on a glibc base. ttf-freefont gives headless Firefox a font to
# render with.
RUN apk add --no-cache python3 py3-pip firefox geckodriver ttf-freefont \
    && mkdir -p /app/download \
    && chmod +x /app/start.sh

ENV SLEEP_HOURS=6
ENV FIREFOX_PATH=/usr/bin/firefox
ENV GECKODRIVER_PATH=/usr/bin/geckodriver

# Declared last so that a new revision does not invalidate the build cache above.
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.title="torleech" \
      org.opencontainers.image.source="https://github.com/sumannath/torleech" \
      org.opencontainers.image.revision="${GIT_SHA}"

ENTRYPOINT ["/app/start.sh"]
