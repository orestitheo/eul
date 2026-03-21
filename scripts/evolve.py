#!/usr/bin/env python3
"""
eul — self-evolving pattern composer
Runs on the server. Every N minutes, generates a new set of TidalCycles
pattern lines and sends them to the live REPL via tmux.

Rules:
  - Always 2-3 active layers, never more
  - Drone always on (d1)
  - Texture cycles in/out independently
  - Drums and chords never overlap (whenmod windows are complementary)
  - Voice only appears during chord sections, never over drums
  - Tempo stays between 0.5-1.2 cps
  - No crush/bitcrush effects (removed — sounded bad)
  - Glitch is optional — coin flip each session
"""

import random
import subprocess
import time
import sys

TMUX_SESSION = "eul"
TMUX_WINDOW = "5"
INTERVAL_MINUTES = 30  # how often to evolve

DRUM_BANKS = {
    "dungeondrums": 14,
    "rad": 37,
    "shxc1": 15,
}
CHORD_SAMPLES = (
    [f"ls:{i}" for i in range(9)] +
    [f"akatosh:{i}" for i in range(2)] +
    ["blackmirror:0", "t99:0", "discoveryone:0"]
)
VOICE_SAMPLE = "discoveryone:0"  # the voice file
VOICE_SAMPLES = ["discoveryone:0", "akatosh:0"]  # all voice-like samples

def send(line):
    """Send a line to the TidalCycles REPL."""
    subprocess.run([
        "tmux", "send-keys", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}",
        line, "Enter"
    ])
    time.sleep(0.4)

def pick_tempo():
    # Smooth perlin drift, range chosen randomly but within sane bounds
    lo = round(random.uniform(0.5, 0.8), 2)
    hi = round(random.uniform(lo + 0.2, 1.2), 2)
    slow_factor = random.choice([16, 24, 32, 48])
    return f"cps (slow {slow_factor} $ range {lo} {hi} perlin)"

def pick_drone():
    lpf_lo = random.randint(200, 500)
    lpf_hi = random.randint(800, 2500)
    slow_factor = random.choice([8, 12, 16, 24])
    room = round(random.uniform(0.7, 1.0), 1)
    gain = round(random.uniform(0.5, 0.8), 1)
    return (
        f'd1 $ sound "drone:0"'
        f' # gain {gain}'
        f' # lpf (slow {slow_factor} $ range {lpf_lo} {lpf_hi} perlin)'
        f' # room {room}'
    )

def pick_texture():
    # whenmod: on for A cycles, off for B cycles
    on = random.choice([3, 4, 5, 6])
    total = on + random.choice([1, 2, 3])
    slow_factor = random.choice([2, 3])
    gain = round(random.uniform(0.4, 0.7), 1)
    return (
        f'd2 $ whenmod {total} {on} id'
        f' $ every {random.randint(4,7)} (jux rev)'
        f' $ slow {slow_factor} $ sound "texture:0 texture:1 texture:2"'
        f' # gain {gain}'
        f' # speed (rand + {round(random.uniform(0.3, 0.7), 1)})'
        f' # room {round(random.uniform(0.5, 0.9), 1)}'
    )

def pick_glitch():
    # Coin flip — sometimes glitch is off entirely
    if random.random() < 0.4:
        return "d3 silence"
    slices = random.sample(range(55), 4)
    slices_str = " ".join(f"glitch1:{i}" for i in sorted(slices))
    freq = random.choice(["rarely", "sometimes"])
    gain = round(random.uniform(0.4, 0.7), 1)
    return (
        f'd3 $ {freq} id'
        f' $ sound "{slices_str}"'
        f' # gain {gain}'
        f' # speed (rand + {round(random.uniform(0.2, 0.5), 1)})'
        f' # pan rand'
    )

def pick_drums_and_chords():
    """
    Returns (drums_line, chords_line, voice_line).
    Drums play for drum_on cycles, chords for chord_on cycles, total = drum_on + chord_on.
    They never overlap.
    """
    total = random.choice([16, 20, 24, 32])
    drum_on = int(total * random.uniform(0.5, 0.75))
    chord_on = total - drum_on

    drum_bank = random.choice(list(DRUM_BANKS.keys()))
    # Pick 8 random slices from the drum bank
    max_slices = DRUM_BANKS[drum_bank]
    slices = [random.randint(0, max_slices - 1) for _ in range(8)]
    drum_seq = " ".join(f"{drum_bank}:{i}" for i in slices)

    drum_gain = round(random.uniform(0.7, 1.0), 1)
    drum_every_rev = random.randint(3, 6)
    drum_every_fast = random.randint(6, 10)
    use_delay = random.random() < 0.5
    delay_str = (
        f' # delay (sometimes (const 0.5) 0) # delaytime {random.choice([0.25, 0.375, 0.5])} # delayfeedback 0.3'
        if use_delay else ""
    )

    drums = (
        f'd4 $ whenmod {total} {drum_on} id'
        f' $ every {drum_every_rev} rev'
        f' $ every {drum_every_fast} (fast 2)'
        f' $ sound "{drum_seq}"'
        f' # gain {drum_gain}'
        f' # speed (range 0.8 1.2 rand)'
        f' # pan (range 0.3 0.7 rand)'
        f'{delay_str}'
    )

    # Chords — pick random subset of ls samples
    num_chords = random.randint(3, 6)
    chord_picks = random.sample(CHORD_SAMPLES, num_chords)
    chord_list = ", ".join(f'"{c}"' for c in chord_picks)
    chord_slow = random.choice([2, 3])
    chord_gain = round(random.uniform(1.1, 1.6), 1)
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

    # Voice — only during chord window, coin flip
    if random.random() < 0.5:
        voice_slow = random.choice([4, 6, 8])
        voice_sample = random.choice(VOICE_SAMPLES)
        voice = (
            f'd5 $ whenmod {total} {chord_on} id'
            f' $ slow {voice_slow} $ sound "{voice_sample}"'
            f' # gain {round(random.uniform(0.5, 0.9), 1)}'
            f' # room 0.95'
            f' # delay 0.7 # delaytime {random.choice([0.375, 0.5, 0.75])} # delayfeedback 0.5'
            f' # pan (slow {random.randint(8,16)} $ range 0.2 0.8 sine)'
        )
    else:
        voice = "d5 silence"

    return drums, chords, voice

def evolve():
    print("Evolving patterns...")
    lines = [
        pick_tempo(),
        pick_drone(),
        pick_texture(),
        pick_glitch(),
    ]
    drums, chords, voice = pick_drums_and_chords()
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
