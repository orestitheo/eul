from genome import GenomePath


class MelodicGenome(GenomePath):
    """
    Covers chords (d6), t99 melodic layer (d3), and voice (d5).
    All three share harmonic context so they evolve together.
    """
    MUTATION_RATE = 0.10
    BIG_JUMP_PROB = 0.04
    GENES = {
        # Chord layer (d6)
        "chord_slow":       (0.5,  0.0, 1.0, "slow factor, maps to 1-4"),
        "chord_loop_len":   (0.5,  0.0, 1.0, "loopAt value, maps to 1-8 beats"),
        "chord_staccato":   (0.2,  0.0, 1.0, "legato length, 0=short 1=long"),
        "chord_delay_wet":  (0.5,  0.0, 1.0, "delay mix"),
        "chord_room":       (0.7,  0.0, 1.0, "reverb amount"),
        "chord_gain":       (0.7,  0.3, 1.0, "chord gain"),
        # T99 melodic layer (d3)
        "t99_slow":         (0.5,  0.0, 1.0, "slow factor, maps to 2-5"),
        "t99_interval":     (0.5,  0.0, 1.0, "interval pattern index"),
        "t99_gain":         (0.8,  0.5, 1.0, "t99 gain"),
        # Voice layer (d5)
        "voice_slow":       (0.5,  0.0, 1.0, "slow factor, maps to 3-6"),
        "voice_stretch":    (0.5,  0.0, 1.0, "speed stretch, maps to 0.4-1.0"),
        "voice_gain":       (0.5,  0.3, 0.7, "voice gain"),
        "voice_room":       (0.9,  0.6, 1.0, "voice reverb"),
        "voice_interval":   (0.5,  0.0, 1.0, "voice interval pattern index"),
    }
