#!/usr/bin/env python3
"""
eul — genetic self-evolving pattern composer.

Each full evolve:
  1. Mutate genes
  2. Find nearest mode attractor, nudge toward it
  3. Build patterns from genes
  4. Send to TidalCycles REPL
  5. Save gene state to disk

Micro-evolve (every 60s): nudge a few gains/filters without restructuring.
"""

import random
import sys
import time
import os

# Allow running directly or as a module
sys.path.insert(0, os.path.dirname(__file__))

from genes   import Genes
from modes   import MODES, MODE_NAMES, nearest_mode
from send    import send, send_all
import patterns as P

INTERVAL_MINUTES = 6


def build_session(g):
    """
    Given genes, determine which layers are active and build all pattern lines.
    Returns list of lines to send.
    """
    mode_name, _ = nearest_mode(g)
    mode = MODES[mode_name]

    has_drums  = mode["has_drums"]
    has_chords = mode["has_chords"]
    has_voice  = mode["has_voice"]
    has_t99    = mode["has_t99"]

    # Glitch: occasional chords
    if mode_name == "glitch" and random.random() < 0.3:
        has_chords = True

    # Voice and t99 are probabilistic even when structurally allowed
    voice_prob = 0.6 if mode_name in ("melodic", "sparse") else 0.35
    if has_voice and random.random() > voice_prob:
        has_voice = False
    if has_t99 and mode_name in ("full", "balanced") and random.random() < 0.4:
        has_t99 = False

    # Timing: drums and chords share the cycle, never overlap
    total     = g.map("drum_cycle_len", 6, 12, integer=True)
    drum_frac = g.get("drum_window_frac")
    drum_on   = max(2, round(total * drum_frac)) if has_drums else 0
    chord_on  = total - drum_on if has_chords else 0

    lines = [P.tempo(g), P.drone(g), P.texture(g)]

    lines.append(P.melodic(g, chord_on, total) if has_t99 else "d3 silence")
    lines.append(P.drums(g, mode)              if has_drums  else "d4 silence")
    lines.append(P.chords(g, chord_on, total)  if has_chords else "d6 silence")
    lines.append(P.voice(g, chord_on, total)   if has_voice  else "d5 silence")

    return lines, mode_name


def evolve(g):
    # 1. Mutate
    g = g.mutate(rate=0.12, big_jump_prob=0.04)

    # 2. Pull toward nearest mode
    mode_name, dist = nearest_mode(g)
    mode = MODES[mode_name]
    # Weaker pull when far away (let it wander), stronger when close (stabilise)
    pull_strength = 0.15 if dist > 1.0 else 0.25
    g = g.nudge_toward(mode["genes"], strength=pull_strength)

    # 3. Build and send
    lines, mode_name = build_session(g)
    print(f"Evolving... [mode: {mode_name}]")
    send_all(lines)

    # 4. Persist
    g.save()
    print("Done.")
    return g


def micro_evolve(g):
    """Nudge gains and filter sweeps without restructuring."""
    print("Micro-evolving...")

    # Small gene nudge (tighter than full evolve)
    g = g.mutate(rate=0.05, big_jump_prob=0.0)

    lpf_lo = g.map("drone_lpf_lo", 100, 600, integer=True)
    lpf_hi = g.map("drone_lpf_hi", 600, 3000, integer=True)
    slow_f = g.map("drone_lpf_speed", 8, 24, integer=True)
    gain   = g.map("drone_gain", 0.4, 1.0)
    send(f'd1 $ (# gain {gain}) $ (# lpf (slow {slow_f} $ range {lpf_lo} {lpf_hi} perlin))')

    t_gain = g.map("texture_gain", 0.3, 0.9)
    t_spd  = g.map("texture_speed_rand", 0.1, 1.0)
    send(f'd2 $ (# gain {t_gain}) $ (# speed (rand + {round(t_spd, 2)}))')

    c_gain = g.map("chord_gain", 0.4, 1.0)
    send(f'd6 $ (# gain {c_gain})')

    g.save()
    print("Micro-evolve done.")
    return g


if __name__ == "__main__":
    g = Genes.load()

    if "--once" in sys.argv:
        evolve(g)
    elif "--micro" in sys.argv:
        micro_evolve(g)
    elif "--print" in sys.argv:
        mode_name, dist = nearest_mode(g)
        print(f"Current genes (nearest mode: {mode_name}, dist: {dist:.3f})")
        print(g)
    else:
        print(f"eul evolve: full every {INTERVAL_MINUTES}min, micro every 60s. Ctrl+C to stop.")
        g = evolve(g)
        last_full = time.time()
        while True:
            time.sleep(60)
            if time.time() - last_full >= INTERVAL_MINUTES * 60:
                g = evolve(g)
                last_full = time.time()
            else:
                g = micro_evolve(g)
