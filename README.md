# eul

Always-on generative music radio station. Streams 24/7 at `http://204.168.163.80:8000/stream`.

## How it works

```
TidalCycles (patterns) → SuperCollider/SuperDirt (audio engine) → JACK (routing) → DarkIce (encoder) → Icecast (HTTP stream)
```

- **TidalCycles** — pattern language. Each `d1`–`d6` line is one audio channel.
- **SuperDirt** — loads your samples, handles effects (reverb, delay, filters, etc.)
- **JACK** — virtual audio cable between SuperCollider and DarkIce (headless, no soundcard needed)
- **DarkIce** — encodes the JACK audio to MP3 192kbps
- **Icecast** — serves it as an HTTP stream
- **scripts/eul/** — genetic self-evolving composer. Mutates every 3 minutes (full) and every 30 seconds (micro-tweaks).

---

## Scripts

| Script | Usage | What it does |
|--------|-------|-------------|
| `./scripts/status.sh` | Anytime | Checks all processes, stream, JACK routing, loaded banks |
| `./scripts/evolve.sh` | Anytime | Triggers a full pattern evolution on the server |
| `./scripts/evolve.sh --micro` | Anytime | Triggers a micro evolution (gains/filters/drum rhythm) |
| `./scripts/evolve.sh --print` | Anytime | Prints current gene state and nearest mode |
| `./scripts/audition.sh` | When tuning gains | Interactive mixer — play banks, adjust gains, get report |
| `./scripts/add-samples.sh <folder>` | After adding samples | Full workflow: rename, sync, register, restart SC, update evolve.py |
| `./scripts/normalize-samples.sh <folder>` | After adding melodic samples | Compress + normalize to consistent loudness |
| `./scripts/fade-samples.sh <folder>` | After adding percussive samples | Add short fade-in/out to prevent clicks |

---

## Genetic composer

The engine evolves itself via `scripts/eul/` running in tmux window 6.

```
scripts/eul/
  genes.py     — 30 float genes [0,1]: tempo, drum structure, chord style, texture, melody, voice
  modes.py     — 7 mode attractors: minimal, sparse, percussive, melodic, full, balanced, glitch
  patterns.py  — pattern builders driven entirely by genes (no hardcoded sequences)
  send.py      — tmux → TidalCycles REPL
  evolve.py    — main loop: mutate → find nearest mode → nudge → build → send → save
```

**Full evolution** (every 3 min):
- All genes get a gaussian mutation nudge + occasional large jump
- System finds the nearest mode attractor and drifts toward it
- Rebuilds all layers from scratch

**Micro evolution** (every 30s):
- Small gene nudge only
- Varies drum rhythm within same bank (new sequence, step count, speed)
- Nudges gains and filter sweeps
- Does NOT retrigger long samples (chords, drone, texture play through)

**Gene state** persists to `/opt/eul/state/genes.json` — evolution survives server restarts.

### Modes

Modes are gravitational attractors, not hard switches. The system drifts toward the nearest one.

| Mode | Character |
|------|-----------|
| `minimal` | drone + texture only — pure ambient, no rhythm |
| `sparse` | drone + texture + chords, no drums |
| `percussive` | drone + drums only, no melody |
| `melodic` | drone + t99 + chords, no drums, voice optional |
| `full` | all layers active |
| `balanced` | all layers, nothing dominant |
| `glitch` | chaotic drums + texture, broken feel |

**Trigger manually:**
```bash
./scripts/evolve.sh           # full evolution
./scripts/evolve.sh --micro   # micro evolution
./scripts/evolve.sh --print   # show current genes + nearest mode
```

**Restart the evolve loop** (after server restart):
```bash
ssh root@204.168.163.80
tmux send-keys -t eul:6 'python3 -u /opt/eul/scripts/eul/evolve.py 2>&1 | tee /var/log/eul/evolve.log' Enter
```

---

## Adding new samples

1. **Drop files** into the right subfolder under `samples/`:
   ```
   samples/
     drone/                         — sustained tones, pads
     texture/                       — field recordings, noise, found sounds
     percussive/                    — one subfolder per kit (e.g. percussive/mykick/)
     melodic/chords/                — one subfolder per chord/pad set
     melodic/singletone/            — one subfolder per voice/melody source
   ```

2. **Run the full workflow:**
   ```bash
   ./scripts/add-samples.sh samples/path/to/yourfolder
   ```

3. **For melodic/chord samples**, normalize after adding:
   ```bash
   ./scripts/normalize-samples.sh samples/path/to/yourfolder
   ```

4. **Commit and push:**
   ```bash
   git add samples/ scripts/eul/ && git commit -m "add samples" && git push
   ```

---

## Audition tool

Interactive mixer for calibrating gain levels per sample bank:

```bash
./scripts/audition.sh
```

Commands inside audition:
```
play <bank>       add bank to mix (supports bank:index e.g. drone:1)
stop <bank>       remove bank
stop all          hush everything
gain <bank> <n>   set gain
+ / -             nudge last touched bank
r                 replay all active layers
list              show all banks
report            print final gain table
q                 quit and print report
```

---

## Sample banks

| Bank | Path | Contents | Role |
|------|------|----------|------|
| `drone` | `samples/drone/` | Whitney Dark Choir (x2), cataamb2 | d1 — always on |
| `texture` | `samples/texture/` | catafx7, disconeblip, droid11, droid14, rain | d2 — cycles in/out |
| `t99` | `samples/melodic/chords/t99/` | 1 sample | d3 — melodic |
| `dungeondrums` | `samples/percussive/dungeondrums/` | 14 slices | d4 — drums |
| `rad` | `samples/percussive/rad/` | 37 slices | d4 — drums |
| `shxc1` | `samples/percussive/shxc1/` | 15 slices | d4 — drums |
| `ls` | `samples/melodic/chords/ls/` | 9 chord WAVs | d6 — chords |
| `akatosh_chord` | `samples/melodic/chords/akatosh_chord/` | 2 chord WAVs | d6 — chords |
| `blackmirror` | `samples/melodic/chords/blackmirror/` | 1 sample | d6 — chords |
| `discoveryone` | `samples/melodic/chords/discoveryone/` | 1 pad WAV | d6 — chords |
| `shxc` | `samples/melodic/chords/shxc/` | 1 sample | d6 — chords |
| `madonna` | `samples/melodic/singletone/madonna/` | Frozen acapella | d5 — voice |
| `akatosh_voice` | `samples/melodic/singletone/akatosh_voice/` | 1 sample | d5 — voice |
| `discoveryone` | `samples/melodic/singletone/discoveryone/` | 1 sample | d5 — voice |

---

## Server

- **IP:** 204.168.163.80
- **Provider:** Hetzner CPX22 (~€8/mo)
- **OS:** Ubuntu 24.04
- **SSH:** `ssh root@204.168.163.80`
- **Logs:** `/var/log/eul/` — jack, superdirt, icecast, darkice, evolve
- **Gene state:** `/opt/eul/state/genes.json`

## tmux windows

| Window | What's running |
|--------|---------------|
| 0 | Xvfb (virtual display for sclang Qt) |
| 1 | JACK (virtual audio routing) |
| 2 | SuperCollider + SuperDirt |
| 3 | Icecast |
| 4 | DarkIce |
| 5 | **TidalCycles REPL ← work here** |
| 6 | evolve loop (genetic composer) |

Navigate: `Ctrl+b` + window number. Detach without stopping: `Ctrl+b d`.

---

## Checking stream health

```bash
./scripts/status.sh
```

Or manually:
```bash
curl -I http://204.168.163.80:8000/stream
# 200 = live
```

---

## Restarting everything

If the stream goes down:

```bash
ssh root@204.168.163.80
bash /opt/eul/setup/start.sh
# wait ~30 seconds for SuperDirt to boot
```

Then restore patterns:
```bash
./scripts/evolve.sh
```
