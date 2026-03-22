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
        "chord_rhythm":     (0.1,  0.0, 1.0, "step density for non-looping banks, 0=one hit, 1=dense"),
        "chord_density":    (0.3,  0.0, 1.0, "fast multiplier for non-looping banks: 0=slow, 1=fast 4"),
        "chord_delay_wet":  (0.5,  0.0, 1.0, "delay mix"),
        "chord_room":       (0.7,  0.0, 1.0, "reverb amount"),
        "chord_gain":       (0.7,  0.3, 1.0, "chord gain"),
        # T99 melodic layer (d3)
        "t99_slow":         (0.5,  0.0, 1.0, "slow factor, maps to 2-5"),
        "t99_interval":     (0.5,  0.0, 1.0, "interval pattern index"),
        "t99_gain":         (0.8,  0.5, 1.0, "t99 gain"),
        "t99_rhythm":       (0.2,  0.0, 1.0, "rest density — 0=sparse, 1=dense stuttering"),
        "t99_speed":        (0.5,  0.0, 1.0, "pitch/speed center, maps to 0.4-1.8, perlin-modulated"),
        "t99_speed_rand":   (0.3,  0.0, 1.0, "pitch drift width (perlin range)"),
        "t99_begin":        (0.0,  0.0, 0.7, "sample start point — different timbres from same file"),
        "t99_chop":         (0.0,  0.0, 1.0, "chop sample into fragments, 0=off, maps to 2-8 chunks"),
        "t99_layer":        (0.0,  0.0, 1.0, "stack a second t99 voice at different speed/pitch"),
        # Voice layer (d5)
        "voice_slow":       (0.5,  0.0, 1.0, "slow factor, maps to 3-6"),
        "voice_stretch":    (0.5,  0.0, 1.0, "speed stretch, maps to 0.4-1.0"),
        "voice_gain":       (0.5,  0.3, 0.7, "voice gain"),
        "voice_room":       (0.9,  0.6, 1.0, "voice reverb"),
        "voice_interval":   (0.5,  0.0, 1.0, "voice interval pattern index"),
    }
