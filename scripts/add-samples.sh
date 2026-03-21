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
#   5. Updates evolve.py with the new bank (DRUM_BANKS / CHORD_SAMPLES / VOICE_SAMPLES)
#   6. Syncs evolve.py to server

set -euo pipefail

SERVER="root@204.168.163.80"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_SAMPLES="$SCRIPTS_DIR/../samples"
REMOTE_SAMPLES="/opt/eul/samples"
BOOT_FILE="/root/.config/SuperCollider/startup.scd"
EVOLVE="$SCRIPTS_DIR/evolve.py"

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
ssh "$SERVER" "python3 /opt/eul/scripts/evolve.py --once"

echo "==> Updating evolve.py"
python3 - "$EVOLVE" "$FOLDER" "$BANK_NAME" "$COUNT" <<'PYEOF'
import sys, re

evolve_path, folder, bank, count = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
text = open(evolve_path).read()

if folder.startswith("percussive/"):
    if f'"{bank}"' in text:
        print(f"  {bank} already in DRUM_BANKS, skipping")
    else:
        text = re.sub(
            r'(DRUM_BANKS\s*=\s*\{)',
            f'\\1\n    "{bank}": {count},',
            text
        )
        print(f"  added \"{bank}\": {count} to DRUM_BANKS")

elif folder.startswith("melodic/chords/"):
    if f'"{bank}:0"' in text:
        print(f"  {bank} already in CHORD_SAMPLES, skipping")
    else:
        new_entries = " +\n    [f\"{bank}:{{i}}\" for i in range({count})]".replace("{bank}", bank).replace("{count}", str(count))
        text = re.sub(
            r'(CHORD_SAMPLES\s*=\s*\([\s\S]*?)\)',
            lambda m: m.group(0)[:-1] + new_entries + '\n)',
            text,
            count=1
        )
        print(f"  added {count} entries for {bank} to CHORD_SAMPLES")

elif folder.startswith("melodic/singletone/"):
    if f'"{bank}:0"' in text:
        print(f"  {bank} already in VOICE_SAMPLES, skipping")
    else:
        text = re.sub(
            r'(VOICE_SAMPLES\s*=\s*\[)',
            f'\\1"{bank}:0", ',
            text
        )
        print(f"  added \"{bank}:0\" to VOICE_SAMPLES")

else:
    print(f"  folder type not recognised — add to evolve.py manually if needed")
    sys.exit(0)

open(evolve_path, 'w').write(text)
PYEOF

echo "==> Syncing evolve.py to server"
rsync -az "$EVOLVE" "$SERVER:/opt/eul/scripts/evolve.py"

echo ""
echo "Done. Bank: $BANK_NAME ($COUNT samples)"
echo "  Wait ~25s for SuperDirt to reload, then use: sound \"$BANK_NAME\""
echo "  evolve.py updated + synced — new bank active from next evolution cycle"
