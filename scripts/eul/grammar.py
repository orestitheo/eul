"""
grammar.py — gene-driven TidalCycles pattern backbone grammar.

Instead of hardcoded transform templates, picks operators from a weighted pool
driven by chaos and complexity genes. Applied to drums (full pool) and chords
(tame subset). Drone and texture stay structurally clean.

Main interface:
  pick_transforms(chaos, complexity, pool="drums") -> list[str]
  wrap_pattern(sound_expr, transforms) -> str
"""

import random


# ── Transform pool ─────────────────────────────────────────────────────────────
#
# Each entry: (fn, weight_fn)
# fn(chaos, complexity) -> TidalCycles operator string
# weight_fn(chaos, complexity) -> float weight (higher = more likely to be picked)

def _every_rev(chaos, complexity):
    interval = max(2, round(2 + (1 - chaos) * 6))   # 2 at high chaos, 8 at low
    return f"every {interval} rev"

def _every_fast(chaos, complexity):
    interval = max(3, round(3 + (1 - chaos) * 5))
    return f"every {interval} (fast 2)"

def _jux_rev(chaos, complexity):
    interval = max(3, round(3 + (1 - chaos) * 4))
    return f"every {interval} (jux rev)"

def _sometimes_fast(chaos, complexity):
    return "sometimes (fast 2)"

def _scramble(chaos, complexity):
    n = random.choice([4, 8])
    return f"scramble {n}"

def _chunk(chaos, complexity):
    n = random.choice([4, 8])
    return f"chunk {n} (fast 2)"

def _palindrome(chaos, complexity):
    return "palindrome"

def _iter(chaos, complexity):
    n = random.choice([4, 8])
    return f"iter {n}"


# Full drum pool — destructive transforms included
DRUM_POOL = [
    (_every_rev,      lambda ch, co: 0.8),
    (_jux_rev,        lambda ch, co: 0.6),
    (_every_fast,     lambda ch, co: 0.4 + ch * 0.5),
    (_sometimes_fast, lambda ch, co: ch * 0.7),
    (_palindrome,     lambda ch, co: 0.3 + co * 0.4),
    (_iter,           lambda ch, co: 0.2 + co * 0.4),
    (_scramble,       lambda ch, co: max(0.0, (ch - 0.5) * 2.0)),   # only at chaos > 0.5
    (_chunk,          lambda ch, co: max(0.0, (ch - 0.4) * 1.5)),   # only at chaos > 0.4
]

# Tame chord pool — no scramble, chunk, or fast transforms (protects looping pads)
CHORD_POOL = [
    (_every_rev,  lambda ch, co: 0.8),
    (_jux_rev,    lambda ch, co: 0.7),
    (_palindrome, lambda ch, co: 0.4 + co * 0.4),
    (_iter,       lambda ch, co: 0.2 + co * 0.3),
]

POOLS = {
    "drums":  DRUM_POOL,
    "chords": CHORD_POOL,
}


def pick_transforms(chaos: float, complexity: float, pool: str = "drums", max_n: int = None) -> list:
    """
    Select 0-N TidalCycles operator strings to wrap a pattern with.
    max_n defaults to min(4, round(complexity * 4)).
    pool: "drums" or "chords"
    """
    if max_n is None:
        max_n = min(4, round(complexity * 4))
    if max_n == 0:
        return []

    entries = POOLS.get(pool, DRUM_POOL)
    fns     = [fn for fn, _ in entries]
    weights = [wfn(chaos, complexity) for _, wfn in entries]

    selected = []
    available = list(range(len(fns)))
    for _ in range(max_n):
        if not available:
            break
        w = [weights[i] for i in available]
        if sum(w) == 0:
            break
        chosen_i = random.choices(available, weights=w, k=1)[0]
        selected.append(fns[chosen_i](chaos, complexity))
        available.remove(chosen_i)

    return selected


def wrap_pattern(sound_expr: str, transforms: list) -> str:
    """
    Wrap a sound expression with transform strings using $ chaining.
    transforms = ["every 4 rev", "jux rev"]
    Result: "every 4 rev $ jux rev $ <sound_expr>"
    """
    if not transforms:
        return sound_expr
    return " $ ".join(transforms) + " $ " + sound_expr
