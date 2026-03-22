from genome import GenomePath


class GlobalGenome(GenomePath):
    """
    The heartbeat and character of the whole system.
    Tempo, structural complexity, and global chaos live here.
    """
    MUTATION_RATE = 0.08
    BIG_JUMP_PROB = 0.03
    GENES = {
        "tempo_center":      (0.5,  0.0, 1.0, "base cps, maps to 0.4-1.2"),
        "tempo_range":       (0.4,  0.1, 1.0, "perlin sweep width, maps to 0.05-0.5"),
        "tempo_drift_speed": (0.5,  0.0, 1.0, "perlin slow factor, maps to 16-48"),
        "complexity":        (0.5,  0.0, 1.0, "how many transforms stack up"),
        "randomness":        (0.5,  0.0, 1.0, "global chaos driver"),
    }
