#!/usr/bin/env python3
"""
audition.py — plays each sample bank one at a time so you can set good gain levels.

Usage:
  ssh -t root@204.168.163.80 "python3 /opt/eul/scripts/audition.py"

For each bank, type a number to set gain and advance, or +/- to nudge.
Evolve loop is paused while running and restored on exit.

Controls:
  1.4         → set gain to 1.4 and advance to next bank
  +           → louder (+0.1), replays
  -           → quieter (-0.1), replays
  Enter       → keep current gain and advance
  q           → quit
"""

import subprocess
import time
import sys
import signal

TMUX_SESSION = "eul"
TMUX_WINDOW = "5"
EVOLVE_WINDOW = "6"

BANKS = [
    ("dungeondrums", "drums",   14),
    ("rad",          "drums",   37),
    ("shxc1",        "drums",   15),
    ("drone",        "pad",     None),
    ("texture",      "texture", None),
    ("t99",          "pad",     None),
    ("ls",           "chords",  9),
    ("akatosh",      "chords",  2),
    ("blackmirror",  "chords",  1),
    ("discoveryone", "chords",  1),
    ("shxc",         "chords",  1),
    ("discoveryone", "voice",   None),
    ("akatosh",      "voice",   None),
    ("madonna",      "voice",   None),
]

def send(line):
    subprocess.run([
        "tmux", "send-keys", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}",
        line, "Enter"
    ])
    time.sleep(0.3)

def pause_evolve():
    subprocess.run(["tmux", "send-keys", "-t", f"{TMUX_SESSION}:{EVOLVE_WINDOW}", "C-c", ""])
    time.sleep(0.5)
    print("  (evolve loop paused)")

def resume_evolve():
    subprocess.run([
        "tmux", "send-keys", "-t", f"{TMUX_SESSION}:{EVOLVE_WINDOW}",
        "python3 -u /opt/eul/scripts/evolve.py 2>&1 | tee /var/log/eul/evolve.log", "Enter"
    ])
    print("  (evolve loop resumed)")

def play(bank, kind, slices, gain):
    if kind == "drums":
        seq = " ".join(f"{bank}:{i}" for i in range(min(8, slices)))
        send(f'd1 $ sound "{seq}" # gain {gain} # room 0')
    elif kind == "pad":
        if bank == "t99":
            send(f'd1 $ slow 4 $ sound "{bank}:0" # loopAt 4 # gain {gain} # room 0.8')
        else:
            send(f'd1 $ slow 4 $ sound "{bank}:0" # gain {gain} # room 0.8')
    elif kind == "texture":
        send(f'd1 $ slow 2 $ sound "texture:0 texture:1 texture:2" # gain {gain} # room 0.6')
    elif kind == "chords":
        send(f'd1 $ slow 3 $ sound "{bank}:0" # loopAt 4 # legato 1 # gain {gain} # room 0.7')
    elif kind == "voice":
        send(f'd1 $ slow 6 $ sound "{bank}:0" # gain {gain} # room 0.9 # note -2')

def cleanup(results):
    send("d1 silence")
    resume_evolve()
    if results:
        print("\n=== Gain table ===")
        for label, gain in results.items():
            print(f"  {label}: {gain}")

def main():
    results = {}

    pause_evolve()

    def on_exit(sig, frame):
        cleanup(results)
        sys.exit(0)
    signal.signal(signal.SIGINT, on_exit)

    print("\neul audition — type a number to set gain + advance, +/- to nudge, Enter to keep, q to quit\n")

    for bank, kind, slices in BANKS:
        gain = 1.0
        label = f"{bank} ({kind})"

        print(f"\n▶  {label}")
        play(bank, kind, slices, gain)

        while True:
            raw = input(f"   gain={gain}: ").strip()

            if raw == "q":
                cleanup(results)
                sys.exit(0)
            elif raw == "+":
                gain = round(gain + 0.1, 1)
                play(bank, kind, slices, gain)
            elif raw == "-":
                gain = round(max(0.1, gain - 0.1), 1)
                play(bank, kind, slices, gain)
            elif raw == "":
                results[label] = gain
                break
            else:
                try:
                    gain = round(float(raw), 1)
                    results[label] = gain
                    break
                except ValueError:
                    print("   type a number, +, -, or Enter")

    cleanup(results)

if __name__ == "__main__":
    main()
