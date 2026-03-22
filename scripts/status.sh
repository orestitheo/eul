#!/usr/bin/env bash
# Check the health of all eul services on the server.
# Usage: ./scripts/status.sh

SERVER="root@204.168.163.80"

echo "==> Processes"
ssh "$SERVER" "
  for proc in jackd sclang scsynth icecast2 darkice ghci; do
    if pgrep -x \$proc > /dev/null 2>&1; then
      echo \"  ✓ \$proc\"
    else
      echo \"  ✗ \$proc  (NOT RUNNING)\"
    fi
  done
"

echo ""
echo "==> Stream"
STATUS=$(curl -s --max-time 3 -r 0-1 -o /dev/null -w "%{http_code}" http://204.168.163.80:8000/stream 2>/dev/null || echo "000")
if [[ "$STATUS" == "200" ]]; then
  echo "  ✓ http://204.168.163.80:8000/stream  (live)"
else
  echo "  ✗ stream not reachable (HTTP $STATUS)"
fi

echo ""
echo "==> JACK routing"
ssh "$SERVER" "
  SC_OUT=\$(jack_lsp -c 2>/dev/null | grep -A1 'SuperCollider:out' | grep darkice || echo '')
  if [[ -n \"\$SC_OUT\" ]]; then
    echo \"  ✓ SuperCollider → DarkIce connected\"
  else
    echo \"  ✗ SuperCollider not routed to DarkIce (stream will be silent)\"
    echo \"    Fix: ssh $SERVER then run:\"
    echo \"      jack_connect SuperCollider:out_1 \\\$(jack_lsp | grep 'darkice.*left')\"
    echo \"      jack_connect SuperCollider:out_2 \\\$(jack_lsp | grep 'darkice.*right')\"
  fi
"

echo ""
echo "==> SuperDirt log (last 5 lines)"
ssh "$SERVER" "tail -5 /var/log/eul/superdirt.log 2>/dev/null || echo '  (no log)'"

echo ""
echo "==> Sample banks loaded"
ssh "$SERVER" "grep 'loadSoundFiles' /root/.config/SuperCollider/startup.scd | sed 's/.*samples\///;s/\").*//' | sed 's/^/  /'"
