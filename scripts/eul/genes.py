"""
genes.py — genetic state for the eul self-evolving composer.

Each gene is a float in [0, 1] (normalized). Pattern builders map these
to their real ranges. This keeps mutation logic simple and universal.

Genes mutate each full evolve: small gaussian nudge most of the time,
occasional large jump. State persists to disk so evolution survives restarts.
"""

import random
import math
import json
import os

STATE_FILE = "/opt/eul/state/genes.json"

# Gene definitions: name -> (default, min, max, description)
# All stored as floats. Ints are rounded when used.
GENE_DEFS = {
    # --- Tempo ---
    "tempo_center":      (0.5,  0.0, 1.0, "base cps center, mapped to 0.4-1.2"),
    "tempo_range":       (0.4,  0.1, 1.0, "how wide the perlin tempo sweep is"),
    "tempo_drift_speed": (0.5,  0.0, 1.0, "slow factor for perlin tempo, mapped to 16-48"),

    # --- Drum structure ---
    "drum_density":      (0.5,  0.0, 1.0, "euclidean hits per 8 steps, mapped to 2-8"),
    "drum_cycle_len":    (0.5,  0.0, 1.0, "total whenmod length, mapped to 6-12"),
    "drum_window_frac":  (0.5,  0.1, 0.9, "fraction of cycle drums occupy"),
    "drum_speed":        (0.5,  0.0, 1.0, "0=half-time, 0.5=normal, 1=double-time"),
    "drum_rest_prob":    (0.3,  0.0, 0.8, "probability of ~ per step"),
    "drum_polyrhythm":   (0.3,  0.0, 1.0, "chance of layering a second rhythm"),
    "drum_chaos":        (0.2,  0.0, 1.0, "how often rev/fast transforms fire"),
    "drum_slice_bias":   (0.5,  0.0, 1.0, "which region of the bank to favour, 0=low 1=high"),

    # --- Chord structure ---
    "chord_slow":        (0.5,  0.0, 1.0, "slow factor, mapped to 1-4"),
    "chord_loop_len":    (0.5,  0.0, 1.0, "loopAt value, mapped to 1-8"),
    "chord_staccato":    (0.2,  0.0, 1.0, "legato length when staccato, 0=short 1=long"),
    "chord_delay_wet":   (0.5,  0.0, 1.0, "delay mix"),
    "chord_room":        (0.7,  0.0, 1.0, "reverb amount"),
    "chord_gain":        (0.7,  0.3, 1.0, "chord gain"),

    # --- Drone ---
    "drone_gain":        (0.7,  0.4, 1.0, "drone gain"),
    "drone_lpf_lo":      (0.3,  0.0, 1.0, "lpf low, mapped to 100-600"),
    "drone_lpf_hi":      (0.7,  0.0, 1.0, "lpf high, mapped to 600-3000"),
    "drone_lpf_speed":   (0.5,  0.0, 1.0, "lpf sweep slow factor, mapped to 8-24"),
    "drone_room":        (0.8,  0.5, 1.0, "drone reverb"),

    # --- Texture ---
    "texture_density":   (0.6,  0.0, 1.0, "whenmod on/total ratio"),
    "texture_slow":      (0.5,  0.0, 1.0, "slow factor, mapped to 1-4"),
    "texture_speed_rand":(0.5,  0.0, 1.0, "random speed amount"),
    "texture_gain":      (0.6,  0.3, 0.9, "texture gain"),

    # --- Melodic (t99) ---
    "melodic_slow":      (0.5,  0.0, 1.0, "slow factor, mapped to 2-5"),
    "melodic_interval":  (0.5,  0.0, 1.0, "which interval pattern, indexes into list"),
    "melodic_gain":      (0.8,  0.5, 1.0, "t99 gain"),

    # --- Voice ---
    "voice_slow":        (0.5,  0.0, 1.0, "slow factor, mapped to 3-6"),
    "voice_stretch":     (0.5,  0.0, 1.0, "speed stretch, mapped to 0.4-1.0"),
    "voice_gain":        (0.5,  0.3, 0.7, "voice gain"),
    "voice_room":        (0.9,  0.6, 1.0, "voice reverb"),

    # --- Global feel ---
    "complexity":        (0.5,  0.0, 1.0, "how many transforms/effects stack up"),
    "randomness":        (0.5,  0.0, 1.0, "drives rest_prob, chaos, speed variation"),
}


class Genes:
    def __init__(self, values=None):
        if values:
            self.values = values
        else:
            self.values = {k: v[0] for k, v in GENE_DEFS.items()}

    def get(self, name):
        return self.values[name]

    def mutate(self, rate=0.15, big_jump_prob=0.05):
        """
        Mutate all genes slightly. Most get a small gaussian nudge.
        Each gene has a big_jump_prob chance of a larger jump.
        rate controls standard deviation of the nudge.
        """
        new = {}
        for name, val in self.values.items():
            _, lo, hi, _ = GENE_DEFS[name]
            if random.random() < big_jump_prob:
                # Large jump — explore
                delta = random.gauss(0, 0.3)
            else:
                # Small nudge — exploit
                delta = random.gauss(0, rate)
            new[name] = max(lo, min(hi, val + delta))
        return Genes(new)

    def nudge_toward(self, target_values, strength=0.2):
        """
        Pull genes toward a target dict (mode attractor).
        strength=0.2 means move 20% of the way there each call.
        Only pulls genes that are defined in target_values.
        """
        new = dict(self.values)
        for name, target in target_values.items():
            if name not in new:
                continue
            _, lo, hi, _ = GENE_DEFS[name]
            current = new[name]
            new[name] = max(lo, min(hi, current + strength * (target - current)))
        return Genes(new)

    def save(self, path=STATE_FILE):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.values, f, indent=2)

    @classmethod
    def load(cls, path=STATE_FILE):
        if not os.path.exists(path):
            print(f"No state file at {path}, starting fresh.")
            return cls()
        with open(path) as f:
            saved = json.load(f)
        # Fill in any new genes not in saved state
        values = {k: v[0] for k, v in GENE_DEFS.items()}
        values.update({k: v for k, v in saved.items() if k in GENE_DEFS})
        return cls(values)

    def map(self, name, lo, hi, integer=False):
        """Map gene [0,1] to [lo, hi]. Optionally round to int."""
        v = lo + self.values[name] * (hi - lo)
        return round(v) if integer else round(v, 3)

    def __repr__(self):
        lines = ["Genes:"]
        for name, val in self.values.items():
            lines.append(f"  {name:<24} {val:.3f}")
        return "\n".join(lines)
