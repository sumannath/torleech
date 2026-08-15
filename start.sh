#!/bin/sh
# Runtime bootstrap. The virtualenv is provisioned on first start rather than
# baked into the image, and Firefox is downloaded here too when the base image
# does not already provide it. Both targets are expected to be persistent
# volumes, so this work happens once, not on every container start.
set -eu

FIREFOX_PATH="${FIREFOX_PATH:-/opt/firefox/firefox}"
VENV_DIR="${VENV_DIR:-/app/venv}"
FIREFOX_URL="https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US"

# -----------------------------
# Firefox
# -----------------------------
if [ -x "$FIREFOX_PATH" ]; then
    # Provided by the base image (apk on Alpine) or already downloaded.
    echo "[INFO] Firefox already present, skipping download"
else
    firefox_dir=$(dirname "$FIREFOX_PATH")
    echo "[INFO] Downloading Firefox to $firefox_dir..."
    mkdir -p "$firefox_dir"

    # Staged inside firefox_dir so the download never lands on the size-capped
    # /tmp tmpfs that Firefox uses for its profiles.
    archive="$firefox_dir/.firefox-download.tar"
    wget -q -O "$archive" "$FIREFOX_URL"

    # -xf auto-detects the compression: Mozilla moved from .tar.bz2 to .tar.xz
    # at Firefox 135 and may move again.
    tar -xf "$archive" -C "$firefox_dir" --strip-components=1
    rm -f "$archive"

    if [ ! -x "$FIREFOX_PATH" ]; then
        echo "[ERROR] Firefox binary missing after extraction: $FIREFOX_PATH"
        exit 1
    fi
    echo "[INFO] Firefox ready: $("$FIREFOX_PATH" --version 2>/dev/null)"
fi

# -----------------------------
# Virtualenv
# -----------------------------
# The venv lives on a volume that outlives the image, so a rebuilt or swapped
# base image can leave a venv built by a different interpreter behind. Stamp it
# with the interpreter and requirements it was built from and rebuild on drift.
venv_stamp="$VENV_DIR/.provisioned"
venv_want="$(python3 -VV | md5sum | cut -c1-16) $(md5sum /app/requirements.txt | cut -c1-16)"

if [ -x "$VENV_DIR/bin/python" ] && [ "$(cat "$venv_stamp" 2>/dev/null)" = "$venv_want" ]; then
    echo "[INFO] Virtualenv already present, skipping creation"
else
    if [ -e "$VENV_DIR/bin/python" ]; then
        echo "[INFO] Virtualenv is stale (interpreter or requirements changed), rebuilding..."
        rm -rf "${VENV_DIR:?}/"* "${VENV_DIR:?}/".* 2>/dev/null || true
    else
        echo "[INFO] Creating virtualenv..."
    fi
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --no-cache-dir --quiet --disable-pip-version-check -r /app/requirements.txt
    printf '%s' "$venv_want" > "$venv_stamp"
    echo "[INFO] Virtualenv ready"
fi

# -----------------------------
# Run the Python application
# -----------------------------
# exec so that main.py becomes PID 1 and receives SIGTERM from `docker stop`
# directly; without it the shell would swallow the signal and Docker would
# SIGKILL the driver mid-run.
echo "[INFO] All dependencies ready. Starting application..."
exec "$VENV_DIR/bin/python" /app/main.py
