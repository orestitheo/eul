#!/usr/bin/env python3
"""
audition.py — plays each sample bank one at a time so you can set good gain levels.

Usage:
  python3 /opt/eul/scripts/audition.py

For each bank it plays a short pattern, waits for you to press Enter,
then moves to the next. At the end it prints a gain table you can paste
into evolve.py.

Controls:
  Enter       → next bank (keep current gain)
  +           → louder  (+0.1)
  -           → quieter (-0.1)
  number      → set gain directly (e.g. 1.4)
  q           → quit
"""

import subprocess
import time
import sys

TMUX_SESSION = "eul"
TMUX_WINDOW = "5"

BANKS = [
    # (name, type, max_slices_or_none)
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
        folder = "singletone" if bank in ("discoveryone", "akatosh", "madonna") else "chords"
        send(f'd1 $ slow 6 $ sound "{bank}:0" # gain {gain} # room 0.9 # note -2')

def main():
    results = {}
    print("\neul audition — press Enter to advance, +/- to adjust, number to set gain, q to quit\n")

    for bank, kind, slices in BANKS:
        gain = 1.0
        label = f"{bank} ({kind})"

        print(f"\n▶  {label}  — gain: {gain}")
        play(bank, kind, slices, gain)

        while True:
            raw = input(f"   [{label}] gain={gain}  (+/-/number/Enter/q): ").strip()
            if raw == "q":
                send("d1 silence")
                print("\nResults so far:")
                for k, v in results.items():
                    print(f"  {k}: {v}")
                sys.exit(0)
            elif raw == "+":
                gain = round(gain + 0.1, 1)
            elif raw == "-":
                gain = round(max(0.1, gain - 0.1), 1)
            elif raw == "":
                results[label] = gain
                break
            else:
                try:
                    gain = round(float(raw), 1)
                except ValueError:
                    pass

            print(f"   → gain: {gain}")
            play(bank, kind, slices, gain)

    send("d1 silence")
    print("\n\n=== Final gain table ===")
    print("Paste these into evolve.py:\n")
    for label, gain in results.items():
        print(f"  {label}: {gain}")

if __name__ == "__main__":
    main()
