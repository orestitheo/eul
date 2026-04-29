"""
send.py — send pattern lines to the TidalCycles REPL via tmux.
"""

import subprocess
import time

TMUX_SESSION = "eul"
TMUX_WINDOW  = "5"


def send(line, delay=0.4):
    subprocess.run([
        "tmux", "send-keys", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}",
        line, "Enter"
    ])
    time.sleep(delay)


def send_all(lines, delay=0.4):
    for line in lines:
        print(f"  > {line[:100]}")
        send(line, delay)
