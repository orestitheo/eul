from genome import GenomePath


class MelodicGenome(GenomePath):
    """
    Covers chords (d6) and voice (d5).
    All chord banks — looping pads and non-looping instruments alike —
    are selected via chord_bank_pos and handled in patterns.chords().
    """
    MUTATION_RATE = 0.10
    BIG_JUMP_PROB = 0.04
    GENES = {
        # Chord layer (d6)
        "chord_bank_pos":   (0.5,  0.0, 1.0, "position across chord banks"),
        "chord_begin":      (0.2,  0.0, 0.8, "sample start point for chord banks"),
        "chord_slow":       (0.5,  0.0, 1.0, "slow factor, maps to 1-4"),
        "chord_loop_len":   (0.5,  0.0, 1.0, "loopAt value, maps to 1-8 beats"),
        "chord_staccato":   (0.2,  0.0, 1.0, "legato length, 0=short 1=long"),
        "chord_rhythm":     (0.1,  0.0, 1.0, "step density for non-looping banks, 0=one hit, 1=dense"),
        "chord_density":    (0.3,  0.0, 1.0, "fast multiplier for non-looping banks: 0=slow, 1=fast 4"),
        "chord_delay_wet":  (0.5,  0.0, 1.0, "delay mix"),
        "chord_room":       (0.7,  0.0, 1.0, "reverb amount"),
        "chord_gain":       (0.7,  0.3, 1.0, "chord gain"),
        # Voice layer (d5)
        "voice_slow":       (0.5,  0.0, 1.0, "slow factor, maps to 3-6"),
        "voice_stretch":    (0.5,  0.0, 1.0, "speed stretch, maps to 0.4-1.0"),
        "voice_gain":       (0.5,  0.3, 0.7, "voice gain"),
        "voice_room":       (0.9,  0.6, 1.0, "voice reverb"),
        "voice_interval":   (0.5,  0.0, 1.0, "voice interval pattern index"),
    }
