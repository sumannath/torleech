FROM ubuntu:latest
LABEL authors="suman"

WORKDIR /app

COPY . /app/

RUN apt update
RUN apt install -y python3 python3-pip python3.12-venv wget tar bzip2 libxtst6 libgtk-3-0 libx11-xcb-dev  \
    libdbus-glib-1-2 libxt6 libpci-dev ffmpeg libsm6 libxext6 libasound2-plugins
RUN mkdir /app/download
RUN wget -O /app/download/firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US"
RUN tar -xvjf /app/download/firefox.tar.bz2 -C /app/download/
RUN python3 -m venv venv
RUN venv/bin/pip install -r requirements.txt

ENV SLEEP_HOURS=6
ENV FIREFOX_PATH=/app/download/firefox/firefox

CMD ["venv/bin/python", "main.py"]