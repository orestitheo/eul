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
#   5. Runs evolve --once to apply
# Note: register the bank manually in src/eul/banks.py before running this script.

set -euo pipefail

SERVER="root@204.168.163.80"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_SAMPLES="$SCRIPTS_DIR/../samples"
REMOTE_SAMPLES="/opt/eul/samples"
BOOT_FILE="/root/.config/SuperCollider/startup.scd"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path-to-sample-folder>"
  echo "Example: $0 samples/percussive/mynewkit"
  exit 1
fi

FOLDER="$1"
FOLDER="${FOLDER#samples/}"
LOCAL_PATH="$(cd "$LOCAL_SAMPLES" && pwd)/$FOLDER"

if [[ ! -d "$LOCAL_PATH" ]]; then
  echo "Error: folder not found: $LOCAL_PATH"
  exit 1
fi

BANK_NAME="$(basename "$FOLDER")"
COUNT=$(ls "$LOCAL_PATH" | wc -l | tr -d ' ')

echo "==> Renaming files in $LOCAL_PATH"
"$SCRIPTS_DIR/rename-samples.sh"

echo "==> Syncing $FOLDER to server"
ssh "$SERVER" "mkdir -p $REMOTE_SAMPLES/$FOLDER"
rsync -avz "$LOCAL_PATH/" "$SERVER:$REMOTE_SAMPLES/$FOLDER/"

echo "==> Adding bank to SuperDirt boot config (if not already there)"
LOAD_LINE="    ~dirt.loadSoundFiles(\"$REMOTE_SAMPLES/$FOLDER\");"
ssh "$SERVER" "grep -qF '$REMOTE_SAMPLES/$FOLDER' $BOOT_FILE || sed -i 's|~dirt.start|$LOAD_LINE\n    ~dirt.start|' $BOOT_FILE"

echo "==> Restarting SuperCollider (SuperDirt will reload in ~25s)"
ssh "$SERVER" "tmux send-keys -t eul:2 C-c '' && sleep 1 && tmux send-keys -t eul:2 \"DISPLAY=:99 QTWEBENGINE_CHROMIUM_FLAGS='--no-sandbox' sclang -D -i none >/var/log/eul/superdirt.log 2>&1\" Enter"
echo "  Waiting 30s for SuperDirt to boot..."
sleep 30

echo "==> Reconnecting JACK routing"
ssh "$SERVER" "
  DARKICE_LEFT=\$(jack_lsp | grep 'darkice.*left')
  DARKICE_RIGHT=\$(jack_lsp | grep 'darkice.*right')
  jack_connect SuperCollider:out_1 \"\$DARKICE_LEFT\" 2>/dev/null || true
  jack_connect SuperCollider:out_2 \"\$DARKICE_RIGHT\" 2>/dev/null || true
  echo \"  Connected: \$DARKICE_LEFT / \$DARKICE_RIGHT\"
"

echo "==> Restoring patterns"
ssh "$SERVER" "python3 -m eul.evolve --once"

echo ""
echo "Done. Bank: $BANK_NAME ($COUNT samples)"
echo "  Wait ~25s for SuperDirt to reload, then use: sound \"$BANK_NAME\""
echo "  Remember to add the bank to src/eul/banks.py and rsync before running this script."
