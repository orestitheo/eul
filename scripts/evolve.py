#!/usr/bin/env python3
"""
eul — self-evolving pattern composer
Runs on the server. Every N minutes, generates a new set of TidalCycles
pattern lines and sends them to the live REPL via tmux.

Rules:
  - Drone always on (d1)
  - Texture cycles in/out independently
  - Drums and chords never overlap (whenmod windows are complementary)
  - Voice only appears during chord sections, never over drums
  - Tempo stays between 0.5-1.2 cps
  - No crush/bitcrush effects (removed — sounded bad)
  - Glitch is optional — coin flip each session
  - Each session picks a MODE that biases what's prominent
"""

import random
import subprocess
import time
import sys

TMUX_SESSION = "eul"
TMUX_WINDOW = "5"
INTERVAL_MINUTES = 6  # how often to evolve

DRUM_BANKS = {
    "dungeondrums": 14,
    "rad": 37,
    "shxc1": 15,
}
CHORD_SAMPLES = (
    [f"ls:{i}" for i in range(9)] +
    [f"akatosh:{i}" for i in range(2)] +
    [f"shxc:{i}" for i in range(1)] +
    ["blackmirror:0", "discoveryone:0"]
)
VOICE_SAMPLES = ["madonna:0", "discoveryone:0", "akatosh:0"]

# Modes bias which layers are prominent this session
MODES = ["drums", "chords", "drone", "glitch", "balanced"]

def send(line):
    """Send a line to the TidalCycles REPL."""
    subprocess.run([
        "tmux", "send-keys", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}",
        line, "Enter"
    ])
    time.sleep(0.4)

def pick_tempo(mode):
    lo = round(random.uniform(0.5, 0.8), 2)
    hi = round(random.uniform(lo + 0.2, 1.2), 2)
    # Drums mode runs faster, drone mode slower
    if mode == "drums":
        lo = round(random.uniform(0.7, 1.0), 2)
        hi = round(random.uniform(lo + 0.1, 1.4), 2)
    elif mode == "drone":
        lo = round(random.uniform(0.4, 0.6), 2)
        hi = round(random.uniform(lo + 0.1, 0.8), 2)
    slow_factor = random.choice([16, 24, 32, 48])
    return f"cps (slow {slow_factor} $ range {lo} {hi} perlin)"

def pick_drone(mode):
    lpf_lo = random.randint(200, 500)
    lpf_hi = random.randint(800, 2500)
    slow_factor = random.choice([8, 12, 16, 24])
    room = round(random.uniform(0.7, 1.0), 1)
    # Drone mode: louder and more present
    gain = round(random.uniform(0.7, 1.0), 1) if mode == "drone" else round(random.uniform(0.4, 0.7), 1)
    return (
        f'd1 $ sound "drone:0"'
        f' # gain {gain}'
        f' # lpf (slow {slow_factor} $ range {lpf_lo} {lpf_hi} perlin)'
        f' # room {room}'
    )

def pick_texture(mode):
    on = random.choice([3, 4, 5, 6])
    total = on + random.choice([1, 2, 3])
    slow_factor = random.choice([2, 3])
    gain = round(random.uniform(0.4, 0.7), 1)
    # Drone/glitch mode: texture more present
    if mode in ("drone", "glitch"):
        on = random.choice([4, 5, 6])
        total = on + random.choice([1, 2])
        gain = round(random.uniform(0.5, 0.8), 1)
    return (
        f'd2 $ whenmod {total} {on} id'
        f' $ every {random.randint(4,7)} (jux rev)'
        f' $ slow {slow_factor} $ sound "texture:0 texture:1 texture:2"'
        f' # gain {gain}'
        f' # speed (rand + {round(random.uniform(0.3, 0.7), 1)})'
        f' # room {round(random.uniform(0.5, 0.9), 1)}'
    )

def pick_t99(mode, chord_on, total):
    # Coin flip — more likely in chords/drone mode
    if mode not in ("chords", "drone", "balanced") and random.random() < 0.5:
        return "d3 silence"
    # Play seconds and fifths: notes 0, 2, 7 in a slow sequence
    notes = random.choice([
        "0 2 7 2",
        "0 7 2 7",
        "0 2 0 7",
        "7 0 2 0",
    ])
    slow_factor = random.choice([3, 4, 6])
    gain = round(random.uniform(0.6, 1.0), 1)
    return (
        f'd3 $ whenmod {total} {chord_on} id'
        f' $ slow {slow_factor} $ sound "t99:0"'
        f' # note "{notes}"'
        f' # gain {gain}'
        f' # room {round(random.uniform(0.7, 0.95), 2)}'
        f' # delay 0.5 # delaytime {random.choice([0.375, 0.5])} # delayfeedback 0.4'
        f' # pan (slow {random.randint(6,12)} $ range 0.2 0.8 sine)'
    )

def pick_drums_and_chords(mode):
    """
    Returns (drums_line, chords_line, voice_line).
    Mode biases how long drums vs chords sections are.
    They never overlap.
    """
    total = random.choice([6, 8, 10, 12])

    if mode == "drums":
        drum_frac = random.uniform(0.65, 0.85)
    elif mode == "chords":
        drum_frac = random.uniform(0.2, 0.45)
    elif mode == "drone":
        # Both quieter / shorter, drone dominates
        drum_frac = random.uniform(0.4, 0.6)
    else:
        drum_frac = random.uniform(0.4, 0.65)

    drum_on = max(2, int(total * drum_frac))
    chord_on = total - drum_on

    drum_bank = random.choice(list(DRUM_BANKS.keys()))
    max_slices = DRUM_BANKS[drum_bank]
    slices = [random.randint(0, max_slices - 1) for _ in range(8)]
    drum_seq = " ".join(f"{drum_bank}:{i}" for i in slices)

    drum_gain = round(random.uniform(0.7, 1.0) if mode == "drums" else random.uniform(0.5, 0.8), 1)
    drum_every_rev = random.randint(3, 6)
    drum_every_fast = random.randint(6, 10)
    dt = random.choice([0.25, 0.375, 0.5])
    delay_str = f' # delay (sometimes (const 0.5) 0) # delaytime (slow 3 $ range {dt} {round(dt*1.5, 3)} sine) # delayfeedback 0.35 # pan (slow 5 $ range 0.1 0.9 sine)'
    flanger_str = ' # shape 0.4 # coarse (sometimes (const 2) 1)' if random.random() < 0.3 else ""

    drums = (
        f'd4 $ whenmod {total} {drum_on} id'
        f' $ every {drum_every_rev} rev'
        f' $ every {drum_every_fast} (fast 2)'
        f' $ sound "{drum_seq}"'
        f' # gain {drum_gain}'
        f' # speed (range 0.8 1.2 rand)'
        f' # pan (range 0.3 0.7 rand)'
        f'{delay_str}'
        f'{flanger_str}'
    )

    num_chords = random.randint(3, 6)
    chord_picks = random.sample(CHORD_SAMPLES, num_chords)
    chord_list = ", ".join(f'"{c}"' for c in chord_picks)
    chord_slow = random.choice([2, 3])
    chord_gain = round(random.uniform(2.4, 3.2) if mode == "chords" else random.uniform(2.0, 2.8), 1)
    chord_room = round(random.uniform(0.6, 0.9), 1)
    chord_hpf = random.randint(150, 300)
    pan_slow = random.randint(4, 10)

    chords = (
        f'd6 $ whenmod {total} {chord_on} id'
        f' $ every {random.randint(3,6)} (jux rev)'
        f' $ slow {chord_slow} $ sound (choose [{chord_list}])'
        f' # gain {chord_gain}'
        f' # hpf {chord_hpf}'
        f' # room {chord_room}'
        f' # pan (slow {pan_slow} $ range 0.2 0.8 sine)'
    )

    # Voice — only during chord window
    # More likely in chords/drone mode
    voice_prob = 0.7 if mode in ("chords", "drone") else 0.4
    if random.random() < voice_prob:
        voice_slow = random.choice([4, 6, 8])
        voice_sample = random.choice(VOICE_SAMPLES)
        voice = (
            f'd5 $ whenmod {total} {chord_on} id'
            f' $ slow {voice_slow} $ sound "{voice_sample}"'
            f' # gain {round(random.uniform(0.5, 0.7), 1)}'
            f' # room {round(random.uniform(0.85, 1.0), 2)}'
            f' # note -2'
            f' # delay 0.7 # delaytime {random.choice([0.375, 0.5, 0.75])} # delayfeedback 0.5'
            f' # pan (slow {random.randint(8,16)} $ range 0.2 0.8 sine)'
        )
    else:
        voice = "d5 silence"

    return drums, chords, voice, chord_on, total

def evolve():
    mode = random.choice(MODES)
    print(f"Evolving patterns... [mode: {mode}]")
    drums, chords, voice, chord_on, total = pick_drums_and_chords(mode)
    lines = [
        pick_tempo(mode),
        pick_drone(mode),
        pick_texture(mode),
        pick_t99(mode, chord_on, total),
    ]
    lines += [drums, chords, voice]

    for line in lines:
        print(f"  > {line[:80]}...")
        send(line)

    print("Done.")

if __name__ == "__main__":
    if "--once" in sys.argv:
        evolve()
    else:
        print(f"eul evolve: running every {INTERVAL_MINUTES} minutes. Ctrl+C to stop.")
        evolve()  # run immediately on start
        while True:
            time.sleep(INTERVAL_MINUTES * 60)
            evolve()
