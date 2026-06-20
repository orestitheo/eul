#!/usr/bin/env bash
# Add a new sample bank end-to-end: preprocess → audition → register → deploy.
#
# Usage:
#   ./scripts/add-bank.sh <folder> <strain> [options]
#
# Strains: Drone, Texture, Chord, Voice, Drum
#
# Options:
#   --slices N     Required for Drum strain (total slice count)
#   --weight N     Selection weight (default: strain default)
#   --no-loop      Chord only — allow glitch/chop (default: looping=True)
#   --samples N    Override sample count (default: auto-counted from folder)
#   --skip-prep    Skip rename + normalize + fade preprocessing
#
# Example:
#   ./scripts/add-bank.sh samples/percussive/mynewkit Drum --slices 20
#   ./scripts/add-bank.sh samples/melodic/chords/mypad Chord --weight 3

set -euo pipefail

SERVER="root@204.168.163.80"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
LOCAL_SAMPLES="$REPO_ROOT/samples"
REMOTE_SAMPLES="/opt/eul/samples"
BOOT_FILE="/root/.config/SuperCollider/startup.scd"

usage() {
  echo "Usage: $0 <folder> <strain> [--slices N] [--weight N] [--no-loop] [--samples N] [--skip-prep]"
  echo "Strains: Drone, Texture, Chord, Voice, Drum"
  exit 1
}

[[ $# -lt 2 ]] && usage

FOLDER="$1"
STRAIN="$2"
shift 2

# Strain → channel (also validates the strain; macOS bash 3.2 has no declare -A)
case "$STRAIN" in
  Drone)   CHANNEL=d1 ;;
  Texture) CHANNEL=d2 ;;
  Chord)   CHANNEL=d6 ;;
  Voice)   CHANNEL=d5 ;;
  Drum)    CHANNEL=d4 ;;
  *) echo "Error: unknown strain '$STRAIN'. Choose: Drone Texture Chord Voice Drum"; exit 1 ;;
esac

# Parse optional flags
SLICES=""
WEIGHT=""
NO_LOOP=0
SAMPLES_OVERRIDE=""
SKIP_PREP=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --slices)   SLICES="$2";           shift 2 ;;
    --weight)   WEIGHT="$2";           shift 2 ;;
    --no-loop)  NO_LOOP=1;             shift   ;;
    --samples)  SAMPLES_OVERRIDE="$2"; shift 2 ;;
    --skip-prep)SKIP_PREP=1;           shift   ;;
    *) echo "Unknown flag: $1"; usage ;;
  esac
done

# Drum requires --slices
if [[ "$STRAIN" == "Drum" && -z "$SLICES" ]]; then
  echo "Error: Drum strain requires --slices N"
  exit 1
fi

# --no-loop only means something for Chord
if [[ $NO_LOOP -eq 1 && "$STRAIN" != "Chord" ]]; then
  echo "Warning: --no-loop only applies to Chord strain, ignoring"
  NO_LOOP=0
fi

# ── 1. Preprocess ───────────────────────────────────────────────────
# rename-samples.sh runs first — it may lowercase the folder itself,
# so the path is resolved after it.
if [[ $SKIP_PREP -eq 0 ]]; then
  echo "==> Renaming samples (lowercase, strip timestamps)"
  "$SCRIPTS_DIR/rename-samples.sh"
fi

FOLDER="${FOLDER#samples/}"
FOLDER="$(echo "${FOLDER// /_}" | tr '[:upper:]' '[:lower:]')"
LOCAL_PATH="$LOCAL_SAMPLES/$FOLDER"

if [[ ! -d "$LOCAL_PATH" ]]; then
  echo "Error: folder not found: $LOCAL_PATH"
  exit 1
fi

BANK_NAME="$(basename "$FOLDER")"

echo "==> Bank: $BANK_NAME  Strain: $STRAIN  Channel: $CHANNEL"

if [[ $SKIP_PREP -eq 0 ]]; then
  echo ""
  echo "==> Normalizing samples"
  "$SCRIPTS_DIR/normalize-samples.sh" "$LOCAL_PATH"

  echo ""
  echo "==> Adding fades"
  "$SCRIPTS_DIR/fade-samples.sh" "$LOCAL_PATH"
else
  echo "  (skipping preprocess)"
fi

# ── 2. Count samples ────────────────────────────────────────────────
if [[ -n "$SAMPLES_OVERRIDE" ]]; then
  SAMPLE_COUNT="$SAMPLES_OVERRIDE"
else
  SAMPLE_COUNT=$(find "$LOCAL_PATH" -maxdepth 1 \( -name "*.wav" -o -name "*.aif" -o -name "*.aiff" -o -name "*.mp3" -o -name "*.flac" \) | wc -l | tr -d ' ')
fi
echo ""
echo "==> $SAMPLE_COUNT sample(s) detected"

# ── 3. Rsync samples to server ──────────────────────────────────────
echo ""
echo "==> Syncing $FOLDER to server"
ssh "$SERVER" "mkdir -p $REMOTE_SAMPLES/$FOLDER"
rsync -avz "$LOCAL_PATH/" "$SERVER:$REMOTE_SAMPLES/$FOLDER/"

# ── 4. Register with SuperDirt (loadSoundFiles) ─────────────────────
echo ""
echo "==> Registering with SuperDirt boot config"
LOAD_LINE="    ~dirt.loadSoundFiles(\"$REMOTE_SAMPLES/$FOLDER\");"
ssh "$SERVER" "grep -qF '$REMOTE_SAMPLES/$FOLDER' $BOOT_FILE || sed -i 's|~dirt.start|$LOAD_LINE\n    ~dirt.start|' $BOOT_FILE"

# ── 5. Restart SuperCollider ────────────────────────────────────────
echo ""
echo "==> Restarting SuperCollider (waiting 30s for SuperDirt to boot)"
ssh "$SERVER" "tmux send-keys -t eul:2 C-c '' && sleep 1 && tmux send-keys -t eul:2 \"DISPLAY=:99 QTWEBENGINE_CHROMIUM_FLAGS='--no-sandbox' sclang -D -i none >/var/log/eul/superdirt.log 2>&1\" Enter"
sleep 30

# ── 6. Reconnect JACK ───────────────────────────────────────────────
echo ""
echo "==> Reconnecting JACK routing"
ssh "$SERVER" "
  DARKICE_LEFT=\$(jack_lsp | grep 'darkice.*left')
  DARKICE_RIGHT=\$(jack_lsp | grep 'darkice.*right')
  jack_connect SuperCollider:out_1 \"\$DARKICE_LEFT\" 2>/dev/null || true
  jack_connect SuperCollider:out_2 \"\$DARKICE_RIGHT\" 2>/dev/null || true
  echo \"  Connected: \$DARKICE_LEFT / \$DARKICE_RIGHT\"
"

# ── 7. Audition ─────────────────────────────────────────────────────
echo ""
echo "==> Auditioning $BANK_NAME on $CHANNEL for 15s..."
if [[ "$STRAIN" == "Drum" ]]; then
  PATTERN="$CHANNEL \$ n (shuffle 8 \$ irand $SLICES) # s \"$BANK_NAME\" # room 0 # gain 1"
else
  PATTERN="$CHANNEL \$ s \"$BANK_NAME\" # gain 1"
fi

ssh "$SERVER" "tmux send-keys -t eul:5 '$PATTERN' Enter"
sleep 15
ssh "$SERVER" "tmux send-keys -t eul:5 '$CHANNEL \$ silence' Enter"

echo ""
read -rp "Register this bank? [y/N] " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo ""
  echo "==> Discarding. Cleaning up boot config and remote samples..."
  ssh "$SERVER" "sed -i '\|$REMOTE_SAMPLES/$FOLDER|d' $BOOT_FILE && rm -rf '$REMOTE_SAMPLES/$FOLDER'"
  echo "Done. Local samples kept at $LOCAL_PATH."
  exit 0
fi

# ── 8. Register in banks.py ─────────────────────────────────────────
echo ""
echo "==> Registering in src/eul/banks.py"
REGISTER_ARGS=("$BANK_NAME" "$STRAIN" "$FOLDER" "$SAMPLE_COUNT")
[[ -n "$SLICES" ]]  && REGISTER_ARGS+=(--slices "$SLICES")
[[ -n "$WEIGHT" ]]  && REGISTER_ARGS+=(--weight "$WEIGHT")
[[ $NO_LOOP -eq 1 ]] && REGISTER_ARGS+=(--no-loop)

python3 "$SCRIPTS_DIR/_register_bank.py" "${REGISTER_ARGS[@]}"

# ── 9. Rsync banks.py + evolve ──────────────────────────────────────
echo ""
echo "==> Deploying updated banks.py"
rsync -az "$REPO_ROOT/pyproject.toml" "$REPO_ROOT/src" "$SERVER:/opt/eul/"

echo ""
echo "==> Applying patterns"
ssh "$SERVER" "python3 -m eul.evolve --once"

echo ""
echo "Done. Bank '$BANK_NAME' is live on $CHANNEL."
echo "  Tidal REPL: $CHANNEL \$ s \"$BANK_NAME\""
