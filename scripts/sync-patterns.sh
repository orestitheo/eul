#!/usr/bin/env bash
# Push pattern file to the server and optionally send lines to the TidalCycles REPL.
#
# Usage:
#   ./scripts/sync-patterns.sh                  # syncs patterns/main.tidal, prompts to send to REPL
#   ./scripts/sync-patterns.sh patterns/foo.tidal

set -euo pipefail

SERVER="root@204.168.163.80"
LOCAL_PATTERNS="$(cd "$(dirname "$0")/../patterns" && pwd)"
REMOTE_PATTERNS="/opt/eul/patterns"
PATTERN_FILE="${1:-$LOCAL_PATTERNS/main.tidal}"
REMOTE_FILE="$REMOTE_PATTERNS/$(basename "$PATTERN_FILE")"

echo "==> Syncing $(basename "$PATTERN_FILE") to server"
ssh "$SERVER" "mkdir -p $REMOTE_PATTERNS"
rsync -avz "$PATTERN_FILE" "$SERVER:$REMOTE_FILE"

echo ""
echo "Synced. To load in TidalCycles:"
echo "  SSH in: ssh $SERVER"
echo "  Attach: tmux attach -t eul  (then Ctrl+b 5 for REPL)"
echo "  Paste the pattern lines manually at the tidal> prompt."
echo ""
echo "Or send a single line non-interactively:"
echo "  ssh $SERVER \"tmux send-keys -t eul:5 'your pattern here' Enter\""
