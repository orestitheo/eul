# eul — Generative Music Radio

## Project
An always-on internet radio station for Demea (Oresti Theodoridis), experimental electronic musician from Malmö, Sweden. Streams 24/7 at `http://204.168.163.80:8000/stream`. Self-evolving — patterns change automatically every 3 minutes (full), with micro-tweaks every 30 seconds.

## Stack
```
TidalCycles (patterns) → SuperCollider/SuperDirt (audio) → JACK (routing) → DarkIce (encoder) → Icecast (HTTP stream)
```
- **TidalCycles** — Haskell pattern language, runs in ghci. Channels d1–d6.
- **SuperDirt** — SuperCollider quark, handles sample playback and effects
- **JACK** — headless virtual audio routing (dummy driver, no soundcard)
- **DarkIce** — encodes JACK audio to MP3 192kbps
- **Icecast** — serves HTTP stream on port 8000
- **scripts/eul/** — genetic self-evolving composer package (replaces old evolve.py)

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
| d1 | Drone — always on |
| d2 | Texture — cycles in/out |
| d3 | t99 melodic layer — during chord window |
| d4 | Drums — whenmod gated, never overlaps chords |
| d5 | Voice — during chord window |
| d6 | Chords — whenmod gated, never overlaps drums |

## Genetic composer (scripts/eul/)
The composer is a Python package with four modules:

- **genes.py** — 30 float genes [0,1] covering tempo, drum density/timing, chord style, texture, melodic intervals, voice. Mutate each full evolve (gaussian nudge + occasional big jump). Persist to `/opt/eul/state/genes.json`.
- **modes.py** — 7 mode attractors (`minimal`, `sparse`, `percussive`, `melodic`, `full`, `balanced`, `glitch`). Each is a partial gene dict. System finds nearest mode each evolve and nudges toward it — gravitational pull, not a hard snap.
- **patterns.py** — pattern builders driven entirely by genes. Drum sequences are algorithmic (euclidean hits, slice bias, rest probability). All samples use `# begin` for random start points.
- **evolve.py** — main loop: mutate → find nearest mode → nudge → build patterns → send → save.

**Full evolve** (every 3 min): mutates all genes, picks new mode attractor, rebuilds all layers.
**Micro evolve** (every 30s): small gene nudge, varies drum rhythm within same bank, nudges gains/filters only — does not retrigger long samples.

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
- After SC restarts, always reconnect JACK and run evolve --once

## Key commands
```bash
./scripts/status.sh                      # check all services
./scripts/evolve.sh                      # trigger full evolution
./scripts/evolve.sh --micro              # trigger micro evolution
./scripts/evolve.sh --print              # print current gene state + nearest mode
./scripts/audition.sh                    # interactive gain mixer
./scripts/add-samples.sh <folder>        # add new sample bank (full workflow)
./scripts/normalize-samples.sh <folder>  # compress/normalize samples
./scripts/fade-samples.sh <folder>       # add fade-in/out to remove clicks
```

## SuperDirt quirks
- **loopAt + note together silences the sample** — SuperDirt bug. Use one or the other.
- **Drums always need `# room 0`** — SuperDirt global reverb bleeds into drums otherwise.
- **JACK routing breaks on every SC restart** — ports named `darkice-{PID}:left/right`. add-samples.sh reconnects automatically.
- **`# begin`** — sets playback start point (0.0–1.0). Used on all long samples so each session starts at a different point.

## Sample banks
| Bank | Path | Role |
|------|------|------|
| `drone` | `samples/drone/` | d1 — always on |
| `texture` | `samples/texture/` | d2 — cycles in/out |
| `t99` | `samples/melodic/chords/t99/` | d3 — melodic |
| `dungeondrums` | `samples/percussive/dungeondrums/` | d4 — drums |
| `rad` | `samples/percussive/rad/` | d4 — drums |
| `shxc1` | `samples/percussive/shxc1/` | d4 — drums |
| `ls` | `samples/melodic/chords/ls/` | d6 — chords |
| `akatosh_chord` | `samples/melodic/chords/akatosh_chord/` | d6 — chords |
| `blackmirror` | `samples/melodic/chords/blackmirror/` | d6 — chords |
| `discoveryone` | `samples/melodic/chords/discoveryone/` | d6 — chords |
| `shxc` | `samples/melodic/chords/shxc/` | d6 — chords |
| `madonna` | `samples/melodic/singletone/madonna/` | d5 — voice |
| `akatosh_voice` | `samples/melodic/singletone/akatosh_voice/` | d5 — voice |
| `discoveryone` | `samples/melodic/singletone/discoveryone/` | d5 — voice |

## Git
Remote: git@github.com:orestitheo/eul.git (SSH)
Short commit messages, don't credit yourself.
