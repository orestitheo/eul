#!/usr/bin/env bash
# Add a new sample folder to the server.
#
# Usage:
#   ./scripts/add-samples.sh samples/percussive/mynewkit
#
# What it does:
#   1. Renames files in the folder (strips timestamps, lowercases)
#   2. Rsyncs the folder to the server
#   3. Adds a loadSoundFiles line to the SuperDirt boot config
#   4. Restarts SuperCollider so the new bank is available

set -euo pipefail

SERVER="root@204.168.163.80"
LOCAL_SAMPLES="$(cd "$(dirname "$0")/../samples" && pwd)"
REMOTE_SAMPLES="/opt/eul/samples"
BOOT_FILE="/root/.config/SuperCollider/startup.scd"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path-to-sample-folder>"
  echo "Example: $0 samples/percussive/mynewkit"
  exit 1
fi

FOLDER="$1"
# Strip leading samples/ if provided
FOLDER="${FOLDER#samples/}"
LOCAL_PATH="$LOCAL_SAMPLES/$FOLDER"

if [[ ! -d "$LOCAL_PATH" ]]; then
  echo "Error: folder not found: $LOCAL_PATH"
  exit 1
fi

BANK_NAME="$(basename "$FOLDER")"

echo "==> Renaming files in $LOCAL_PATH"
"$(dirname "$0")/rename-samples.sh"

echo "==> Syncing $FOLDER to server"
ssh "$SERVER" "mkdir -p $REMOTE_SAMPLES/$FOLDER"
rsync -avz "$LOCAL_PATH/" "$SERVER:$REMOTE_SAMPLES/$FOLDER/"

echo "==> Adding bank to SuperDirt boot config (if not already there)"
LOAD_LINE="    ~dirt.loadSoundFiles(\"$REMOTE_SAMPLES/$FOLDER\");"
ssh "$SERVER" "grep -qF '$REMOTE_SAMPLES/$FOLDER' $BOOT_FILE || sed -i 's|~dirt.start|$LOAD_LINE\n    ~dirt.start|' $BOOT_FILE"

echo "==> Restarting SuperCollider (SuperDirt will reload in ~25s)"
ssh "$SERVER" "tmux send-keys -t eul:2 C-c '' && sleep 1 && tmux send-keys -t eul:2 \"DISPLAY=:99 QTWEBENGINE_CHROMIUM_FLAGS='--no-sandbox' sclang -D -i none >/var/log/eul/superdirt.log 2>&1\" Enter"

echo ""
echo "Done. Wait ~25 seconds for SuperDirt to boot, then use:"
echo "  sound \"$BANK_NAME\"  -- in TidalCycles"
