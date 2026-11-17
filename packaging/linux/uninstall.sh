#!/bin/sh
# Remove brAInStream for the current user. Projects, recordings and the
# list of recent projects (~/.config/brainstream) are kept.
set -eu
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
rm -f "$HOME/.local/bin/brainstream" \
    "$DATA/applications/brainstream.desktop" \
    "$DATA/icons/hicolor/scalable/apps/brainstream.svg" \
    "$DATA/icons/hicolor/256x256/apps/brainstream.png"
rm -rf "$DATA/brainstream"
update-desktop-database "$DATA/applications" >/dev/null 2>&1 || true
echo "brAInStream is removed. Projects and recordings are kept."
