from genome import GenomePath


class TextureGenome(GenomePath):
    """
    The atmosphere around the drone. Cycles in and out, shifts speed and density.
    Medium mutation — should breathe noticeably but not flicker.
    """
    MUTATION_RATE = 0.10
    BIG_JUMP_PROB = 0.03
    GENES = {
        "density":     (0.6,  0.0, 1.0, "whenmod on/total ratio"),
        "slow":        (0.5,  0.0, 1.0, "slow factor, maps to 1-4"),
        "speed_rand":  (0.5,  0.0, 1.0, "random speed width (perlin range)"),
        "gain":        (0.6,  0.3, 0.9, "texture gain"),
        "sample_bias": (0.5,  0.0, 1.0, "bias toward which texture sample"),
        "room":        (0.6,  0.0, 1.0, "reverb amount"),
    }
