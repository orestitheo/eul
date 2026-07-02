import random

from ..genome import GenomePath


class PercussiveGenome(GenomePath):
    """
    The most volatile domain — but the groove itself persists. groove_seed
    freezes the structural random draws in the drum builder, so per-tick
    mutations make small adjustments (hit counts, syncopation, accents)
    to the SAME beat instead of rerolling it. The seed itself rerolls
    rarely, giving each groove a lifetime of several minutes.
    """
    MUTATION_RATE = 0.06
    BIG_JUMP_PROB = 0.02
    GROOVE_REROLL_PROB = 0.07   # ~once per 5-6 min at 45s ticks

    def mutate(self, rate=None, big_jump_prob=None):
        g = super().mutate(rate, big_jump_prob)
        if random.random() < self.GROOVE_REROLL_PROB:
            g.values["groove_seed"] = random.random()          # new groove
        else:
            g.values["groove_seed"] = self.values["groove_seed"]  # keep identity
        return g

    GENES = {
        "density":     (0.5,  0.0, 1.0, "euclidean hits per 8 steps, maps to 2-8"),
        "cycle_len":   (0.5,  0.0, 1.0, "whenmod total length, maps to 6-12"),
        "window_frac": (0.5,  0.1, 0.9, "fraction of cycle drums occupy"),
        "speed":       (0.5,  0.0, 1.0, "0=half-time, 0.5=normal, 1=double-time"),
        "rest_prob":   (0.3,  0.0, 0.8, "probability of silence per step"),
        "polyrhythm":  (0.3,  0.0, 1.0, "chance of layering a second rhythm"),
        "chaos":       (0.2,  0.0, 1.0, "how often destructive transforms fire"),
        "swing":       (0.4,  0.0, 1.0, "shuffle amount — pushes off-beats late, off-grid flow"),
        "punch":       (0.55, 0.0, 1.0, "accent dynamics + waveshaping drive — hard beats"),
        "ghost":       (0.3,  0.0, 1.0, "offset ghost-note double a 1/16 late, flowy fills"),
        "euclid_bias": (0.4,  0.0, 1.0, "chance to render an interlocking euclidean groove vs step seq"),
        "groove_seed": (0.5,  0.0, 1.0, "groove identity — seeds structural draws, held across mutations"),
        "rotation":    (0.3,  0.0, 1.0, "hat-voice euclidean rotation — drifting it shifts syncopation"),
        "slice_bias":  (0.5,  0.0, 1.0, "which region of the bank to favour, 0=low 1=high"),
        "bank_pos":    (0.0,  0.0, 1.0, "position across bank spectrum — 0=first bank, 1=last bank, in-between=crossfade"),
    }
