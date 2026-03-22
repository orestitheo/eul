"""
modes.py — predefined mode attractors for the genetic composer.

A mode is a partial gene dict — only defines the genes it cares about.
During evolution, the nearest mode exerts a gravitational pull on the
current gene state. The system drifts toward it but never fully snaps.

Modes can also hard-gate layers (has_drums, has_chords etc.) — these
are structural decisions that don't make sense as continuous genes.
"""

# Each mode: gene targets (partial) + structural flags
MODES = {
    "minimal": {
        "genes": {
            "drone_gain":       0.9,
            "texture_density":  0.8,
            "texture_gain":     0.7,
            "complexity":       0.1,
            "randomness":       0.2,
            "tempo_center":     0.2,
        },
        "has_drums":  False,
        "has_chords": False,
        "has_voice":  False,
        "has_t99":    False,
    },

    "sparse": {
        "genes": {
            "drone_gain":       0.8,
            "chord_slow":       0.8,
            "chord_room":       0.9,
            "complexity":       0.2,
            "randomness":       0.3,
            "tempo_center":     0.3,
        },
        "has_drums":  False,
        "has_chords": True,
        "has_voice":  True,   # optional, decided by voice_prob
        "has_t99":    True,
    },

    "percussive": {
        "genes": {
            "drum_density":     0.8,
            "drum_chaos":       0.5,
            "drum_speed":       0.7,
            "drum_cycle_len":   0.6,
            "complexity":       0.6,
            "randomness":       0.6,
            "tempo_center":     0.7,
        },
        "has_drums":  True,
        "has_chords": False,
        "has_voice":  False,
        "has_t99":    False,
    },

    "melodic": {
        "genes": {
            "melodic_slow":     0.7,
            "chord_slow":       0.7,
            "chord_room":       0.8,
            "voice_room":       0.9,
            "complexity":       0.4,
            "randomness":       0.3,
            "tempo_center":     0.3,
            "drone_gain":       0.7,
        },
        "has_drums":  False,
        "has_chords": True,
        "has_voice":  True,
        "has_t99":    True,
    },

    "full": {
        "genes": {
            "complexity":       0.6,
            "randomness":       0.5,
            "drum_window_frac": 0.55,
            "tempo_center":     0.5,
        },
        "has_drums":  True,
        "has_chords": True,
        "has_voice":  True,
        "has_t99":    True,
    },

    "balanced": {
        "genes": {
            "complexity":       0.5,
            "randomness":       0.5,
            "drum_window_frac": 0.5,
            "drone_gain":       0.7,
            "chord_gain":       0.7,
            "tempo_center":     0.5,
        },
        "has_drums":  True,
        "has_chords": True,
        "has_voice":  True,
        "has_t99":    True,
    },

    "glitch": {
        "genes": {
            "drum_chaos":       0.9,
            "drum_density":     0.7,
            "drum_rest_prob":   0.6,
            "randomness":       0.9,
            "complexity":       0.8,
            "texture_speed_rand": 0.9,
            "tempo_center":     0.6,
        },
        "has_drums":  True,
        "has_chords": False,  # rarely — decided per-evolve
        "has_voice":  False,
        "has_t99":    False,
    },
}

MODE_NAMES = list(MODES.keys())


def nearest_mode(genes):
    """
    Find the mode whose gene targets are closest to current gene state.
    Distance = sum of squared differences over shared genes.
    """
    best_mode = None
    best_dist = float("inf")
    for name, mode in MODES.items():
        dist = sum(
            (genes.get(g) - v) ** 2
            for g, v in mode["genes"].items()
        )
        if dist < best_dist:
            best_dist = dist
            best_mode = name
    return best_mode, best_dist
