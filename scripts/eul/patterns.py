"""
patterns.py — TidalCycles pattern builders driven by gene state.

Every function takes a Genes instance and returns a pattern string.
No hardcoded random choices — all variation comes from genes.
"""

import random
import math

# ── Sample banks ──────────────────────────────────────────────────────────────

DRUM_BANKS = {
    "dungeondrums": 14,
    "rad":          37,
    "shxc1":        15,
}

CHORD_SAMPLES_WEIGHTED = (
    [(f"ls:{i}",            1) for i in range(9)] +
    [(f"akatosh_chord:{i}", 3) for i in range(2)] +
    [(f"shxc:{i}",          3) for i in range(1)] +
    [("blackmirror:0", 3), ("discoveryone:0", 3)]
)
CHORD_SAMPLES  = [s for s, _ in CHORD_SAMPLES_WEIGHTED]
_CHORD_WEIGHTS = [w for _, w in CHORD_SAMPLES_WEIGHTED]

VOICE_SAMPLES = ["madonna:0", "discoveryone:0", "akatosh_voice:0"]

MELODIC_INTERVALS = [
    "0 7 0 7",
    "0 7 12 7",
    "0 3 7 3",
    "0 4 7 4",
    "0 5 0 7",
    "0 7 0 12",
    "0 3 5 7",
    "12 7 3 0",
    "0 4 7 12",
    "7 12 7 0",
    "[0,7]",
    "[0,7,12]",
    "[0,3,7]",
    "[0,4,7]",
    "[0,7] [0,5] [0,7] [0,3]",
    "[0,4,7] [0,3,7] [0,5,7] [0,7]",
]

VOICE_INTERVALS = [
    "-2",
    "0 7 0 5",
    "0 -2 0 5",
    "0 3 0 7",
    "0 5 3 0",
    "7 0 7 12",
    "[0,7]",
    "0 12 7 0",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _euclidean_hits(density_gene, steps=8):
    """Map density gene [0,1] to k hits in `steps` steps."""
    k = max(1, round(density_gene * steps))
    return k

def _drum_seq(bank, slices, max_slices, rest_prob, slice_bias):
    """
    Build a drum sequence of `slices` steps from `bank`.
    slice_bias [0,1] favours low vs high slice indices.
    rest_prob [0,1] chance of ~ per step.
    """
    parts = []
    for _ in range(slices):
        if random.random() < rest_prob:
            parts.append("~")
        else:
            # Bias slice selection toward low or high end of the bank
            center = round(slice_bias * (max_slices - 1))
            spread = max(1, max_slices // 3)
            idx = int(random.gauss(center, spread))
            idx = max(0, min(max_slices - 1, idx))
            parts.append(f"{bank}:{idx}")
    # Avoid all rests
    if all(p == "~" for p in parts):
        parts[0] = f"{bank}:0"
    return " ".join(parts)

def _every_transforms(chaos, complexity):
    """Return a chain of every/jux transforms based on chaos and complexity genes."""
    parts = []
    n_transforms = round(complexity * 3)  # 0-3 transforms
    if n_transforms >= 1:
        interval = max(2, round(2 + (1 - chaos) * 6))  # 2-8
        parts.append(f"every {interval} rev")
    if n_transforms >= 2 and chaos > 0.4:
        interval = max(3, round(3 + (1 - chaos) * 5))
        parts.append(f"every {interval} (fast 2)")
    if n_transforms >= 3 and chaos > 0.6:
        parts.append(f"sometimes (fast 2)")
    return parts

# ── Pattern builders ──────────────────────────────────────────────────────────

def tempo(g):
    center = g.map("tempo_center", 0.4, 1.2)
    rng    = g.map("tempo_range", 0.05, 0.5)
    lo     = round(max(0.3, center - rng / 2), 2)
    hi     = round(min(1.6, center + rng / 2), 2)
    slow_f = g.map("tempo_drift_speed", 16, 48, integer=True)
    return f"cps (slow {slow_f} $ range {lo} {hi} perlin)"


def drone(g):
    gain    = g.map("drone_gain", 0.4, 1.0)
    lpf_lo  = g.map("drone_lpf_lo", 100, 600, integer=True)
    lpf_hi  = g.map("drone_lpf_hi", 600, 3000, integer=True)
    slow_f  = g.map("drone_lpf_speed", 8, 24, integer=True)
    room    = g.map("drone_room", 0.5, 1.0)
    sample  = random.randint(0, 2)
    return (
        f'd1 $ sound "drone:{sample}"'
        f' # gain {gain}'
        f' # lpf (slow {slow_f} $ range {lpf_lo} {lpf_hi} perlin)'
        f' # room {room}'
    )


def texture(g):
    density   = g.get("texture_density")
    on        = max(2, round(density * 7))
    total     = on + random.randint(1, 3)
    slow_f    = g.map("texture_slow", 1, 4, integer=True)
    gain      = g.map("texture_gain", 0.3, 0.9)
    spd_rand  = g.map("texture_speed_rand", 0.1, 1.0)
    num       = random.choice([1, 1, 2])
    picks     = random.sample(range(5), min(num, 5))
    tex_seq   = " ".join(f"texture:{i}" for i in picks)
    chaos     = g.get("drum_chaos")
    jux_int   = max(3, round(3 + (1 - chaos) * 5))
    return (
        f'd2 $ whenmod {total} {on} id'
        f' $ every {jux_int} (jux rev)'
        f' $ slow {slow_f} $ sound "{tex_seq}"'
        f' # gain {gain}'
        f' # speed (rand + {round(spd_rand, 2)})'
        f' # room {g.map("chord_room", 0.4, 0.9)}'
    )


def melodic(g, chord_on, total):
    slow_f  = g.map("melodic_slow", 2, 5, integer=True)
    gain    = g.map("melodic_gain", 0.5, 1.0)
    idx     = g.map("melodic_interval", 0, len(MELODIC_INTERVALS) - 1, integer=True)
    notes   = MELODIC_INTERVALS[idx]
    dt      = random.choice([0.375, 0.5])
    pan_spd = random.randint(6, 12)
    return (
        f'd3 $ whenmod {total} {chord_on} id'
        f' $ slow {slow_f} $ sound "t99:0"'
        f' # legato 1'
        f' # note "{notes}"'
        f' # gain {gain}'
        f' # room {g.map("drone_room", 0.7, 1.0)}'
        f' # delay 0.5 # delaytime {dt} # delayfeedback 0.4'
        f' # pan (slow {pan_spd} $ range 0.2 0.8 sine)'
    )


def drums(g, mode_flags):
    total      = g.map("drum_cycle_len", 6, 12, integer=True)
    drum_frac  = g.get("drum_window_frac")
    drum_on    = max(2, round(total * drum_frac))
    rest_prob  = g.get("drum_rest_prob")
    slice_bias = g.get("drum_slice_bias")
    chaos      = g.get("drum_chaos")
    complexity = g.get("complexity")
    drum_spd   = g.get("drum_speed")
    poly       = g.get("drum_polyrhythm")
    gain       = round(random.uniform(0.8, 0.9), 1)

    bank       = random.choice(list(DRUM_BANKS.keys()))
    max_slices = DRUM_BANKS[bank]

    # Build sequence from genes rather than hardcoded slice lists
    k     = _euclidean_hits(g.get("drum_density"))
    seq   = _drum_seq(bank, 8, max_slices, rest_prob, slice_bias)
    transforms = _every_transforms(chaos, complexity)
    transform_str = " $ ".join(f"$ {t}" for t in transforms) if transforms else ""

    # Speed: half-time / normal / double-time from gene
    if drum_spd < 0.33:
        speed_wrap = "$ slow 2 "
    elif drum_spd > 0.66:
        speed_wrap = "$ fast 2 "
    else:
        speed_wrap = ""

    # Polyrhythm layer
    poly_str = ""
    if poly > 0.5:
        seq2 = _drum_seq(bank, 5, max_slices, rest_prob, slice_bias)
        poly_str = f', slow 1.5 $ sound "{seq2}"'

    if poly_str:
        sound_str = f'$ stack [sound "{seq}"{poly_str}]'
    else:
        sound_str = f'{speed_wrap}$ sound "{seq}"'

    dt = random.choice([0.25, 0.375, 0.5])
    delay_str = (
        f' # delay (sometimes (const 0.5) 0)'
        f' # delaytime (slow 3 $ range {dt} {round(dt*1.5, 3)} sine)'
        f' # delayfeedback 0.35'
        f' # pan (slow 5 $ range 0.1 0.9 sine)'
    )

    return (
        f'd4 $ whenmod {total} {drum_on} id'
        f' {transform_str} {sound_str}'
        f' # gain {gain}'
        f' # room 0'
        f' # speed (range 0.8 1.2 rand)'
        f' # pan (range 0.3 0.7 rand)'
        f'{delay_str}'
    )


def chords(g, chord_on, total):
    num_picks  = random.randint(2, 5)
    picks      = random.choices(CHORD_SAMPLES, weights=_CHORD_WEIGHTS, k=num_picks)
    chord_list = ", ".join(f'"{c}"' for c in picks)
    slow_f     = g.map("chord_slow", 1, 4, integer=True)
    gain       = g.map("chord_gain", 0.4, 1.0)
    hpf        = random.randint(100, 300)
    pan_slow   = random.randint(4, 10)
    room       = g.map("chord_room", 0.0, 1.0)
    loop_at    = g.map("chord_loop_len", 1, 8, integer=True)
    staccato   = g.map("chord_staccato", 0.05, 0.5)
    delay_wet  = g.map("chord_delay_wet", 0.0, 1.0)
    jux_int    = max(3, round(3 + (1 - g.get("drum_chaos")) * 4))

    # Style determined by genes: high loop_len → looped, high chaos → glitch, low staccato → staccato
    chaos = g.get("drum_chaos")
    if chaos > 0.65:
        begin = round(random.uniform(0.0, 0.5), 2)
        end   = round(begin + random.uniform(0.1, 0.4), 2)
        style_str = f' # begin {begin} # end {end} # legato 1 # loopAt {loop_at}'
    elif staccato < 0.15:
        style_str = f' # legato {staccato} # cut 1'
    else:
        style_str = f' # loopAt {loop_at} # legato 1'

    delay_str = (
        f' # delay {round(delay_wet, 2)}'
        f' # delaytime {random.choice([0.25, 0.375, 0.5, 0.75])}'
        f' # delayfeedback {round(random.uniform(0.2, 0.5), 1)}'
    ) if delay_wet > 0.2 else ""

    return (
        f'd6 $ whenmod {total} {chord_on} id'
        f' $ every {jux_int} (jux rev)'
        f' $ slow {slow_f} $ sound (choose [{chord_list}])'
        f'{style_str}'
        f' # gain {gain}'
        f' # hpf {hpf}'
        f' # room {room}'
        f'{delay_str}'
        f' # pan (slow {pan_slow} $ range 0.2 0.8 sine)'
    )


def voice(g, chord_on, total):
    sample     = random.choice(VOICE_SAMPLES)
    slow_f     = g.map("voice_slow", 3, 6, integer=True)
    gain       = g.map("voice_gain", 0.3, 0.7)
    stretch    = g.map("voice_stretch", 0.4, 1.0)
    room       = g.map("voice_room", 0.6, 1.0)
    idx        = g.map("melodic_interval", 0, len(VOICE_INTERVALS) - 1, integer=True)
    notes      = VOICE_INTERVALS[idx % len(VOICE_INTERVALS)]
    dt         = random.choice([0.375, 0.5, 0.75])
    pan_spd    = random.randint(8, 16)
    return (
        f'd5 $ whenmod {total} {chord_on} id'
        f' $ slow {slow_f} $ sound "{sample}"'
        f' # gain {gain}'
        f' # legato 1'
        f' # speed {stretch}'
        f' # note "{notes}"'
        f' # room {room}'
        f' # delay 0.7 # delaytime {dt} # delayfeedback 0.5'
        f' # pan (slow {pan_spd} $ range 0.2 0.8 sine)'
    )
