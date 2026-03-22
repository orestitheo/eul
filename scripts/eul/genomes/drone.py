from genome import GenomePath


class DroneGenome(GenomePath):
    """
    The foundation. Drifts very slowly — it's what holds the space open.
    Low mutation rate keeps it stable between full evolves.
    """
    MUTATION_RATE = 0.06
    BIG_JUMP_PROB = 0.02
    GENES = {
        "gain":       (0.7,  0.4, 1.0, "drone gain"),
        "lpf_lo":     (0.3,  0.0, 1.0, "lpf sweep low, maps to 100-600 Hz"),
        "lpf_hi":     (0.7,  0.0, 1.0, "lpf sweep high, maps to 600-3000 Hz"),
        "lpf_speed":  (0.5,  0.0, 1.0, "lpf perlin slow factor, maps to 8-24"),
        "room":       (0.8,  0.5, 1.0, "reverb amount"),
        "pitch":      (0.5,  0.0, 1.0, "semitone offset, maps to -7 to +7"),
        "begin":      (0.3,  0.0, 0.6, "sample start point"),
        "gate":       (0.1,  0.0, 1.0, "gating amount — 0=always on, 1=frequently silent"),
    }
