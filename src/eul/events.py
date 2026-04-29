"""
events.py — world events for the eul genetic composer.

World events are sudden global shifts that override genes across multiple
domains simultaneously. They fire probabilistically on each full evolve,
last for a configured number of evolve ticks, then expire.

Adding a new event: one WorldEvent entry in EVENTS. No core code changes.

Tuning for testing: set EVENT_PROBABILITIES["crunch"] = 1.0 to force-trigger
next tick, then restore. Or use evolve.py --event <name> to fire manually.
"""

import random
from dataclasses import dataclass, field


# ── Probability overrides for testing ─────────────────────────────────────────
# Set any event to 1.0 to guarantee it fires next tick. Restore after testing.
EVENT_PROBABILITIES = {
    "crunch":          0.04,
    "dissolve":        0.05,
    "storm":           0.03,
    "silence":         0.04,
    "glitch_burst":    0.03,
    "harmonic_shift":  0.04,
}


@dataclass
class WorldEvent:
    name: str
    overrides: dict          # {"domain": {"gene": value}, ...}
    duration_range: tuple    # (min_evolves, max_evolves)
    cancels: list = field(default_factory=list)  # event names this cancels on trigger


EVENTS = {
    "crunch": WorldEvent(
        name="crunch",
        overrides={
            "percussive": {"chaos": 0.9, "density": 0.75},
            "global":     {"complexity": 0.85},
            "drone":      {"room": 0.15},
        },
        duration_range=(1, 3),
        cancels=["silence", "dissolve"],
    ),

    "dissolve": WorldEvent(
        name="dissolve",
        overrides={
            "percussive": {"density": 0.1, "chaos": 0.05},
            "drone":      {"gain": 0.95, "room": 0.95},
            "melodic":    {"chord_room": 0.9, "chord_delay_wet": 0.8},
            "global":     {"complexity": 0.15, "randomness": 0.15},
        },
        duration_range=(2, 4),
        cancels=["crunch", "storm"],
    ),

    "storm": WorldEvent(
        name="storm",
        overrides={
            "percussive": {"chaos": 0.95, "density": 0.9, "speed": 0.85, "rest_prob": 0.1},
            "global":     {"complexity": 0.95, "randomness": 0.9, "tempo_center": 0.75},
            "texture":    {"speed_rand": 0.95},
        },
        duration_range=(1, 2),
        cancels=["silence", "dissolve"],
    ),

    "silence": WorldEvent(
        name="silence",
        overrides={
            "drone":      {"gain": 0.55},
            "texture":    {"gain": 0.3, "density": 0.2},
            "percussive": {"density": 0.05, "rest_prob": 0.75},
            "global":     {"complexity": 0.05, "randomness": 0.1, "tempo_center": 0.15},
        },
        duration_range=(1, 2),
        cancels=["crunch", "storm"],
    ),

    "glitch_burst": WorldEvent(
        name="glitch_burst",
        overrides={
            "percussive": {"chaos": 1.0, "rest_prob": 0.6, "blend": 0.9, "density": 0.8},
            "global":     {"randomness": 1.0, "complexity": 1.0},
            "texture":    {"speed_rand": 1.0},
        },
        duration_range=(1, 1),
        cancels=[],
    ),

    "harmonic_shift": WorldEvent(
        name="harmonic_shift",
        overrides={
            # interval genes are randomized at fire time in EventManager.tick()
            "global":     {"complexity": 0.6},
            "drone":      {"room": 0.9},
        },
        duration_range=(2, 5),
        cancels=[],
    ),
}


class EventManager:
    """Tracks active world events and fires new ones each full evolve tick."""

    def __init__(self):
        self.active: dict = {}   # name -> evolves_remaining

    def tick(self, genomes: dict) -> str | None:
        """
        Call once per full evolve.
        1. Decrement active events, remove expired.
        2. Apply overrides from still-active events to genomes (in place).
        3. Maybe trigger a new event.
        Returns the name of a newly triggered event, or None.
        """
        # Expire finished events
        self.active = {n: rem - 1 for n, rem in self.active.items() if rem > 1}

        # Apply overrides from all active events
        for event_name in list(self.active):
            event = EVENTS[event_name]
            _apply_event(genomes, event)

        # Maybe trigger a new event
        triggered = None
        candidates = [
            (name, event) for name, event in EVENTS.items()
            if name not in self.active
        ]
        random.shuffle(candidates)
        for name, event in candidates:
            prob = EVENT_PROBABILITIES.get(name, 0.04)
            if random.random() < prob:
                for cancel in event.cancels:
                    self.active.pop(cancel, None)
                duration = random.randint(*event.duration_range)
                self.active[name] = duration
                overrides = dict(event.overrides)
                # Randomize interval genes for harmonic_shift at fire time
                if name == "harmonic_shift":
                    overrides["melodic"] = {
                        "voice_interval": round(random.random(), 3),
                        "chord_bank_pos": round(random.random(), 3),
                    }
                    overrides["drone"] = {"pitch": round(random.random(), 3), "room": 0.9}
                _apply_overrides(genomes, overrides)
                triggered = name
                break   # one new event per tick

        return triggered

    def fire(self, name: str, genomes: dict):
        """Manually trigger a named event (for --event CLI flag)."""
        if name not in EVENTS:
            raise ValueError(f"Unknown event: {name!r}. Available: {list(EVENTS)}")
        event = EVENTS[name]
        for cancel in event.cancels:
            self.active.pop(cancel, None)
        duration = random.randint(*event.duration_range)
        self.active[name] = duration
        overrides = dict(event.overrides)
        if name == "harmonic_shift":
            overrides["melodic"] = {
                "t99_interval":   round(random.random(), 3),
                "voice_interval": round(random.random(), 3),
            }
            overrides["drone"] = {"pitch": round(random.random(), 3), "room": 0.9}
        _apply_overrides(genomes, overrides)

    def to_dict(self) -> dict:
        return {"active": self.active}

    @classmethod
    def from_dict(cls, d: dict) -> "EventManager":
        obj = cls()
        obj.active = d.get("active", {})
        return obj

    def __repr__(self):
        if not self.active:
            return "EventManager: (no active events)"
        parts = ", ".join(f"{n}({r})" for n, r in self.active.items())
        return f"EventManager: {parts}"


def _apply_event(genomes: dict, event: WorldEvent):
    _apply_overrides(genomes, event.overrides)


def _apply_overrides(genomes: dict, overrides: dict):
    for domain, targets in overrides.items():
        if domain in genomes:
            genomes[domain] = genomes[domain].apply_override(targets)
