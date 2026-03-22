#!/usr/bin/env python3
"""
eul — genetic self-evolving pattern composer v2.

Each full evolve (every 3 min):
  1. Mutate each domain genome independently (per-domain rate)
  2. Find nearest mode attractor, nudge each domain toward its targets
  3. Tick world events — may fire a new event or apply active ones
  4. Build patterns and send to TidalCycles
  5. Save state

Micro-evolve (every 30s):
  Nudge gains/filters within the current structure, no layer switching.
"""

import random
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(__file__))

from genomes.drone      import DroneGenome
from genomes.texture    import TextureGenome
from genomes.percussive import PercussiveGenome
from genomes.melodic    import MelodicGenome
from genomes.global_    import GlobalGenome
from modes   import MODES, MODE_NAMES, nearest_mode, DOMAIN_KEYS
from events  import EventManager, EVENTS
from send    import send, send_all
import patterns as P

STATE_FILE = "/opt/eul/state/genes.json"
INTERVAL_MINUTES = 3


# ── State persistence ──────────────────────────────────────────────────────────

def _fresh_genomes():
    return {
        "drone":      DroneGenome(),
        "texture":    TextureGenome(),
        "percussive": PercussiveGenome(),
        "melodic":    MelodicGenome(),
        "global":     GlobalGenome(),
    }


def _migrate_v1(flat: dict) -> dict:
    """Map old flat gene dict to new domain genomes."""
    return {
        "drone": DroneGenome({
            "gain":      flat.get("drone_gain",      0.7),
            "lpf_lo":    flat.get("drone_lpf_lo",    0.3),
            "lpf_hi":    flat.get("drone_lpf_hi",    0.7),
            "lpf_speed": flat.get("drone_lpf_speed", 0.5),
            "room":      flat.get("drone_room",      0.8),
            "pitch":     0.5,
            "begin":     0.3,
        }),
        "texture": TextureGenome({
            "density":     flat.get("texture_density",   0.6),
            "slow":        flat.get("texture_slow",      0.5),
            "speed_rand":  flat.get("texture_speed_rand",0.5),
            "gain":        flat.get("texture_gain",      0.6),
            "sample_bias": 0.5,
            "room":        0.6,
        }),
        "percussive": PercussiveGenome({
            "density":     flat.get("drum_density",    0.5),
            "cycle_len":   flat.get("drum_cycle_len",  0.5),
            "window_frac": flat.get("drum_window_frac",0.5),
            "speed":       flat.get("drum_speed",      0.5),
            "rest_prob":   flat.get("drum_rest_prob",  0.3),
            "polyrhythm":  flat.get("drum_polyrhythm", 0.3),
            "chaos":       flat.get("drum_chaos",      0.2),
            "slice_bias":  flat.get("drum_slice_bias", 0.5),
            "bank_pos":    flat.get("drum_bank_idx",   0.0),
        }),
        "melodic": MelodicGenome({
            "chord_slow":      flat.get("chord_slow",      0.5),
            "chord_loop_len":  flat.get("chord_loop_len",  0.5),
            "chord_staccato":  flat.get("chord_staccato",  0.2),
            "chord_delay_wet": flat.get("chord_delay_wet", 0.5),
            "chord_room":      flat.get("chord_room",      0.7),
            "chord_gain":      flat.get("chord_gain",      0.7),
            "t99_slow":        flat.get("melodic_slow",    0.5),
            "t99_interval":    flat.get("melodic_interval",0.5),
            "t99_gain":        flat.get("melodic_gain",    0.8),
            "voice_slow":      flat.get("voice_slow",      0.5),
            "voice_stretch":   flat.get("voice_stretch",   0.5),
            "voice_gain":      flat.get("voice_gain",      0.5),
            "voice_room":      flat.get("voice_room",      0.9),
            "voice_interval":  flat.get("melodic_interval",0.5),
        }),
        "global": GlobalGenome({
            "tempo_center":      flat.get("tempo_center",      0.5),
            "tempo_range":       flat.get("tempo_range",       0.4),
            "tempo_drift_speed": flat.get("tempo_drift_speed", 0.5),
            "complexity":        flat.get("complexity",        0.5),
            "randomness":        flat.get("randomness",        0.5),
        }),
    }


def load_all(path=STATE_FILE):
    """Load genomes + EventManager from state file. Auto-migrates v1 format."""
    if not os.path.exists(path):
        print("No state file found, starting fresh.")
        return _fresh_genomes(), EventManager()

    with open(path) as f:
        saved = json.load(f)

    version = saved.get("version", 1)

    if version == 1:
        # Old flat format or legacy {"genes": {...}, "state": {...}}
        print("Migrating v1 gene state to v2 domain format...")
        flat = saved.get("genes", saved)
        genomes = _migrate_v1(flat)
        return genomes, EventManager()

    # v2 format
    genomes = {
        "drone":      DroneGenome.from_dict(saved.get("drone",      {})),
        "texture":    TextureGenome.from_dict(saved.get("texture",   {})),
        "percussive": PercussiveGenome.from_dict(saved.get("percussive", {})),
        "melodic":    MelodicGenome.from_dict(saved.get("melodic",   {})),
        "global":     GlobalGenome.from_dict(saved.get("global",    {})),
    }
    events = EventManager.from_dict(saved.get("events", {}))
    return genomes, events


def save_all(genomes: dict, events: EventManager, path=STATE_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "version": 2,
        "drone":      genomes["drone"].to_dict(),
        "texture":    genomes["texture"].to_dict(),
        "percussive": genomes["percussive"].to_dict(),
        "melodic":    genomes["melodic"].to_dict(),
        "global":     genomes["global"].to_dict(),
        "events":     events.to_dict(),
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ── Session building ───────────────────────────────────────────────────────────

def build_session(genomes: dict, mode: dict):
    """
    Determine which layers are active and build all pattern lines.
    Returns (list_of_lines, mode_name).
    """
    mode_name, _ = nearest_mode(genomes)
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

    glob = genomes["global"]
    perc = genomes["percussive"]
    mel  = genomes["melodic"]

    total    = perc.map("cycle_len", 6, 12, integer=True)
    drum_frac = perc.get("window_frac")
    drum_on  = max(2, round(total * drum_frac)) if has_drums else 0
    chord_on = total - drum_on if has_chords else 0

    lines = [
        P.tempo(glob),
        P.drone(genomes["drone"]),
        P.texture(genomes["texture"], glob),
    ]
    lines.append(P.melodic(mel, chord_on, total) if has_t99    else "d3 silence")
    lines.append(P.drums(perc, glob)             if has_drums  else "d4 silence")
    lines.append(P.chords(mel, chord_on, total, glob) if has_chords else "d6 silence")
    lines.append(P.voice(mel, chord_on, total)   if has_voice  else "d5 silence")

    return lines, mode_name


# ── Evolution cycles ───────────────────────────────────────────────────────────

def evolve(genomes: dict, events: EventManager):
    # 1. Mutate each domain with its own rate
    genomes = {k: g.mutate() for k, g in genomes.items()}

    # 2. Find nearest mode, nudge each domain toward its targets
    mode_name, dist = nearest_mode(genomes)
    mode = MODES[mode_name]
    pull = 0.15 if dist > 1.0 else 0.25
    for domain, targets in mode.items():
        if domain in DOMAIN_KEYS and isinstance(targets, dict) and domain in genomes:
            genomes[domain] = genomes[domain].nudge_toward(targets, pull)

    # 3. World events
    triggered = events.tick(genomes)
    event_str = f" [event: {triggered}]" if triggered else ""

    # 4. Build and send
    lines, mode_name = build_session(genomes, mode)
    print(f"Evolving... [mode: {mode_name}]{event_str}")
    send_all(lines)

    # 5. Persist
    save_all(genomes, events)
    print("Done.")
    return genomes, events


def micro_evolve(genomes: dict, events: EventManager):
    """Nudge gains/filters without restructuring layers or switching banks."""
    print("Micro-evolving...")

    # Light nudge on all domains (smaller rate, no big jumps)
    genomes = {k: g.mutate(rate=0.07, big_jump_prob=0.0) for k, g in genomes.items()}

    drn  = genomes["drone"]
    tex  = genomes["texture"]
    perc = genomes["percussive"]
    mel  = genomes["melodic"]

    # Drone: filter sweep + gain
    lpf_lo = drn.map("lpf_lo", 100, 600, integer=True)
    lpf_hi = drn.map("lpf_hi", 600, 3000, integer=True)
    slow_f = drn.map("lpf_speed", 8, 24, integer=True)
    gain   = drn.map("gain", 0.4, 1.0)
    send(f'd1 $ (# gain {gain}) $ (# lpf (slow {slow_f} $ range {lpf_lo} {lpf_hi} perlin))')

    # Texture: gain and speed only — don't swap samples, let them play through
    t_gain = tex.map("gain", 0.3, 0.9)
    t_spd  = tex.map("speed_rand", 0.1, 1.0)
    send(f'd2 $ (# gain {t_gain}) $ (# speed (slow 8 $ range {round(1.0 - t_spd * 0.5, 2)} {round(1.0 + t_spd * 0.5, 2)} perlin))')

    # Drums: vary rhythm within the same bank — don't switch banks
    rest_prob  = perc.get("rest_prob")
    slice_bias = perc.get("slice_bias")
    drum_spd   = perc.get("speed")
    from banks import DRUM_BANKS
    bank_pos = perc.get("bank_pos") * (len(DRUM_BANKS) - 1)
    bank     = DRUM_BANKS[int(bank_pos)]
    from banks import BANKS
    max_slices = BANKS[bank]["slices"]
    steps      = random.choice([6, 8, 8, 10])
    seq        = P._drum_seq(bank, steps, max_slices, rest_prob, slice_bias)
    speed_str  = "$ slow 2 " if drum_spd < 0.33 else ("$ fast 2 " if drum_spd > 0.66 else "")
    d_gain     = round(random.uniform(0.8, 0.9), 1)
    send(f'd4 $ (# gain {d_gain}) # room 0 {speed_str}$ sound "{seq}"')

    # Chords: gain nudge only — long samples need to play through
    c_gain = mel.map("chord_gain", 0.4, 1.0)
    send(f'd6 $ (# gain {c_gain})')

    save_all(genomes, events)
    print("Micro-evolve done.")
    return genomes, events


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    genomes, events = load_all()

    if "--once" in sys.argv:
        evolve(genomes, events)

    elif "--micro" in sys.argv:
        micro_evolve(genomes, events)

    elif "--print" in sys.argv:
        mode_name, dist = nearest_mode(genomes)
        print(f"Nearest mode: {mode_name} (dist: {dist:.3f})")
        if events.active:
            print(f"Active events: {events}")
        for domain, g in genomes.items():
            print(g)

    elif "--event" in sys.argv:
        idx = sys.argv.index("--event")
        if idx + 1 >= len(sys.argv):
            print(f"Usage: evolve.py --event <name>")
            print(f"Available events: {list(EVENTS)}")
            sys.exit(1)
        event_name = sys.argv[idx + 1]
        try:
            events.fire(event_name, genomes)
            print(f"Fired event: {event_name}")
            lines, mode_name = build_session(genomes, MODES[nearest_mode(genomes)[0]])
            send_all(lines)
            save_all(genomes, events)
        except ValueError as e:
            print(e)
            sys.exit(1)

    else:
        print(f"eul evolve v2: full every {INTERVAL_MINUTES}min, micro every 30s. Ctrl+C to stop.")
        genomes, events = evolve(genomes, events)
        last_full = time.time()
        while True:
            time.sleep(30)
            if time.time() - last_full >= INTERVAL_MINUTES * 60:
                genomes, events = evolve(genomes, events)
                last_full = time.time()
            else:
                genomes, events = micro_evolve(genomes, events)
