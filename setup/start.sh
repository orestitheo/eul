#!/usr/bin/env bash
# Start all eul services in a tmux session.
# Run from anywhere: bash /opt/eul/setup/start.sh
# Attach after: tmux attach -t eul

set -euo pipefail

SESSION="eul"
tmux kill-session -t $SESSION 2>/dev/null || true
kill $(pgrep sclang) $(pgrep scsynth) $(pgrep jackd) $(pgrep Xvfb) $(pgrep darkice) $(pgrep icecast2) 2>/dev/null || true
sleep 2

tmux new-session -d -s $SESSION -x 220 -y 50

# 0: Xvfb — virtual display required by sclang (Qt dependency)
tmux send-keys -t $SESSION:0 "Xvfb :99 -screen 0 1024x768x24 >/var/log/eul/xvfb.log 2>&1" Enter
sleep 2

# 1: JACK — headless virtual audio server (dummy driver, no soundcard needed)
tmux new-window -t $SESSION
tmux send-keys -t $SESSION:1 "jackd -d dummy -r 44100 -p 1024 >/var/log/eul/jack.log 2>&1" Enter
sleep 3

# 2: SuperCollider + SuperDirt — audio engine + sample playback
#    QTWEBENGINE_CHROMIUM_FLAGS needed to run sclang as root
tmux new-window -t $SESSION
tmux send-keys -t $SESSION:2 "DISPLAY=:99 QTWEBENGINE_CHROMIUM_FLAGS='--no-sandbox' sclang -D -i none >/var/log/eul/superdirt.log 2>&1" Enter
sleep 25

# 3: Icecast — HTTP streaming server on port 8000
tmux new-window -t $SESSION
tmux send-keys -t $SESSION:3 "icecast2 -c /opt/eul/config/icecast.xml -b >/var/log/eul/icecast.log 2>&1" Enter
sleep 2

# 4: DarkIce — encodes JACK audio and sends to Icecast
tmux new-window -t $SESSION
tmux send-keys -t $SESSION:4 "darkice -c /opt/eul/config/darkice.cfg >/var/log/eul/darkice.log 2>&1" Enter
sleep 3

# Wire SuperCollider output → DarkIce input in JACK
# Without this the stream is silent
jack_connect SuperCollider:out_1 darkice-$(pgrep darkice):left  2>/dev/null || \
  jack_connect SuperCollider:out_1 $(jack_lsp | grep darkice | grep left | head -1) 2>/dev/null || true
jack_connect SuperCollider:out_2 darkice-$(pgrep darkice):right 2>/dev/null || \
  jack_connect SuperCollider:out_2 $(jack_lsp | grep darkice | grep right | head -1) 2>/dev/null || true

# 5: TidalCycles REPL — interactive pattern input
tmux new-window -t $SESSION
tmux send-keys -t $SESSION:5 "ghci -ghci-script /opt/eul/config/tidal_boot.hs" Enter

echo "eul started."
echo "Stream: http://$(hostname -I | awk '{print $1}'):8000/stream"
echo "Attach: tmux attach -t eul  (window 5 = TidalCycles REPL)"
