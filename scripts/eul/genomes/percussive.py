from genome import GenomePath


class PercussiveGenome(GenomePath):
    """
    The most volatile domain. Drums should shift character frequently —
    high mutation rate means rhythm and texture change noticeably every evolve.
    """
    MUTATION_RATE = 0.18
    BIG_JUMP_PROB = 0.06
    GENES = {
        "density":     (0.5,  0.0, 1.0, "euclidean hits per 8 steps, maps to 2-8"),
        "cycle_len":   (0.5,  0.0, 1.0, "whenmod total length, maps to 6-12"),
        "window_frac": (0.5,  0.1, 0.9, "fraction of cycle drums occupy"),
        "speed":       (0.5,  0.0, 1.0, "0=half-time, 0.5=normal, 1=double-time"),
        "rest_prob":   (0.3,  0.0, 0.8, "probability of silence per step"),
        "polyrhythm":  (0.3,  0.0, 1.0, "chance of layering a second rhythm"),
        "chaos":       (0.2,  0.0, 1.0, "how often destructive transforms fire"),
        "slice_bias":  (0.5,  0.0, 1.0, "which region of the bank to favour, 0=low 1=high"),
        "bank_pos":    (0.0,  0.0, 1.0, "position across bank spectrum — 0=first bank, 1=last bank, in-between=crossfade"),
    }
