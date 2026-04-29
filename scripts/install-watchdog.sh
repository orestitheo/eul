#!/usr/bin/env bash
# Deploy and enable the stream watchdog on the server.
# Run once from your local machine.

set -euo pipefail

SERVER="root@204.168.163.80"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Deploying watchdog script"
rsync -az "$SCRIPTS_DIR/watchdog.sh" "$SERVER:/opt/eul/watchdog.sh"
ssh "$SERVER" "chmod +x /opt/eul/watchdog.sh"

echo "==> Installing systemd units"
ssh "$SERVER" "cat > /etc/systemd/system/eul-watchdog.service" << 'EOF'
[Unit]
Description=eul stream watchdog
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/eul/watchdog.sh
User=root
EOF

ssh "$SERVER" "cat > /etc/systemd/system/eul-watchdog.timer" << 'EOF'
[Unit]
Description=eul stream watchdog — every 2 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=2min
Unit=eul-watchdog.service

[Install]
WantedBy=timers.target
EOF

echo "==> Enabling and starting timer"
ssh "$SERVER" "systemctl daemon-reload && systemctl enable --now eul-watchdog.timer"

echo ""
echo "Done. Verify with:"
echo "  ssh $SERVER 'systemctl list-timers eul-watchdog'"
echo "  ssh $SERVER 'journalctl -u eul-watchdog -n 20'"
echo "  ssh $SERVER 'tail -f /var/log/eul/watchdog.log'"
