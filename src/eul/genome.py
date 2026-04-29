"""
genome.py — GenomePath base class for the eul genetic composer.

Each genetic domain (drone, texture, percussive, melodic, global) extends this.
Genes are floats in [0, 1]; pattern builders map them to real ranges via .map().

Subclasses define:
  GENES: dict of name -> (default, lo, hi, description)
  MUTATION_RATE: gaussian sigma for small nudges
  BIG_JUMP_PROB: probability of a large exploratory jump per gene
"""

import random
import math


class GenomePath:
    GENES: dict = {}
    MUTATION_RATE: float = 0.12
    BIG_JUMP_PROB: float = 0.04

    def __init__(self, values: dict = None):
        self.values = {k: v[0] for k, v in self.GENES.items()}
        if values:
            self.values.update({k: v for k, v in values.items() if k in self.GENES})

    def get(self, name: str) -> float:
        return self.values[name]

    def map(self, name: str, lo: float, hi: float, integer: bool = False):
        """Scale gene [0,1] to [lo, hi]. Optionally round to int."""
        v = lo + self.values[name] * (hi - lo)
        return round(v) if integer else round(v, 3)

    def mutate(self, rate: float = None, big_jump_prob: float = None) -> "GenomePath":
        """Return new instance with mutated values. Uses class defaults unless overridden."""
        rate = rate if rate is not None else self.MUTATION_RATE
        big_jump_prob = big_jump_prob if big_jump_prob is not None else self.BIG_JUMP_PROB
        new = {}
        for name, val in self.values.items():
            _, lo, hi, _ = self.GENES[name]
            if random.random() < big_jump_prob:
                delta = random.gauss(0, 0.3)
            else:
                delta = random.gauss(0, rate)
            new[name] = max(lo, min(hi, val + delta))
        return self.__class__(new)

    def nudge_toward(self, targets: dict, strength: float = 0.2) -> "GenomePath":
        """Pull genes toward target values (mode gravitational pull). Returns new instance."""
        new = dict(self.values)
        for name, target in targets.items():
            if name not in new:
                continue
            _, lo, hi, _ = self.GENES[name]
            current = new[name]
            new[name] = max(lo, min(hi, current + strength * (target - current)))
        return self.__class__(new)

    def apply_override(self, overrides: dict) -> "GenomePath":
        """Snap specific genes to target values (world event hard override). Returns new instance."""
        new = dict(self.values)
        for name, target in overrides.items():
            if name not in new:
                continue
            _, lo, hi, _ = self.GENES[name]
            new[name] = max(lo, min(hi, float(target)))
        return self.__class__(new)

    def to_dict(self) -> dict:
        return dict(self.values)

    @classmethod
    def from_dict(cls, d: dict) -> "GenomePath":
        return cls(d)

    def __repr__(self):
        lines = [f"{self.__class__.__name__}:"]
        for name, val in self.values.items():
            lines.append(f"  {name:<28} {val:.3f}")
        return "\n".join(lines)
