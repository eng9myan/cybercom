#!/usr/bin/env bash
# Populate ./cycom-source/ with the Cycom 19 community source.
#
# Two modes — first that succeeds wins:
#   1. If D:/cycom-19.0/cycom-19.0/ exists locally (the Windows-extracted zip), copy it in.
#   2. Otherwise, git clone from github.com/cycom/cycom branch 19.0.
#
# Safe to re-run: skips if cycom-source/ already has content.

set -euo pipefail
cd "$(dirname "$0")/.."

if [ -d cycom-source ] && [ -n "$(ls -A cycom-source 2>/dev/null)" ]; then
  echo "cycom-source/ is already populated. Delete it manually if you need a fresh copy."
  exit 0
fi

LOCAL_SRC="/d/cycom-19.0/cycom-19.0"
if [ -d "$LOCAL_SRC" ] && [ -d "$LOCAL_SRC/addons" ]; then
  echo "Found local Cycom source at $LOCAL_SRC — copying in (no git clone needed)…"
  mkdir -p cycom-source
  cp -r "$LOCAL_SRC/." cycom-source/
  echo "Done. cycom-source/ now mirrors $LOCAL_SRC."
else
  echo "No local source at $LOCAL_SRC — cloning Cycom 19 community from GitHub (several hundred MB)…"
  git clone --depth=1 --branch 19.0 --single-branch https://github.com/cycom/cycom.git cycom-source
fi

echo "cycom-source/ is mounted into the container at /mnt/cycom-source."
echo "Restart the stack to pick up new addons: docker compose restart cycom"
