#!/usr/bin/env python3
"""
eul audition — interactive mixer to find good gain levels.

Commands:
  list              show all available banks
  play <bank>       add/replace a bank in the mix (auto-detects type)
  stop <bank>       remove a bank from the mix
  stop all          clear everything
  gain <bank> <n>   set gain for a bank (e.g. gain ls 2.4)
  +  /  -           louder / quieter for last touched bank
  r                 replay all active layers
  status            show what's currently playing
  report            print final gain table
  q                 quit
"""

import subprocess
import time
import sys
import signal

TMUX_SESSION = "eul"
TMUX_WINDOW = "5"
EVOLVE_WINDOW = "6"

# All banks with their type and slice count
ALL_BANKS = {
    "dungeondrums": ("drums",   14),
    "rad":          ("drums",   37),
    "shxc1":        ("drums",   15),
    "drone":        ("pad",     1),
    "texture":      ("texture", 3),
    "t99":          ("pad",     1),
    "ls":           ("chords",  9),
    "akatosh":      ("chords",  2),
    "blackmirror":  ("chords",  1),
    "discoveryone": ("chords",  1),
    "shxc":         ("chords",  1),
    "madonna":      ("voice",   1),
}

# Which TidalCycles channel each bank type uses
TYPE_CHANNEL = {
    "drums":   "d4",
    "pad":     "d1",
    "texture": "d2",
    "chords":  "d6",
    "voice":   "d5",
}

# Active layers: bank -> {gain, channel, kind}
active = {}
last_touched = None

def send(line):
    subprocess.run([
        "tmux", "send-keys", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}",
        line, "Enter"
    ])
    time.sleep(0.3)

def pause_evolve():
    subprocess.run(["tmux", "send-keys", "-t", f"{TMUX_SESSION}:{EVOLVE_WINDOW}", "C-c", ""])
    time.sleep(0.5)
    print("  [evolve paused]")

def resume_evolve():
    subprocess.run([
        "tmux", "send-keys", "-t", f"{TMUX_SESSION}:{EVOLVE_WINDOW}",
        "python3 -u /opt/eul/scripts/evolve.py 2>&1 | tee /var/log/eul/evolve.log", "Enter"
    ])
    print("  [evolve resumed]")

def build_pattern(bank, kind, slices, gain):
    if kind == "drums":
        seq = " ".join(f"{bank}:{i}" for i in range(min(8, slices)))
        return f'$ sound "{seq}" # gain {gain} # room 0'
    elif kind == "pad":
        if bank == "t99":
            return f'$ slow 4 $ sound "{bank}:0" # loopAt 4 # legato 1 # gain {gain} # room 0.8'
        else:
            return f'$ slow 4 $ sound "{bank}:0" # gain {gain} # room 0.8'
    elif kind == "texture":
        return f'$ slow 2 $ sound "texture:0 texture:1 texture:2" # gain {gain} # room 0.6'
    elif kind == "chords":
        return f'$ slow 3 $ sound "{bank}:0" # loopAt 4 # legato 1 # gain {gain} # room 0.7'
    elif kind == "voice":
        return f'$ slow 6 $ sound "{bank}:0" # gain {gain} # room 0.9 # note -2'

def play_bank(bank, kind, slices, gain):
    ch = TYPE_CHANNEL.get(kind, "d1")
    pat = build_pattern(bank, kind, slices, gain)
    send(f"{ch} {pat}")

def stop_channel(ch):
    send(f"{ch} silence")

def replay_all():
    if not active:
        print("  nothing playing")
        return
    for bank, info in active.items():
        kind, slices = ALL_BANKS[bank]
        play_bank(bank, kind, slices, info["gain"])

def print_status():
    if not active:
        print("  [nothing playing]")
        return
    print("  Active layers:")
    for bank, info in active.items():
        bar = "█" * max(0, round(info["gain"] * 5))
        marker = " ◀" if bank == last_touched else ""
        print(f"    {info['ch']}  {bank:<16} gain={info['gain']:.1f}  {bar:<20}{marker}")

def print_report():
    if not active:
        print("  no data yet")
        return
    print("\n" + "="*45)
    print("  Final gain table")
    print("="*45)
    for bank, info in active.items():
        print(f"  {bank:<16} ({info['kind']:<8})  gain = {info['gain']:.1f}")
    print("="*45)

def print_banks():
    print("\n  Available banks:")
    for bank, (kind, slices) in ALL_BANKS.items():
        status = "  ▶ playing" if bank in active else ""
        print(f"    {bank:<16} ({kind}){status}")

def cmd_play(bank):
    global last_touched
    if bank not in ALL_BANKS:
        print(f"  unknown bank '{bank}' — type 'list' to see all")
        return
    kind, slices = ALL_BANKS[bank]
    ch = TYPE_CHANNEL[kind]
    gain = active[bank]["gain"] if bank in active else 1.0
    active[bank] = {"gain": gain, "ch": ch, "kind": kind}
    last_touched = bank
    play_bank(bank, kind, slices, gain)
    print(f"  playing {bank} on {ch}  gain={gain:.1f}")

def cmd_stop(bank):
    if bank == "all":
        for info in active.values():
            stop_channel(info["ch"])
        active.clear()
        print("  stopped all")
        return
    if bank not in active:
        print(f"  {bank} is not playing")
        return
    stop_channel(active[bank]["ch"])
    del active[bank]
    print(f"  stopped {bank}")

def cmd_gain(bank, val):
    global last_touched
    if bank not in ALL_BANKS:
        print(f"  unknown bank '{bank}'")
        return
    try:
        gain = round(float(val), 1)
        if gain <= 0:
            print("  gain must be > 0")
            return
    except ValueError:
        print("  invalid gain value")
        return
    kind, slices = ALL_BANKS[bank]
    ch = TYPE_CHANNEL[kind]
    active[bank] = {"gain": gain, "ch": ch, "kind": kind}
    last_touched = bank
    play_bank(bank, kind, slices, gain)
    bar = "█" * max(0, round(gain * 5))
    print(f"  {bank}  gain={gain:.1f}  {bar}")

def cmd_nudge(direction):
    global last_touched
    if not last_touched:
        print("  play a bank first")
        return
    bank = last_touched
    info = active.get(bank)
    if not info:
        print(f"  {bank} is not playing — use 'play {bank}' first")
        return
    gain = round(info["gain"] + (0.1 if direction == "+" else -0.1), 1)
    gain = max(0.1, gain)
    cmd_gain(bank, gain)

def main():
    pause_evolve()

    def on_exit(sig, frame):
        print()
        print_report()
        send("hush")
        resume_evolve()
        sys.exit(0)
    signal.signal(signal.SIGINT, on_exit)

    print("\n" + "="*45)
    print("  eul audition")
    print("="*45)
    print("  play <bank>        add to mix")
    print("  stop <bank>        remove from mix")
    print("  stop all           clear mix")
    print("  gain <bank> <n>    set gain")
    print("  + / -              nudge last touched bank")
    print("  r                  replay all")
    print("  status             show active layers")
    print("  list               show all banks")
    print("  report             print gain table")
    print("  q                  quit")
    print("="*45 + "\n")

    while True:
        try:
            raw = input("audition> ").strip()
        except EOFError:
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "q":
            print_report()
            send("hush")
            resume_evolve()
            sys.exit(0)
        elif cmd == "list":
            print_banks()
        elif cmd == "play" and len(parts) >= 2:
            cmd_play(parts[1])
        elif cmd == "stop" and len(parts) >= 2:
            cmd_stop(parts[1] if parts[1] != "all" else "all")
        elif cmd == "gain" and len(parts) >= 3:
            cmd_gain(parts[1], parts[2])
        elif cmd in ("+", "-"):
            cmd_nudge(cmd)
        elif cmd == "r":
            replay_all()
            print_status()
        elif cmd == "status":
            print_status()
        elif cmd == "report":
            print_report()
        else:
            print("  ?  type 'list' to see banks or check the commands above")

if __name__ == "__main__":
    main()
