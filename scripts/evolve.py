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
# Each entry is (sample, weight). ls has many files but we don't want it to dominate.
CHORD_SAMPLES_WEIGHTED = (
    [(f"ls:{i}", 1) for i in range(9)] +
    [(f"akatosh_chord:{i}", 3) for i in range(2)] +
    [(f"shxc:{i}", 3) for i in range(1)] +
    [("blackmirror:0", 3), ("discoveryone:0", 3)]
)
CHORD_SAMPLES = [s for s, _ in CHORD_SAMPLES_WEIGHTED]
_CHORD_WEIGHTS = [w for _, w in CHORD_SAMPLES_WEIGHTED]
VOICE_SAMPLES = ["madonna:0", "discoveryone:0", "akatosh_voice:0"]

# Modes define the structural character of a session
# minimal:    drone + texture only — pure ambient, no rhythm
# sparse:     drone + texture + chords, no drums
# percussive: drone + drums only, no melody
# melodic:    drone + t99 + chords, no drums, voice optional
# full:       all layers
# balanced:   all layers, nothing dominant
# glitch:     chaotic drums + texture, fast/broken, minimal melody
MODES = ["minimal", "sparse", "percussive", "melodic", "full", "balanced", "glitch"]

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
    gain = round(random.uniform(0.8, 1.0), 1) if mode == "drone" else round(random.uniform(0.6, 0.8), 1)
    sample = random.randint(0, 2)
    return (
        f'd1 $ sound "drone:{sample}"'
        f' # gain {gain}'
        f' # lpf (slow {slow_factor} $ range {lpf_lo} {lpf_hi} perlin)'
        f' # room {room}'
    )

def pick_texture(mode):
    on = random.choice([3, 4, 5, 6])
    total = on + random.choice([1, 2, 3])
    slow_factor = random.choice([2, 3])
    gain = round(random.uniform(0.5, 0.7), 1)
    # Drone/glitch mode: texture more present
    if mode in ("drone", "glitch"):
        on = random.choice([4, 5, 6])
        total = on + random.choice([1, 2])
        gain = round(random.uniform(0.6, 0.8), 1)
    # Pick 1 or 2 texture samples randomly
    num = random.choice([1, 1, 2])
    picks = random.sample(range(5), num)
    tex_seq = " ".join(f"texture:{i}" for i in picks)
    return (
        f'd2 $ whenmod {total} {on} id'
        f' $ every {random.randint(4,7)} (jux rev)'
        f' $ slow {slow_factor} $ sound "{tex_seq}"'
        f' # gain {gain}'
        f' # speed (rand + {round(random.uniform(0.3, 0.7), 1)})'
        f' # room {round(random.uniform(0.5, 0.9), 1)}'
    )

def pick_t99(mode, chord_on, total):
    # Only in modes where melody makes sense
    if mode in ("minimal", "percussive", "glitch"):
        return "d3 silence"
    if mode in ("full", "balanced") and random.random() < 0.4:
        return "d3 silence"

    slow_factor = random.choice([2, 2, 3])
    gain = round(random.uniform(0.7, 0.9), 1)
    loop_at = random.choice([2, 4, 4, 8])

    # Melodic patterns using intervals (semitones)
    # Fifths=7, fourths=5, minor third=3, major third=4, octave=12
    melodic_patterns = [
        "0 7 0 7",        # root + fifth alternating
        "0 7 12 7",       # root fifth octave fifth
        "0 3 7 3",        # minor arpeggio
        "0 4 7 4",        # major arpeggio
        "0 5 0 7",        # fourth and fifth
        "0 7 0 12",       # root fifth octave
        "0 3 5 7",        # minor scale fragment
        "12 7 3 0",       # descending minor
        "0 4 7 12",       # major arpeggio ascending
        "7 12 7 0",       # fifth octave descent
    ]

    # Chord stacks — play multiple notes simultaneously using note patterns with chords
    chord_patterns = [
        "[0,7]",          # power chord (root+fifth)
        "[0,7,12]",       # root+fifth+octave
        "[0,3,7]",        # minor triad
        "[0,4,7]",        # major triad
        "[0,5,7]",        # sus4
        "[0,7] [0,5] [0,7] [0,3]",   # chord sequence
        "[0,4,7] [0,3,7] [0,5,7] [0,7]",  # chord progression
    ]

    style = random.choice(["melodic", "melodic", "chords", "slow_melody"])

    if style == "melodic":
        notes = random.choice(melodic_patterns)
        note_str = f' # note "{notes}"'
    elif style == "chords":
        notes = random.choice(chord_patterns)
        note_str = f' # note "{notes}"'
    elif style == "slow_melody":
        # Very slow, just 2 notes
        n1, n2 = random.choice([(0, 7), (0, 12), (7, 12), (0, 5), (3, 7)])
        notes = f"{n1} {n2}"
        slow_factor = random.choice([3, 4])
        note_str = f' # note "{notes}"'

    return (
        f'd3 $ whenmod {total} {chord_on} id'
        f' $ slow {slow_factor} $ sound "t99:0"'
        f' # legato 1'
        f'{note_str}'
        f' # gain {gain}'
        f' # room {round(random.uniform(0.7, 0.95), 2)}'
        f' # delay 0.5 # delaytime {random.choice([0.375, 0.5])} # delayfeedback 0.4'
        f' # pan (slow {random.randint(6,12)} $ range 0.2 0.8 sine)'
    )

def pick_drums_and_chords(mode):
    """
    Returns (drums_line, chords_line, voice_line, chord_on, total).
    Mode determines which layers are present and their structural balance.
    Drums and chords never overlap (complementary whenmod windows).
    """
    total = random.choice([6, 8, 10, 12])

    # Structural decisions per mode
    has_drums  = mode in ("percussive", "full", "balanced", "glitch")
    has_chords = mode in ("sparse", "melodic", "full", "balanced")
    # glitch: drums dominate, chords rare
    if mode == "glitch":
        has_chords = random.random() < 0.3

    if mode == "percussive":
        drum_frac = random.uniform(0.7, 0.9)
    elif mode == "sparse":
        drum_frac = 0.0  # no drums
    elif mode == "melodic":
        drum_frac = 0.0  # no drums
    elif mode == "glitch":
        drum_frac = random.uniform(0.7, 0.9)
    elif mode == "full":
        drum_frac = random.uniform(0.45, 0.65)
    else:  # balanced
        drum_frac = random.uniform(0.4, 0.6)

    drum_on  = max(2, int(total * drum_frac)) if has_drums else 0
    chord_on = total - drum_on if has_chords else 0

    drum_bank = random.choice(list(DRUM_BANKS.keys()))
    max_slices = DRUM_BANKS[drum_bank]
    slices = [random.randint(0, max_slices - 1) for _ in range(8)]
    drum_seq = " ".join(f"{drum_bank}:{i}" for i in slices)

    drum_gain = round(random.uniform(0.8, 0.9), 1)  # stable, narrow range
    drum_every_rev = random.randint(3, 6)
    dt = random.choice([0.25, 0.375, 0.5])
    delay_str = f' # delay (sometimes (const 0.5) 0) # delaytime (slow 3 $ range {dt} {round(dt*1.5, 3)} sine) # delayfeedback 0.35 # pan (slow 5 $ range 0.1 0.9 sine)'

    # Glitch mode forces chaotic drum style
    if mode == "glitch":
        drum_style = random.choice(["chaotic", "chaotic", "polyrhythm"])
    else:
        drum_style = random.choice(["straight", "straight", "halftime", "polyrhythm", "sparse", "chaotic"])

    if drum_style == "straight":
        # Normal 8-step sequence, occasional fast
        drum_every_fast = random.randint(6, 10)
        pattern_str = (
            f' $ every {drum_every_rev} rev'
            f' $ every {drum_every_fast} (fast 2)'
            f' $ sound "{drum_seq}"'
        )
    elif drum_style == "halftime":
        # Slow and heavy
        pattern_str = (
            f' $ every {drum_every_rev} rev'
            f' $ slow 2 $ sound "{drum_seq}"'
        )
    elif drum_style == "polyrhythm":
        # Two different sequences overlaid at different speeds
        slices2 = [random.randint(0, max_slices - 1) for _ in range(5)]
        seq2 = " ".join(f"{drum_bank}:{i}" for i in slices2)
        pattern_str = (
            f' $ every {drum_every_rev} rev'
            f' $ stack [sound "{drum_seq}", slow 1.5 $ sound "{seq2}"]'
        )
    elif drum_style == "sparse":
        # Lots of rests, unpredictable hits
        sparse_seq = " ".join(
            f"{drum_bank}:{random.randint(0, max_slices-1)}" if random.random() > 0.5 else "~"
            for _ in range(8)
        )
        pattern_str = (
            f' $ every {drum_every_rev} rev'
            f' $ sound "{sparse_seq}"'
        )
    elif drum_style == "chaotic":
        # Fast with random speed variations
        pattern_str = (
            f' $ every {random.randint(2,4)} rev'
            f' $ every {random.randint(3,5)} (fast {random.choice([2,3])})'
            f' $ sometimes (fast {random.choice([2,3])})'
            f' $ sound "{drum_seq}"'
        )

    if not has_drums:
        drums = "d4 silence"
    else:
        drums = (
            f'd4 $ whenmod {total} {drum_on} id'
            f'{pattern_str}'
            f' # gain {drum_gain}'
            f' # room 0'
            f' # speed (range 0.8 1.2 rand)'
            f' # pan (range 0.3 0.7 rand)'
            f'{delay_str}'
        )

    if not has_chords:
        chords = "d6 silence"
    else:
        num_chords = random.randint(3, 6)
        chord_picks = random.choices(CHORD_SAMPLES, weights=_CHORD_WEIGHTS, k=num_chords)
        chord_list = ", ".join(f'"{c}"' for c in chord_picks)
        chord_slow = random.choice([2, 3])
        chord_gain = round(random.uniform(0.6, 1.0), 1)
        chord_hpf = random.randint(150, 300)
        pan_slow = random.randint(4, 10)

        chord_style = random.choice(["looped", "looped", "looped", "staccato", "glitch", "reverse"])
        if chord_style == "looped":
            loop_at = random.choice([2, 4, 4, 8])
            style_str = f' # loopAt {loop_at} # legato 1'
        elif chord_style == "staccato":
            style_str = f' # legato {round(random.uniform(0.1, 0.4), 1)} # cut 1'
        elif chord_style == "glitch":
            begin = round(random.uniform(0.0, 0.5), 2)
            end = round(begin + random.uniform(0.1, 0.4), 2)
            style_str = f' # begin {begin} # end {end} # legato 1 # loopAt {random.choice([1,2,4])}'
        elif chord_style == "reverse":
            style_str = f' # loopAt {random.choice([2,4])} # legato 1 # speed -1'

        chord_delay = (
            f' # delay {round(random.uniform(0.3, 0.7), 1)}'
            f' # delaytime {random.choice([0.25, 0.375, 0.5, 0.75])}'
            f' # delayfeedback {round(random.uniform(0.2, 0.5), 1)}'
        ) if random.random() < 0.7 else ""
        chord_room = round(random.uniform(0.7, 1.0), 1) if random.random() < 0.6 else round(random.uniform(0.0, 0.3), 1)

        chords = (
            f'd6 $ whenmod {total} {chord_on} id'
            f' $ every {random.randint(3,6)} (jux rev)'
            f' $ slow {chord_slow} $ sound (choose [{chord_list}])'
            f'{style_str}'
            f' # gain {chord_gain}'
            f' # hpf {chord_hpf}'
            f' # room {chord_room}'
            f'{chord_delay}'
            f' # pan (slow {pan_slow} $ range 0.2 0.8 sine)'
        )

    # Voice — only when chords are present
    voice_prob = 0.6 if mode in ("melodic", "sparse") else 0.35
    if not has_chords:
        voice = "d5 silence"
    elif random.random() < voice_prob:
        voice_slow = random.choice([3, 4, 6])
        voice_sample = random.choice(VOICE_SAMPLES)
        # Stretch: slow speed stretches the sample without changing pitch
        stretch = round(random.uniform(0.5, 0.9), 2)
        # Interval patterns — fifths, half steps, octaves
        voice_notes = random.choice([
            "-2",               # slightly down (original behaviour)
            "0 7 0 5",          # root, fifth, root, fourth
            "0 -2 0 5",         # down a step, up a fourth
            "0 3 0 7",          # minor feel
            "0 5 3 0",          # descending
            "7 0 7 12",         # fifth and octave
            "[0,7]",            # power chord
            "0 12 7 0",         # octave leap
        ])
        voice = (
            f'd5 $ whenmod {total} {chord_on} id'
            f' $ slow {voice_slow} $ sound "{voice_sample}"'
            f' # gain {round(random.uniform(0.4, 0.6), 1)}'
            f' # legato 1'
            f' # speed {stretch}'
            f' # note "{voice_notes}"'
            f' # room {round(random.uniform(0.85, 1.0), 2)}'
            f' # delay 0.7 # delaytime {random.choice([0.375, 0.5, 0.75])} # delayfeedback 0.5'
            f' # pan (slow {random.randint(8,16)} $ range 0.2 0.8 sine)'
        )
    else:
        voice = "d5 silence"

    return drums, chords, voice, chord_on, total

def micro_evolve():
    """Small tweaks every 60s — nudge gains and filter sweeps without restructuring."""
    print("Micro-evolving...")
    # Drone: just tweak gain and filter range (don't change sample — full evolve handles that)
    lpf_lo = random.randint(200, 500)
    lpf_hi = random.randint(800, 2500)
    slow_factor = random.choice([8, 12, 16, 24])
    gain = round(random.uniform(0.5, 0.8), 1)
    send(f'd1 $ (# gain {gain}) $ (# lpf (slow {slow_factor} $ range {lpf_lo} {lpf_hi} perlin))')

    # Texture: nudge gain and speed
    gain = round(random.uniform(0.4, 0.7), 1)
    send(f'd2 $ (# gain {gain}) $ (# speed (rand + {round(random.uniform(0.3, 0.8), 1)}))')

    # Chords: nudge gain (keep in normalized range)
    chord_gain = round(random.uniform(0.6, 1.0), 1)
    send(f'd6 $ (# gain {chord_gain})')

    print("Micro-evolve done.")

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
    if "--micro" in sys.argv:
        micro_evolve()
    elif "--once" in sys.argv:
        evolve()
    else:
        print(f"eul evolve: running every {INTERVAL_MINUTES} minutes, micro-evolve every 60s. Ctrl+C to stop.")
        evolve()
        last_full = time.time()
        while True:
            time.sleep(60)
            if time.time() - last_full >= INTERVAL_MINUTES * 60:
                evolve()
                last_full = time.time()
            else:
                micro_evolve()
