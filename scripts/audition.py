#!/usr/bin/env python3
"""
eul audition — interactive mixer to find good gain levels.
Uses curses for a persistent status bar at the bottom.
"""

import subprocess
import time
import sys
import signal
import curses

TMUX_SESSION = "eul"
TMUX_WINDOW = "5"
EVOLVE_WINDOW = "6"

ALL_BANKS = {
    "dungeondrums": ("drums",   14),
    "rad":          ("drums",   37),
    "shxc1":        ("drums",   15),
    "drone":        ("pad",     3),
    "texture":      ("texture", 3),
    "t99":          ("pad",     1),
    "ls":           ("chords",  9),
    "akatosh":      ("chords",  2),
    "blackmirror":  ("chords",  1),
    "discoveryone": ("chords",  1),
    "shxc":         ("chords",  1),
    "madonna":      ("voice",   1),
}

TYPE_CHANNEL = {
    "drums":   "d4",
    "pad":     "d1",
    "texture": "d2",
    "chords":  "d6",
    "voice":   "d5",
}

active = {}
last_touched = None
log_lines = []

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

def build_pattern(bank, kind, slices, gain):
    if kind == "drums":
        seq = " ".join(f"{bank}:{i}" for i in range(min(8, slices)))
        return f'$ sound "{seq}" # gain {gain} # room 0'
    elif kind == "pad":
        if bank == "t99":
            return f'$ slow 4 $ sound "{bank}:0" # loopAt 4 # legato 1 # gain {gain} # room 0.8'
        elif bank == "drone":
            return f'$ slow 4 $ sound "drone:0 drone:1 drone:2" # gain {gain} # room 0.8'
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

def cmd_play(arg):
    global last_touched
    # Support bank:index syntax (e.g. drone:1)
    if ":" in arg:
        bank, idx = arg.rsplit(":", 1)
        try:
            idx = int(idx)
        except ValueError:
            return f"invalid index in '{arg}'"
    else:
        bank, idx = arg, None

    if bank not in ALL_BANKS:
        return f"unknown bank '{bank}'"
    kind, slices = ALL_BANKS[bank]
    ch = TYPE_CHANNEL[kind]
    key = arg  # use bank:idx as the active key so they don't overwrite each other
    gain = active[key]["gain"] if key in active else 1.0
    active[key] = {"gain": gain, "ch": ch, "kind": kind}
    last_touched = key

    if idx is not None:
        # Play single slice directly
        pat = build_pattern(bank, kind, slices, gain)
        # Override sound to specific index
        import re
        pat = re.sub(r'sound "[^"]+"', f'sound "{bank}:{idx}"', pat)
        send(f"{ch} {pat}")
    else:
        play_bank(bank, kind, slices, gain)
    return f"playing {key} on {ch}  gain={gain:.1f}"

def cmd_stop(key):
    if key == "all":
        send("hush")
        active.clear()
        return "stopped all"
    if key not in active:
        return f"{key} is not playing"
    send(f"{active[key]['ch']} silence")
    del active[key]
    return f"stopped {key}"

def cmd_gain(key, val):
    global last_touched
    bank = key.split(":")[0] if ":" in key else key
    if bank not in ALL_BANKS:
        return f"unknown bank '{bank}'"
    try:
        gain = round(float(val), 1)
        if gain <= 0:
            return "gain must be > 0"
    except ValueError:
        return "invalid gain value"
    kind, slices = ALL_BANKS[bank]
    ch = TYPE_CHANNEL[kind]
    active[key] = {"gain": gain, "ch": ch, "kind": kind}
    last_touched = key
    play_bank(bank, kind, slices, gain)
    bar = "█" * max(0, round(gain * 5))
    return f"{key}  gain={gain:.1f}  {bar}"

def cmd_nudge(direction):
    global last_touched
    if not last_touched:
        return "play a bank first"
    bank = last_touched
    if bank not in active:
        return f"{bank} not playing — use 'play {bank}' first"
    gain = round(active[bank]["gain"] + (0.1 if direction == "+" else -0.1), 1)
    gain = max(0.1, gain)
    return cmd_gain(bank, gain)

def get_status_lines():
    lines = []
    if not active:
        lines.append("  [nothing playing]")
    else:
        for bank, info in active.items():
            bar = "█" * max(0, round(info["gain"] * 5))
            marker = " ◀" if bank == last_touched else ""
            lines.append(f"  {info['ch']}  {bank:<16} {info['gain']:.1f}  {bar:<15}{marker}")
    return lines

def get_report():
    if not active:
        return ["  no data yet"]
    lines = ["", "  === Final gain table ==="]
    for bank, info in active.items():
        lines.append(f"  {bank:<16} ({info['kind']:<8})  gain = {info['gain']:.1f}")
    lines.append("")
    return lines

def main(stdscr):
    global log_lines

    curses.curs_set(1)
    curses.use_default_colors()
    stdscr.scrollok(False)

    pause_evolve()

    bank_list = list(ALL_BANKS.keys())

    def draw(input_buf=""):
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # --- top: bank list ---
        header = "  Banks: " + "  ".join(bank_list)
        stdscr.addstr(0, 0, header[:w-1], curses.A_DIM)
        stdscr.addstr(1, 0, "─" * (w-1), curses.A_DIM)

        # --- middle: log output ---
        log_area_top = 2
        status_height = len(active) + 3  # layers + borders + title
        help_height = 2
        log_area_bottom = h - status_height - help_height - 2  # input line
        log_area_height = max(1, log_area_bottom - log_area_top)

        visible_logs = log_lines[-(log_area_height):]
        for i, line in enumerate(visible_logs):
            try:
                stdscr.addstr(log_area_top + i, 0, line[:w-1])
            except curses.error:
                pass

        # --- status box ---
        status_top = h - status_height - help_height - 1
        try:
            stdscr.addstr(status_top, 0, "─" * (w-1), curses.A_DIM)
            stdscr.addstr(status_top + 1, 0, "  Active layers:", curses.A_BOLD)
            status_lines = get_status_lines()
            for i, line in enumerate(status_lines):
                stdscr.addstr(status_top + 2 + i, 0, line[:w-1])
        except curses.error:
            pass

        # --- help bar ---
        help_top = h - help_height - 1
        help_text = "  play <bank>  stop <bank>  stop all  gain <bank> <n>  +  -  r  list  report  q"
        try:
            stdscr.addstr(help_top, 0, "─" * (w-1), curses.A_DIM)
            stdscr.addstr(help_top + 1, 0, help_text[:w-1], curses.A_DIM)
        except curses.error:
            pass

        # --- input line ---
        prompt = "audition> " + input_buf
        try:
            stdscr.addstr(h-1, 0, prompt[:w-1], curses.A_BOLD)
        except curses.error:
            pass

        stdscr.move(h-1, min(len(prompt), w-1))
        stdscr.refresh()

    def log(msg):
        for line in msg.split("\n"):
            log_lines.append(line)

    draw()

    input_buf = ""
    while True:
        draw(input_buf)
        try:
            ch = stdscr.get_wch()
        except curses.error:
            continue

        if ch in (curses.KEY_BACKSPACE, "\x7f", "\b"):
            input_buf = input_buf[:-1]
        elif ch in ("\n", "\r", curses.KEY_ENTER):
            raw = input_buf.strip()
            input_buf = ""
            if not raw:
                continue

            log(f"audition> {raw}")
            parts = raw.split()
            cmd = parts[0].lower()

            if cmd == "q":
                report = get_report()
                for line in report:
                    log(line)
                draw()
                send("hush")
                resume_evolve()
                time.sleep(1)
                return
            elif cmd == "list":
                log("  Banks:")
                for b, (kind, _) in ALL_BANKS.items():
                    playing = "  ▶" if b in active else ""
                    log(f"    {b:<16} ({kind}){playing}")
            elif cmd == "play" and len(parts) >= 2:
                log("  " + cmd_play(parts[1]))
            elif cmd == "stop" and len(parts) >= 2:
                log("  " + cmd_stop(" ".join(parts[1:])))
            elif cmd == "gain" and len(parts) >= 3:
                log("  " + cmd_gain(parts[1], parts[2]))
            elif cmd in ("+", "-"):
                log("  " + cmd_nudge(cmd))
            elif cmd == "r":
                for bank, info in active.items():
                    kind, slices = ALL_BANKS[bank]
                    play_bank(bank, kind, slices, info["gain"])
                log("  replaying all")
            elif cmd == "report":
                for line in get_report():
                    log(line)
            else:
                log(f"  ? unknown command '{raw}'")
        elif isinstance(ch, str) and ch.isprintable():
            input_buf += ch

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    finally:
        send("hush")
        resume_evolve()
