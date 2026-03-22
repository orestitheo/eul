"""
banks.py — single registry of all sample banks.

Adding a new bank or renaming a folder = one entry here, nothing else.
Pattern builders read from BANKS rather than hardcoding paths.

Fields:
  path     — relative path under samples/ (matches SuperDirt boot config)
  domain   — which genetic domain owns this bank
  looping  — True: always loopAt style + legato=1, never staccato/glitch
  weight   — relative selection weight for random bank picks
  slices   — number of slices in the bank (drum banks)
  samples  — explicit sample list (unused for drums; auto-derived for others)
"""

BANKS = {
    # Drone (d1)
    "drone": {
        "path":    "drone",
        "domain":  "drone",
        "samples": [0, 1, 2],   # drone:0, drone:1, drone:2
    },

    # Texture (d2)
    "texture": {
        "path":    "texture",
        "domain":  "texture",
        "samples": list(range(5)),   # texture:0..4
    },

    # Melodic — t99 (d3)
    "t99": {
        "path":    "melodic/chords/t99",
        "domain":  "melodic",
        "looping": False,
    },

    # Voice (d5)
    "madonna": {
        "path":    "melodic/singletone/madonna",
        "domain":  "melodic",
        "looping": False,
    },
    "akatosh_voice": {
        "path":    "melodic/singletone/akatosh_voice",
        "domain":  "melodic",
        "looping": False,
    },
    "discoveryone_voice": {
        "path":    "melodic/singletone/discoveryone",
        "domain":  "melodic",
        "looping": False,
    },

    # Chords (d6) — looping banks never go staccato or glitch
    "ls": {
        "path":    "melodic/chords/ls",
        "domain":  "melodic",
        "looping": True,
        "weight":  1,
        "samples": list(range(9)),
    },
    "akatosh_chord": {
        "path":    "melodic/chords/akatosh_chord",
        "domain":  "melodic",
        "looping": True,
        "weight":  3,
        "samples": list(range(2)),
    },
    "blackmirror": {
        "path":    "melodic/chords/blackmirror",
        "domain":  "melodic",
        "looping": True,
        "weight":  3,
        "samples": [0],
    },
    "discoveryone": {
        "path":    "melodic/chords/discoveryone",
        "domain":  "melodic",
        "looping": True,
        "weight":  3,
        "samples": [0],
    },
    "shxc": {
        "path":    "melodic/chords/shxc",
        "domain":  "melodic",
        "looping": False,
        "weight":  3,
        "samples": [0],
    },

    # Drums (d4)
    "dungeondrums": {
        "path":    "percussive/dungeondrums",
        "domain":  "percussive",
        "slices":  14,
    },
    "rad": {
        "path":    "percussive/rad",
        "domain":  "percussive",
        "slices":  37,
    },
    "shxc1": {
        "path":    "percussive/shxc1",
        "domain":  "percussive",
        "slices":  15,
    },
}

# Convenience: ordered list of drum banks (for bank_idx gene mapping)
DRUM_BANKS = [k for k, v in BANKS.items() if v.get("domain") == "percussive"]

# Convenience: chord bank entries with weights for weighted random selection
CHORD_BANK_NAMES = [k for k, v in BANKS.items() if v.get("domain") == "melodic" and "weight" in v]

# Build weighted chord sample list: [(sample_str, weight), ...]
CHORD_SAMPLES_WEIGHTED = []
for _bname in CHORD_BANK_NAMES:
    _b = BANKS[_bname]
    _w = _b["weight"]
    for _i in _b["samples"]:
        CHORD_SAMPLES_WEIGHTED.append((f"{_bname}:{_i}", _b.get("looping", False), _w))

CHORD_SAMPLES  = [s for s, _, _ in CHORD_SAMPLES_WEIGHTED]
CHORD_LOOPING  = [l for _, l, _ in CHORD_SAMPLES_WEIGHTED]
_CHORD_WEIGHTS = [w for _, _, w in CHORD_SAMPLES_WEIGHTED]

VOICE_SAMPLES = ["madonna:0", "discoveryone_voice:0", "akatosh_voice:0"]
