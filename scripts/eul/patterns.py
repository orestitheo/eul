"""
patterns.py — TidalCycles pattern builders driven by genome objects.

Each function takes genome domain instances and returns a TidalCycles pattern string.
Sample bank constants and interval libraries live here.
Transform backbone is built via grammar.py.
"""

import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import grammar
from banks import DRUM_BANKS, CHORD_SAMPLES, CHORD_LOOPING, _CHORD_WEIGHTS, VOICE_SAMPLES

# ── Interval libraries ─────────────────────────────────────────────────────────

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

# ── Helpers ────────────────────────────────────────────────────────────────────

def _euclidean_hits(density_gene, steps=8):
    return max(1, round(density_gene * steps))


def _drum_seq(bank, slices, max_slices, rest_prob, slice_bias):
    """Build a drum sequence of `slices` steps from `bank`."""
    parts = []
    for _ in range(slices):
        if random.random() < rest_prob:
            parts.append("~")
        else:
            center = round(slice_bias * (max_slices - 1))
            spread = max(1, max_slices // 3)
            idx    = int(random.gauss(center, spread))
            idx    = max(0, min(max_slices - 1, idx))
            parts.append(f"{bank}:{idx}")
    if all(p == "~" for p in parts):
        parts[0] = f"{bank}:0"
    return " ".join(parts)


# ── Pattern builders ───────────────────────────────────────────────────────────

def tempo(glob):
    """Global tempo pattern. glob: GlobalGenome."""
    center = glob.map("tempo_center", 0.4, 1.2)
    rng    = glob.map("tempo_range", 0.05, 0.5)
    lo     = round(max(0.3, center - rng / 2), 2)
    hi     = round(min(1.6, center + rng / 2), 2)
    slow_f = glob.map("tempo_drift_speed", 16, 48, integer=True)
    return f"cps (slow {slow_f} $ range {lo} {hi} perlin)"


def drone(drn):
    """Always-on foundation. drn: DroneGenome."""
    gain    = drn.map("gain", 0.4, 1.0)
    lpf_lo  = drn.map("lpf_lo", 100, 600, integer=True)
    lpf_hi  = drn.map("lpf_hi", 600, 3000, integer=True)
    slow_f  = drn.map("lpf_speed", 8, 24, integer=True)
    room    = drn.map("room", 0.5, 1.0)
    pitch   = drn.map("pitch", -7, 7, integer=True)
    begin   = drn.map("begin", 0.0, 0.6)
    sample  = random.randint(0, 2)
    pitch_str = f" # note ({pitch})" if pitch != 0 else ""
    # Occasionally gate the drone — on for 3-8 cycles, off for 1-4
    if random.random() < 0.4:
        on    = random.randint(3, 8)
        total = on + random.randint(1, 4)
        gate  = f"whenmod {total} {on} id $ "
    else:
        gate = ""
    return (
        f'd1 $ {gate}sound "drone:{sample}"'
        f' # begin {begin}'
        f' # gain {gain}'
        f' # lpf (slow {slow_f} $ range {lpf_lo} {lpf_hi} perlin)'
        f' # room {room}'
        f'{pitch_str}'
    )


def texture(tex, glob):
    """Atmospheric layer. tex: TextureGenome, glob: GlobalGenome."""
    density   = tex.get("density")
    on        = max(2, round(density * 7))
    total     = on + random.randint(1, 3)
    slow_f    = tex.map("slow", 1, 4, integer=True)
    gain      = tex.map("gain", 0.3, 0.9)
    spd_rand  = tex.map("speed_rand", 0.1, 1.0)
    room      = tex.map("room", 0.0, 1.0)
    # Sample bias: lean toward a region of the texture bank
    bias      = tex.get("sample_bias")
    center    = round(bias * 4)
    picks     = sorted(set([
        max(0, min(4, round(random.gauss(center, 1.5))))
        for _ in range(random.choice([1, 1, 2]))
    ]))
    tex_seq   = " ".join(f"texture:{i}" for i in picks)
    chaos     = glob.get("randomness")
    jux_int   = max(3, round(3 + (1 - chaos) * 5))
    begin     = round(random.uniform(0.0, 0.7), 2)
    return (
        f'd2 $ whenmod {total} {on} id'
        f' $ every {jux_int} (jux rev)'
        f' $ slow {slow_f} $ sound "{tex_seq}"'
        f' # begin {begin}'
        f' # gain {gain}'
        f' # speed (slow 8 $ range {round(1.0 - spd_rand * 0.5, 2)} {round(1.0 + spd_rand * 0.5, 2)} perlin)'
        f' # room {room}'
    )


def melodic(mel, chord_on, total):
    """
    T99 melodic layer (d3). mel: MelodicGenome.

    Builds a rhythmically and timbrally varied pattern from a single sample.
    Genes control: rhythm density, pitch/speed drift, sample slicing, layering.
    """
    slow_f     = mel.map("t99_slow", 2, 5, integer=True)
    gain       = mel.map("t99_gain", 0.5, 1.0)
    idx        = mel.map("t99_interval", 0, len(MELODIC_INTERVALS) - 1, integer=True)
    notes      = MELODIC_INTERVALS[idx]
    room       = mel.map("chord_room", 0.7, 1.0)
    dt         = random.choice([0.375, 0.5])
    pan_spd    = random.randint(6, 16)
    begin      = mel.map("t99_begin", 0.0, 0.7)

    # Rhythm — build a sequence with rests driven by t99_rhythm gene
    # 0=one hit (original feel), 0.5=scattered, 1=dense stutter
    rhythm     = mel.get("t99_rhythm")
    if rhythm < 0.15:
        # Original: single hit, no rhythm sequence
        seq = "t99:0"
    else:
        steps = 8
        hits  = max(1, round(rhythm * steps))
        # Euclidean-style: spread hits evenly then add rests
        positions = set(round(i * steps / hits) % steps for i in range(hits))
        seq = " ".join("t99:0" if i in positions else "~" for i in range(steps))

    # Speed/pitch — perlin-modulated drift around a center
    spd_center = mel.map("t99_speed", 0.4, 1.8)
    spd_rand   = mel.map("t99_speed_rand", 0.05, 0.6)
    spd_lo     = round(max(0.2, spd_center - spd_rand), 2)
    spd_hi     = round(min(2.5, spd_center + spd_rand), 2)
    spd_slow   = random.randint(4, 12)   # how slowly pitch drifts
    speed_str  = f'(slow {spd_slow} $ range {spd_lo} {spd_hi} perlin)'

    # Chop — slice sample into N fragments and sequence them
    chop       = mel.get("t99_chop")
    chop_n     = round(chop * 7) + 1   # maps to 1-8, 1=no chop
    chop_str   = f' # unit "c" # speed {chop_n}' if chop_n > 1 else ""
    # unit "c" in SuperDirt plays sample at original pitch regardless of speed,
    # so we use it only for pure chop — otherwise use perlin pitch modulation
    if chop_n > 1:
        speed_param = f' # unit "c" # speed {chop_n}'
        pitch_param = f' # note "{notes}"'
    else:
        speed_param = f' # speed {speed_str}'
        pitch_param = f' # note "{notes}"'

    # Layer — optionally stack a second voice at different speed/octave
    layer      = mel.get("t99_layer")
    layer_str  = ""
    if layer > 0.5:
        layer_spd  = round(spd_center * random.choice([0.5, 0.75, 1.5, 2.0]), 2)
        layer_spd  = max(0.2, min(2.5, layer_spd))
        layer_note = random.choice(["-12", "-7", "0", "7", "12"])
        layer_str  = f', slow {slow_f * 2} $ sound "t99:0" # speed {layer_spd} # note "{layer_note}" # gain {round(gain * 0.5, 2)} # room {room} # pan (slow {pan_spd + 4} $ range 0.6 0.9 sine)'

    core = (
        f'slow {slow_f} $ sound "{seq}"'
        f' # begin {begin}'
        f' # legato 1'
        f'{speed_param}'
        f'{pitch_param}'
        f' # gain {gain}'
        f' # room {room}'
        f' # delay 0.5 # delaytime {dt} # delayfeedback 0.4'
        f' # pan (slow {pan_spd} $ range 0.1 0.9 sine)'
    )

    if layer_str:
        sound_expr = f'stack [{core}{layer_str}]'
    else:
        sound_expr = core

    return (
        f'd3 $ whenmod {total} {chord_on} id'
        f' $ {sound_expr}'
    )


def drums(perc, glob):
    """Percussion layer (d4). perc: PercussiveGenome, glob: GlobalGenome."""
    total      = perc.map("cycle_len", 6, 12, integer=True)
    drum_frac  = perc.get("window_frac")
    drum_on    = max(2, round(total * drum_frac))
    rest_prob  = perc.get("rest_prob")
    slice_bias = perc.get("slice_bias")
    chaos      = perc.get("chaos")
    complexity = glob.get("complexity")
    drum_spd   = perc.get("speed")
    poly       = perc.get("polyrhythm")
    gain       = round(random.uniform(0.8, 0.9), 1)

    # Bank position drifts continuously across the spectrum [0, len(DRUM_BANKS)-1].
    # Integer part = left bank, fractional part = crossfade amount toward right bank.
    # e.g. pos=0.7 → 30% rad, 70% shxc1. The transition is a genetic journey.
    bank_pos  = perc.get("bank_pos") * (len(DRUM_BANKS) - 1)   # scale to bank count
    left_idx  = int(bank_pos)
    right_idx = min(left_idx + 1, len(DRUM_BANKS) - 1)
    mix       = bank_pos - left_idx   # 0.0 = fully left, 1.0 = fully right

    bank_a      = DRUM_BANKS[left_idx]
    bank_b      = DRUM_BANKS[right_idx]
    slices_a    = _drum_bank_slices(bank_a)
    slices_b    = _drum_bank_slices(bank_b)

    steps = []
    for _ in range(8):
        if random.random() < rest_prob:
            steps.append("~")
        elif random.random() < mix:
            idx = max(0, min(slices_b - 1, round(random.gauss(slice_bias * (slices_b - 1), slices_b // 3))))
            steps.append(f"{bank_b}:{idx}")
        else:
            idx = max(0, min(slices_a - 1, round(random.gauss(slice_bias * (slices_a - 1), slices_a // 3))))
            steps.append(f"{bank_a}:{idx}")
    if all(s == "~" for s in steps):
        steps[0] = f"{bank_a}:0"
    seq = " ".join(steps)

    # Gene-driven backbone transforms
    transforms = grammar.pick_transforms(chaos, complexity, pool="drums")
    sound_expr = f'sound "{seq}"'

    # Speed wrapping
    if drum_spd < 0.33:
        sound_expr = f"slow 2 $ {sound_expr}"
    elif drum_spd > 0.66:
        sound_expr = f"fast 2 $ {sound_expr}"

    # Polyrhythm layer
    if poly > 0.5:
        seq2 = _drum_seq(bank_a, 5, slices_a, rest_prob, slice_bias)
        sound_expr = f'stack [{sound_expr}, slow 1.5 $ sound "{seq2}"]'

    backbone = grammar.wrap_pattern(sound_expr, transforms)
    dt = random.choice([0.25, 0.375, 0.5])

    return (
        f'd4 $ whenmod {total} {drum_on} id'
        f' $ {backbone}'
        f' # gain {gain}'
        f' # room 0'
        f' # speed (slow 6 $ range 0.85 1.15 perlin)'
        f' # pan (range 0.3 0.7 rand)'
        f' # delay (sometimes (const 0.5) 0)'
        f' # delaytime (slow 3 $ range {dt} {round(dt*1.5, 3)} sine)'
        f' # delayfeedback 0.35'
    )


def chords(mel, chord_on, total, glob):
    """Chord layer (d6). mel: MelodicGenome, glob: GlobalGenome."""
    from banks import CHORD_BANKS

    # Exclusive: pick ONE bank per evolve, weighted by bank weight (not sample count)
    bank_names  = list(CHORD_BANKS.keys())
    bank_weights = [CHORD_BANKS[b].weight for b in bank_names]
    bank_name   = random.choices(bank_names, weights=bank_weights, k=1)[0]
    bank        = CHORD_BANKS[bank_name]
    is_looping  = bank.looping

    # Pick samples only from the chosen bank
    num_picks  = min(random.randint(2, 4), len(bank.samples))
    picks      = [f"{bank_name}:{i}" for i in random.choices(bank.samples, k=num_picks)]
    chord_list = ", ".join(f'"{c}"' for c in picks)

    slow_f    = mel.map("chord_slow", 1, 4, integer=True)
    gain      = mel.map("chord_gain", 0.4, 1.0)
    hpf       = random.randint(100, 300)
    pan_slow  = random.randint(4, 10)
    room      = mel.map("chord_room", 0.0, 1.0)
    loop_at   = mel.map("chord_loop_len", 1, 8, integer=True)
    staccato  = mel.map("chord_staccato", 0.05, 0.5)
    delay_wet = mel.map("chord_delay_wet", 0.0, 1.0)
    chaos     = glob.get("randomness")
    begin     = round(random.uniform(0.0, 0.7), 2)

    # Long pads: sustain holds the sample for N seconds regardless of cycle length.
    # loopAt silences long samples at certain tempos — sustain is the safe alternative.
    if is_looping:
        sustain = random.randint(8, 16)
        loop_prefix = ''
        style_str = f' # begin {begin} # sustain {sustain} # legato 1'
    elif chaos > 0.65:
        end = round(begin + random.uniform(0.1, 0.4), 2)
        loop_prefix = ''
        style_str = f' # begin {begin} # end {min(end, 0.99)} # legato 1'
    elif staccato < 0.15:
        loop_prefix = ''
        style_str = f' # begin {begin} # legato {staccato} # cut 1'
    else:
        loop_prefix = ''
        style_str = f' # begin {begin} # legato 1'

    delay_str = (
        f' # delay {round(delay_wet, 2)}'
        f' # delaytime {random.choice([0.25, 0.375, 0.5, 0.75])}'
        f' # delayfeedback {round(random.uniform(0.2, 0.5), 1)}'
    ) if delay_wet > 0.2 else ""

    # Gene-driven backbone transforms (tame chord pool)
    transforms = grammar.pick_transforms(chaos, glob.get("complexity"), pool="chords")
    sound_expr = f'{loop_prefix}slow {slow_f} $ sound (choose [{chord_list}])'
    backbone   = grammar.wrap_pattern(sound_expr, transforms)

    return (
        f'd6 $ whenmod {total} {chord_on} id'
        f' $ {backbone}'
        f'{style_str}'
        f' # gain {gain}'
        f' # hpf {hpf}'
        f' # room {room}'
        f'{delay_str}'
        f' # pan (slow {pan_slow} $ range 0.2 0.8 sine)'
    )


def voice(mel, chord_on, total):
    """Voice layer (d5). mel: MelodicGenome."""
    sample  = random.choice(VOICE_SAMPLES)
    slow_f  = mel.map("voice_slow", 3, 6, integer=True)
    gain    = mel.map("voice_gain", 0.3, 0.7)
    stretch = mel.map("voice_stretch", 0.4, 1.0)
    room    = mel.map("voice_room", 0.6, 1.0)
    idx     = mel.map("voice_interval", 0, len(VOICE_INTERVALS) - 1, integer=True)
    notes   = VOICE_INTERVALS[idx % len(VOICE_INTERVALS)]
    dt      = random.choice([0.375, 0.5, 0.75])
    pan_spd = random.randint(8, 16)
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


def _drum_bank_slices(bank_name: str) -> int:
    from banks import BANKS
    return BANKS[bank_name].slices
