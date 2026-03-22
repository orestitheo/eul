"""
banks.py — sample bank registry using strain-based inheritance.

Strains define defaults. Banks are instances that override only what differs.
Pattern builders use by_strain() and Bank attributes — no hardcoded names.

Adding a new bank:   one line in BANKS
Adding a new strain: one class
Changing a rule for all chords: one line in Chord
"""


# ── Strains ────────────────────────────────────────────────────────────────────

class Strain:
    """Base strain. All banks inherit from this."""
    rules   = []      # list of rule tags, e.g. ["exclusive"]
    looping = False   # True: always loopAt + legato=1, never staccato/glitch
    weight  = 1       # relative selection weight within strain
    samples = [0]     # sample indices (e.g. [0,1,2] → bank:0, bank:1, bank:2)
    slices  = None    # for drum banks: total slice count

    def __init__(self, path, **overrides):
        self.path = path
        for k, v in overrides.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path!r})"


class Drone(Strain):
    """Always-on ambient foundation. One bank, always playing."""
    rules   = []
    looping = True
    samples = [0, 1, 2]


class Texture(Strain):
    """Atmospheric layer. Gates in/out. One bank at a time."""
    rules   = ["exclusive"]
    looping = True
    samples = list(range(5))


class Chord(Strain):
    """
    Harmonic/melodic chord layer. Exclusive — only one chord bank plays at a time.
    Looping by default (pad style). Individual banks can override looping=False
    to allow glitch/chop/staccato behaviour.
    """
    rules   = ["exclusive"]
    looping = True
    weight  = 2


class Voice(Strain):
    """Vocal/singletone layer. Exclusive — one voice at a time. Pitched."""
    rules   = ["exclusive"]
    looping = False
    weight  = 1


class Drum(Strain):
    """Percussive layer. Bank crossfade via bank_pos gene."""
    rules   = []
    looping = False
    weight  = 1


# ── Bank registry ──────────────────────────────────────────────────────────────
# One entry per bank. Only declare what differs from the strain default.

BANKS = {
    # Drone (d1)
    "drone":     Drone("drone", samples=[0, 1, 2]),

    # Texture (d2)
    "texture":   Texture("texture", samples=list(range(5))),

    # Chords (d6) + melodic instrument (d3)
    # All Chord strain → exclusive (one at a time), but looping is per-bank
    "ls":            Chord("melodic/chords/ls",           samples=list(range(9)), weight=1),
    "akatosh_chord": Chord("melodic/chords/akatosh_chord",samples=list(range(1)), weight=3),
    "blackmirror":   Chord("melodic/chords/blackmirror",  samples=[0],            weight=3),
    "discoveryone":  Chord("melodic/chords/discoveryone", samples=[0],            weight=3),
    "shxc":          Chord("melodic/chords/shxc",         samples=[0],            weight=3, looping=False),  # can glitch/chop
    "t99":           Chord("melodic/chords/t99",          samples=[0],            weight=2, looping=False),  # melodic instrument, pitched

    # Voice (d5)
    "madonna":           Voice("melodic/singletone/madonna",       samples=[0]),
    "akatosh_voice":     Voice("melodic/singletone/akatosh_voice", samples=[0]),
    "discoveryone_voice":Voice("melodic/singletone/discoveryone",  samples=[0]),

    # Drums (d4)
    # "dungeondrums": Drum("percussive/dungeondrums", slices=14),
    "rad":   Drum("percussive/rad",   slices=37),
    "shxc1": Drum("percussive/shxc1", slices=15),
}


# ── Convenience accessors ──────────────────────────────────────────────────────

def by_strain(strain_class):
    """Return {name: bank} for all banks of a given strain."""
    return {k: v for k, v in BANKS.items() if isinstance(v, strain_class)}


def has_rule(bank, rule: str) -> bool:
    return rule in bank.rules


# Pre-built views used by pattern builders
DRUM_BANKS   = list(by_strain(Drum).keys())   # ordered list for bank_pos gene
CHORD_BANKS  = by_strain(Chord)
VOICE_BANKS  = by_strain(Voice)
DRONE_BANKS  = by_strain(Drone)
TEXTURE_BANKS= by_strain(Texture)


# Weighted chord sample list for random selection
# [(name:idx, is_looping, weight), ...]
CHORD_SAMPLES_WEIGHTED = []
for _bname, _b in CHORD_BANKS.items():
    for _i in _b.samples:
        CHORD_SAMPLES_WEIGHTED.append((f"{_bname}:{_i}", _b.looping, _b.weight))

CHORD_SAMPLES  = [s for s, _, _ in CHORD_SAMPLES_WEIGHTED]
CHORD_LOOPING  = [l for _, l, _ in CHORD_SAMPLES_WEIGHTED]
_CHORD_WEIGHTS = [w for _, _, w in CHORD_SAMPLES_WEIGHTED]

VOICE_SAMPLES  = [f"{n}:0" for n in VOICE_BANKS]
