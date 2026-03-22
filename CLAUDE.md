# eul — Generative Music Radio

## Project
An always-on internet radio station for Demea (Oresti Theodoridis), experimental electronic musician from Malmö, Sweden. Streams 24/7 at `http://204.168.163.80:8000/stream`. Self-evolving — patterns change automatically every 6 minutes, with micro-tweaks every 60 seconds.

## Stack
```
TidalCycles (patterns) → SuperCollider/SuperDirt (audio) → JACK (routing) → DarkIce (encoder) → Icecast (HTTP stream)
```
- **TidalCycles** — Haskell pattern language, runs in ghci. Channels d1–d6.
- **SuperDirt** — SuperCollider quark, handles sample playback and effects
- **JACK** — headless virtual audio routing (dummy driver, no soundcard)
- **DarkIce** — encodes JACK audio to MP3 192kbps
- **Icecast** — serves HTTP stream on port 8000
- **evolve.py** — Python script, self-evolves patterns every 6 min + micro-evolve every 60s

## Server
- IP: 204.168.163.80
- Provider: Hetzner CPX22
- OS: Ubuntu 24.04
- SSH: `ssh root@204.168.163.80`
- Logs: `/var/log/eul/`

## tmux windows
| Window | Process |
|--------|---------|
| 0 | Xvfb (virtual display for sclang) |
| 1 | JACK |
| 2 | SuperCollider + SuperDirt |
| 3 | Icecast |
| 4 | DarkIce |
| 5 | TidalCycles REPL |
| 6 | evolve.py loop |

## Pattern channels
| Channel | Role |
|---------|------|
| d1 | Drone — always on |
| d2 | Texture — cycles in/out |
| d3 | t99 melodic layer — during chord window |
| d4 | Drums — whenmod gated |
| d5 | Voice — during chord window |
| d6 | Chords — whenmod gated, never overlaps drums |

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

## Rules
- Don't over-engineer
- Short commit messages, don't credit yourself
- Explain TidalCycles concepts briefly as you use them — Oresti is a SW engineer (6 years, AI/backend) but new to this domain
- Keep it playful, not academic
- Always rsync evolve.py to server after changes and run --once to apply immediately
- After SC restarts, always reconnect JACK and run evolve --once

## Key commands
```bash
./scripts/status.sh                    # check all services
./scripts/evolve.sh                    # trigger full evolution
./scripts/evolve.sh --micro            # trigger micro evolution
./scripts/audition.sh                  # interactive gain mixer
./scripts/add-samples.sh <folder>      # add new sample bank (full workflow)
./scripts/normalize-samples.sh <folder> # compress/normalize samples
./scripts/fade-samples.sh <folder>     # add fade-in/out to remove clicks
```

## Git
Remote: git@github.com:orestitheo/eul.git (SSH)
Short commit messages, don't credit yourself.
