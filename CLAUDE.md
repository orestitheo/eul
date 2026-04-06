# eul — Generative Music Radio

## Project
An always-on internet radio station for Demea (Oresti Theodoridis), experimental electronic musician from Malmö, Sweden. Streams 24/7 at `http://204.168.163.80:8000/stream`. Self-evolving — each sound domain evolves on its own clock, falling in and out of phase.

## Stack
```
TidalCycles (patterns) → SuperCollider/SuperDirt (audio) → JACK (routing) → DarkIce (encoder) → Icecast (HTTP stream)
```
- **TidalCycles** — Haskell pattern language, runs in ghci. Channels d1–d6.
- **SuperDirt** — SuperCollider quark, handles sample playback and effects
- **JACK** — headless virtual audio routing (dummy driver, no soundcard)
- **DarkIce** — encodes JACK audio to MP3 192kbps
- **Icecast** — serves HTTP stream on port 8000
- **scripts/eul/** — genetic self-evolving composer package

## Server
- IP: 204.168.163.80
- Provider: Hetzner CPX22
- OS: Ubuntu 24.04
- SSH: `ssh root@204.168.163.80`
- Logs: `/var/log/eul/`
- Gene state: `/opt/eul/state/genes.json`

## tmux windows
| Window | Process |
|--------|---------|
| 0 | Xvfb (virtual display for sclang) |
| 1 | JACK |
| 2 | SuperCollider + SuperDirt |
| 3 | Icecast |
| 4 | DarkIce |
| 5 | TidalCycles REPL |
| 6 | evolve loop (`python3 -u /opt/eul/scripts/eul/evolve.py`) |

## Pattern channels
| Channel | Role |
|---------|------|
| d1 | Drone — gene-gated, can silence for stretches |
| d2 | Texture — cycles in/out |
| d3 | Melodic layer — non-looping chord banks (t99, shxc), during chord window |
| d4 | Drums — whenmod gated, never overlaps chords |
| d5 | Voice — during chord window |
| d6 | Chords — looping pads + non-looping banks, whenmod gated |

## Genetic composer (scripts/eul/)
The composer is a Python package. Each sound domain is a separate genetic path with its own mutation rate.

- **genome.py** — `GenomePath` base class. All domain genomes extend this. Genes are floats [0,1] mapped to real ranges via `.map()`. Methods: `mutate`, `nudge_toward` (mode pull), `apply_override` (event snap).
- **genomes/** — one file per domain:
  - `drone.py` — `DroneGenome` (rate=0.06, slow drift)
  - `texture.py` — `TextureGenome` (rate=0.10)
  - `percussive.py` — `PercussiveGenome` (rate=0.18, most volatile)
  - `melodic.py` — `MelodicGenome` (rate=0.10, covers d3+d5+d6)
  - `global_.py` — `GlobalGenome` (rate=0.08, tempo + complexity)
- **banks.py** — single registry of all sample banks. Add a bank or rename a folder here only. Looping flag on chord banks protects long pads from staccato/glitch slicing.
- **grammar.py** — gene-driven TidalCycles backbone transforms. `pick_transforms(chaos, complexity, pool)` selects from a weighted pool (`scramble`, `chunk`, `palindrome`, `iter`, `every N rev`, etc). Drums get the full destructive pool; chords get a tame subset.
- **modes.py** — 7 mode attractors with domain-namespaced gene targets. `nearest_mode(genomes)` computes distance across all domains.
- **patterns.py** — pattern builders, one per channel. Takes genome objects. Calls `grammar.py` for drum/chord backbone.
- **events.py** — world events: sudden global shifts that override genes across multiple domains. `EventManager.tick()` called each full evolve. Add new events in `EVENTS` dict — no core code changes needed. Tune probabilities in `EVENT_PROBABILITIES` at top of file.
- **evolve.py** — main loop: each domain evolves on its own clock → mode pull → world events → build → send → save.

**Domain clocks** (tunable in `DOMAIN_INTERVALS`):
| Domain | Clock | Mutation rate | Controls |
|--------|-------|--------------|---------|
| `percussive` | 90s | 0.18 | drums — rhythm, bank crossfade, chaos |
| `texture` | 4min | 0.10 | atmospheric layer — density, speed, samples |
| `melodic` | 5min | 0.10 | chords, t99, voice — pitch, rhythm, delay |
| `global` | 6min | 0.08 | tempo, complexity, randomness |
| `drone` | 8min | 0.06 | foundation — gain, filter sweep, pitch |

Main loop ticks every 30s, checks which domains are due, mutates only those, rebuilds all patterns if anything changed.

### World events
| Event | Character | Duration |
|-------|-----------|----------|
| `crunch` | high drum chaos, boost complexity, dry drone | 1–3 evolves |
| `dissolve` | sparse drums, wet reverb everything, low complexity | 2–4 evolves |
| `storm` | max drum chaos + density, fast tempo, chaotic texture | 1–2 evolves |
| `silence` | near-silence, slow tempo, minimal everything | 1–2 evolves |
| `glitch_burst` | full chaos on drums + texture, 1 evolve only | 1 evolve |
| `harmonic_shift` | randomize interval genes + drone pitch | 2–5 evolves |

Fire manually: `./scripts/evolve.sh --event <name>`
Tune probability: edit `EVENT_PROBABILITIES` in `events.py` (set to `1.0` to force next tick).

## Modes
| Mode | Character |
|------|-----------|
| minimal | drone + texture only, pure ambient |
| sparse | drone + texture + chords, no drums |
| percussive | drone + drums only, no melody |
| melodic | drone + t99 + chords, no drums |
| full | all layers |
| balanced | all layers, nothing dominant |
| glitch | chaotic drums + texture, broken feel |

## You are an expert in
- TidalCycles pattern syntax and SuperDirt effects
- Generative/algorithmic music composition
- SuperCollider, JACK, Icecast, DarkIce setup and operation
- Building always-on ambient/generative music systems

## Artist context
- Artist name: Demea — experimental electronic, samples, noise
- Main site: demea.xyz (separate repo: github.com/orestitheo/oresti-xyz)
- Music style: ambient, textural, slowly evolving, occasional beats
- Album SYN on Bandcamp (dmea.bandcamp.com)

## SSH access
Claude has full SSH access to the server at `root@204.168.163.80`. Always apply changes directly:
- Edit package locally → `rsync -az scripts/eul/ root@204.168.163.80:/opt/eul/scripts/eul/` → `ssh root@204.168.163.80 "python3 /opt/eul/scripts/eul/evolve.py --once"`
- Never ask Oresti to run commands manually unless it requires interactive input

## Rules
- Don't over-engineer
- Short commit messages, don't credit yourself
- Explain TidalCycles concepts briefly as you use them — Oresti is a SW engineer (6 years, AI/backend) but new to this domain
- Keep it playful, not academic
- Always rsync scripts/eul/ to server after changes and run --once to apply immediately
- Adding a new sample bank: one entry in `banks.py` BANKS dict, then rsync + --once. No other code changes.
- After SC restarts, always reconnect JACK and run evolve --once

## Key commands
```bash
./scripts/status.sh                      # check all services
./scripts/evolve.sh                      # trigger full evolution
./scripts/evolve.sh --micro              # trigger micro evolution
./scripts/evolve.sh --print              # print current gene state + nearest mode
./scripts/evolve.sh --event <name>       # manually fire a world event
./scripts/audition.sh                    # interactive gain mixer
./scripts/add-samples.sh <folder>        # add new sample bank (full workflow)
./scripts/normalize-samples.sh <folder>  # compress/normalize samples
./scripts/fade-samples.sh <folder>       # add fade-in/out to remove clicks
```

## SuperDirt quirks
- **loopAt + note together silences the sample** — SuperDirt bug. Use one or the other.
- **loopAt silences long samples** — avoid loopAt entirely for long pads; use `# sustain N` instead.
- **`ls` is a reserved TidalCycles identifier** — never name a sample bank `ls`, it conflicts with a Haskell built-in and silences the bank.
- **SuperDirt needs 6 orbits** — `~dirt.start(57120, [0, 0, 0, 0, 0, 0])` in startup.scd. d1–d6 = orbits 0–5. Default `[0,0]` silences d3–d6.
- **Drums always need `# room 0`** — SuperDirt global reverb bleeds into drums otherwise.
- **JACK routing breaks on every SC restart** — ports named `darkice-{PID}:left/right`. add-samples.sh reconnects automatically.
- **`# begin`** — sets playback start point (0.0–1.0). Used on all long samples so each session starts at a different point.
- **Long pads use `# loopAt N`** — loops the sample every N cycles.

## Sample banks

Banks are registered in `banks.py` using a strain class hierarchy. Strain defines defaults; banks override only what differs. Adding a new bank = one line in `BANKS`.

### Strains
| Strain | Channel | Key rules | Looping default |
|--------|---------|-----------|----------------|
| `Drone` | d1 | — | yes |
| `Texture` | d2 | exclusive | yes |
| `Chord` | d3/d6 | exclusive | yes |
| `Voice` | d5 | exclusive | no |
| `Drum` | d4 | — | no |

`exclusive` = only one bank of this strain plays at a time. Rules are declarative tags on the class.

### Banks
| Bank | Strain | Path | Notes |
|------|--------|------|-------|
| `drone` | Drone | `samples/drone/` | 3 samples |
| `texture` | Texture | `samples/texture/` | 5 samples |
| `akatosh_chord` | Chord | `samples/melodic/chords/akatosh_chord/` | looping |
| `blackmirror` | Chord | `samples/melodic/chords/blackmirror/` | looping, 18s pad |
| `discoveryone` | Chord | `samples/melodic/chords/discoveryone/` | looping |
| `shxc` | Chord | `samples/melodic/chords/shxc/` | looping=False, can glitch/stab |
| `t99` | Chord | `samples/melodic/chords/t99/` | looping=False, pitched melodic |
| `madonna` | Voice | `samples/melodic/singletone/madonna/` | |
| `akatosh_voice` | Voice | `samples/melodic/singletone/akatosh_voice/` | |
| `discoveryone_voice` | Voice | `samples/melodic/singletone/discoveryone/` | |
| `rad` | Drum | `samples/percussive/rad/` | 37 slices |
| `shxc1` | Drum | `samples/percussive/shxc1/` | 15 slices |

## Git
Remote: git@github.com:orestitheo/eul.git (SSH)
Short commit messages, don't credit yourself.
