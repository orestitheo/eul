"""
modes.py — mode attractors for the eul genetic composer.

Each mode defines partial gene targets per domain. During evolution,
the nearest mode exerts a gravitational pull — it drifts toward it,
never fully snaps. Modes also hard-gate which layers are active.

Gene targets use the same normalized [0,1] values as the genomes.
"""

MODES = {
    "minimal": {
        "drone":      {"gain": 0.9, "room": 0.9},
        "texture":    {"density": 0.8, "gain": 0.7},
        "percussive": {},
        "melodic":    {},
        "global":     {"complexity": 0.1, "randomness": 0.2, "tempo_center": 0.2},
        "has_drums":  False,
        "has_chords": False,
        "has_voice":  False,
        "has_t99":    False,
    },

    "sparse": {
        "drone":      {"gain": 0.8},
        "texture":    {"density": 0.5},
        "percussive": {},
        "melodic":    {"chord_slow": 0.8, "chord_room": 0.9, "chord_delay_wet": 0.6},
        "global":     {"complexity": 0.2, "randomness": 0.3, "tempo_center": 0.3},
        "has_drums":  False,
        "has_chords": True,
        "has_voice":  True,
        "has_t99":    True,
    },

    "percussive": {
        "drone":      {"gain": 0.6},
        "texture":    {"density": 0.4},
        "percussive": {"density": 0.8, "chaos": 0.5, "speed": 0.7, "cycle_len": 0.6},
        "melodic":    {},
        "global":     {"complexity": 0.6, "randomness": 0.6, "tempo_center": 0.7},
        "has_drums":  True,
        "has_chords": False,
        "has_voice":  False,
        "has_t99":    False,
    },

    "melodic": {
        "drone":      {"gain": 0.7},
        "texture":    {"density": 0.5},
        "percussive": {},
        "melodic":    {"t99_slow": 0.7, "chord_slow": 0.7, "chord_room": 0.8, "voice_room": 0.9},
        "global":     {"complexity": 0.4, "randomness": 0.3, "tempo_center": 0.3},
        "has_drums":  False,
        "has_chords": True,
        "has_voice":  True,
        "has_t99":    True,
    },

    "full": {
        "drone":      {},
        "texture":    {},
        "percussive": {"window_frac": 0.55},
        "melodic":    {},
        "global":     {"complexity": 0.6, "randomness": 0.5, "tempo_center": 0.5},
        "has_drums":  True,
        "has_chords": True,
        "has_voice":  True,
        "has_t99":    True,
    },

    "balanced": {
        "drone":      {"gain": 0.7},
        "texture":    {},
        "percussive": {"window_frac": 0.5},
        "melodic":    {"chord_gain": 0.7},
        "global":     {"complexity": 0.5, "randomness": 0.5, "tempo_center": 0.5},
        "has_drums":  True,
        "has_chords": True,
        "has_voice":  True,
        "has_t99":    True,
    },

    "glitch": {
        "drone":      {},
        "texture":    {"speed_rand": 0.9},
        "percussive": {"chaos": 0.9, "density": 0.7, "rest_prob": 0.6},
        "melodic":    {},
        "global":     {"randomness": 0.9, "complexity": 0.8, "tempo_center": 0.6},
        "has_drums":  True,
        "has_chords": False,
        "has_voice":  False,
        "has_t99":    False,
    },
}

MODE_NAMES = list(MODES.keys())

DOMAIN_KEYS = {"drone", "texture", "percussive", "melodic", "global"}


def nearest_mode(genomes: dict) -> tuple:
    """
    Find the mode whose gene targets are closest to current genome state.
    genomes: dict of domain_name -> GenomePath instance
    Returns (mode_name, distance).
    Distance = sum of squared differences over all shared gene targets.
    """
    best_mode = None
    best_dist = float("inf")
    for name, mode in MODES.items():
        dist = 0.0
        for domain, targets in mode.items():
            if domain not in DOMAIN_KEYS or not isinstance(targets, dict):
                continue
            g = genomes.get(domain)
            if g is None:
                continue
            for gene, target in targets.items():
                if gene in g.GENES:
                    dist += (g.get(gene) - target) ** 2
        if dist < best_dist:
            best_dist = dist
            best_mode = name
    return best_mode, best_dist
