#!/usr/bin/env bash
# Stream watchdog — checks for silence and auto-recovers the pipeline.
# Runs on the server via systemd timer every 2 minutes.

set -uo pipefail

LOG=/var/log/eul/watchdog.log
STREAM_URL="http://localhost:8000/stream"
TMUX_SESSION="eul"
SILENCE_THRESHOLD=-50  # dBFS — below this for 5s = silent

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"
}

reconnect_jack() {
    local left right
    left=$(jack_lsp 2>/dev/null | grep 'darkice.*left' | head -1)
    right=$(jack_lsp 2>/dev/null | grep 'darkice.*right' | head -1)
    if [[ -z "$left" || -z "$right" ]]; then
        log "  JACK: no darkice ports visible yet"
        return 1
    fi
    jack_connect SuperCollider:out_1 "$left" 2>/dev/null || true
    jack_connect SuperCollider:out_2 "$right" 2>/dev/null || true
    log "  JACK reconnected: $left / $right"
}

stream_mean_volume() {
    # Returns mean volume in dBFS, or "error" if stream unreachable
    local out
    out=$(timeout 15 ffmpeg -t 5 -i "$STREAM_URL" -af volumedetect -f null /dev/null 2>&1) || { echo "error"; return; }
    echo "$out" | grep -oP 'mean_volume: \K[-0-9.]+' || echo "error"
}

is_silent() {
    local vol="$1"
    [[ "$vol" == "error" ]] && return 0
    (( $(echo "$vol < $SILENCE_THRESHOLD" | bc -l) ))
}

restart_evolve() {
    log "  Restarting evolve loop (window 6)"
    tmux send-keys -t "${TMUX_SESSION}:6" C-c "" 2>/dev/null || true
    sleep 1
    tmux send-keys -t "${TMUX_SESSION}:6" "python3 -u -m eul.evolve" Enter
}

restart_darkice() {
    log "  Restarting DarkIce (window 4)"
    tmux send-keys -t "${TMUX_SESSION}:4" C-c "" 2>/dev/null || true
    sleep 2
    tmux send-keys -t "${TMUX_SESSION}:4" "darkice -c /opt/eul/config/darkice.cfg" Enter
    sleep 5
}

restart_supercollider() {
    log "  Restarting SuperCollider (window 2) — waiting 30s for SuperDirt boot"
    tmux send-keys -t "${TMUX_SESSION}:2" C-c "" 2>/dev/null || true
    sleep 1
    tmux send-keys -t "${TMUX_SESSION}:2" "DISPLAY=:99 QTWEBENGINE_CHROMIUM_FLAGS='--no-sandbox' sclang -D -i none >/var/log/eul/superdirt.log 2>&1" Enter
    sleep 30
}

restart_tidal() {
    # Recreate window 5 and boot ghci. Without this REPL, evolve has nowhere to
    # send patterns ("can't find window: 5") and the stream goes permanently silent.
    log "  Restarting TidalCycles (window 5) — waiting 25s for ghci/SuperDirt connect"
    tmux kill-window -t "${TMUX_SESSION}:5" 2>/dev/null || true
    tmux new-window -t "${TMUX_SESSION}:5" -n tidal
    sleep 1
    tmux send-keys -t "${TMUX_SESSION}:5" "cd /opt/eul && ghci -ghci-script /opt/eul/config/tidal_boot.hs" Enter
    sleep 25
}

recover() {
    local recovered=0

    # 1. Evolve loop
    if ! pgrep -f "eul.evolve" > /dev/null 2>&1; then
        log "Evolve loop dead"
        restart_evolve
        recovered=1
    fi

    # 2. DarkIce
    if ! pgrep -x darkice > /dev/null 2>&1; then
        log "DarkIce dead"
        restart_darkice
        reconnect_jack
        recovered=1
    fi

    # 3. JACK routing (darkice alive but ports not connected)
    if ! jack_lsp -c 2>/dev/null | grep -A5 "^SuperCollider:out_1$" | grep -q darkice; then
        log "JACK routing broken"
        reconnect_jack
        recovered=1
    fi

    # 4. SuperCollider/SuperDirt
    if ! pgrep -x scsynth > /dev/null 2>&1 || ! pgrep -x sclang > /dev/null 2>&1; then
        log "SuperCollider dead"
        restart_supercollider
        reconnect_jack
        recovered=1
    fi

    # 5. TidalCycles REPL (window 5 / ghci) — must come after SC so it can connect
    #    to SuperDirt. If the window or ghci is gone, patterns never reach SuperDirt.
    if ! tmux list-windows -t "$TMUX_SESSION" -F '#I' 2>/dev/null | grep -qx 5 \
       || ! pgrep -f tidal_boot.hs > /dev/null 2>&1; then
        log "TidalCycles REPL dead"
        restart_tidal
        recovered=1
    fi

    if [[ $recovered -eq 1 ]]; then
        sleep 3
        log "  Reloading patterns"
        python3 -m eul.evolve --once
        log "Recovery complete"
    else
        log "All processes alive — silence cause unknown, reloading patterns"
        python3 -m eul.evolve --once
    fi
}

main() {
    local vol
    vol=$(stream_mean_volume)

    if is_silent "$vol"; then
        log "Silence detected (${vol} dBFS) — recovering"
        recover
    fi
    # healthy: log nothing
}

main
