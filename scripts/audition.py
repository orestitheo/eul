#!/usr/bin/env python3
"""
audition.py — plays each sample bank so you can dial in good gain levels.

Controls:
  +       → louder (+0.1), replays
  -       → quieter (-0.1), replays
  1.4     → set gain to 1.4, replays
  Enter   → confirm current gain and move to next
  r       → replay current bank
  q       → quit and print results
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

def resume_evolve():
    subprocess.run([
        "tmux", "send-keys", "-t", f"{TMUX_SESSION}:{EVOLVE_WINDOW}",
        "python3 -u /opt/eul/scripts/evolve.py 2>&1 | tee /var/log/eul/evolve.log", "Enter"
    ])

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

def print_status(gain):
    bar = "█" * max(0, round(gain * 5))
    print(f"   gain: {gain:.1f}  {bar:<20}")

def cleanup(results):
    send("d1 silence")
    resume_evolve()
    if results:
        print("\n\n=== Gain table — paste into evolve.py ===\n")
        for label, gain in results.items():
            print(f"  {label}: {gain}")
        print()

def main():
    results = {}
    total = len(BANKS)

    pause_evolve()

    def on_exit(sig, frame):
        print()
        cleanup(results)
        sys.exit(0)
    signal.signal(signal.SIGINT, on_exit)

    print("\n" + "="*50)
    print("  eul audition")
    print("  +/-: adjust gain   number: set gain   r: replay   Enter: confirm & next   q: quit")
    print("="*50)

    for idx, (bank, kind, slices) in enumerate(BANKS):
        gain = 1.0
        label = f"{bank} ({kind})"

        print(f"\n[{idx+1}/{total}]  {label}")
        print(f"  Playing now...")
        play(bank, kind, slices, gain)
        print_status(gain)

        while True:
            raw = input("  +  -  r  number  Enter=confirm  q=quit  > ").strip()

            if raw == "q":
                cleanup(results)
                sys.exit(0)
            elif raw == "r":
                play(bank, kind, slices, gain)
                print_status(gain)
            elif raw == "+":
                gain = round(gain + 0.1, 1)
                play(bank, kind, slices, gain)
                print_status(gain)
            elif raw == "-":
                gain = round(max(0.1, gain - 0.1), 1)
                play(bank, kind, slices, gain)
                print_status(gain)
            elif raw == "":
                results[label] = gain
                print(f"  ✓ confirmed {label} = {gain}")
                break
            else:
                try:
                    val = round(float(raw), 1)
                    if val <= 0:
                        print("  gain must be > 0")
                    else:
                        gain = val
                        play(bank, kind, slices, gain)
                        print_status(gain)
                except ValueError:
                    print("  didn't understand that — try +, -, a number like 1.4, or Enter")

    cleanup(results)

if __name__ == "__main__":
    main()
