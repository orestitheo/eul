# eul

Always-on generative music radio station. Streams 24/7 at `http://204.168.163.80:8000/stream`.

## How it works

```
TidalCycles (patterns) → SuperCollider/SuperDirt (audio engine) → JACK (routing) → DarkIce (encoder) → Icecast (HTTP stream)
```

- **TidalCycles** — pattern language. Each `d1`–`d6` line is one audio channel. Send a new line, it changes immediately on the next cycle.
- **SuperDirt** — loads your samples, handles effects (reverb, delay, filters, etc.)
- **JACK** — virtual audio cable between SuperCollider and DarkIce (headless, no soundcard needed)
- **DarkIce** — encodes the JACK audio to MP3 192kbps
- **Icecast** — serves it as an HTTP stream
- **evolve.py** — self-evolves patterns every 6 minutes (full) and every 60 seconds (micro-tweaks)

---

## Scripts

| Script | Usage | What it does |
|--------|-------|-------------|
| `./scripts/status.sh` | Anytime | Checks all processes, stream, JACK routing, loaded banks |
| `./scripts/evolve.sh` | Anytime | Triggers a full pattern evolution on the server |
| `./scripts/evolve.sh --micro` | Anytime | Triggers a micro evolution (gains/filters only) |
| `./scripts/audition.sh` | When tuning gains | Interactive mixer — play banks, adjust gains, get report |
| `./scripts/add-samples.sh <folder>` | After adding samples | Full workflow: rename, sync, register, restart SC, update evolve.py |
| `./scripts/normalize-samples.sh <folder>` | After adding melodic samples | Compress + normalize to consistent loudness |
| `./scripts/fade-samples.sh <folder>` | After adding percussive samples | Add short fade-in/out to prevent clicks |
| `./scripts/rename-samples.sh` | Manually if needed | Strips timestamps, lowercases, fixes spaces |
| `./scripts/sync-patterns.sh` | After editing patterns | Pushes pattern file to server |

---

## Adding new samples

1. **Drop files** into the right subfolder under `samples/`:
   ```
   samples/
     drone/                    — sustained tones, pads
     texture/                  — field recordings, noise, found sounds
     percussive/               — one subfolder per kit (e.g. percussive/mykick/)
     melodic/chords/           — one subfolder per chord/pad set
     melodic/singletone/       — one subfolder per voice/melody source
   ```
   Each subfolder = one bank name in TidalCycles. So `percussive/mykick/` = `sound "mykick"`.

2. **Run the full workflow:**
   ```bash
   ./scripts/add-samples.sh samples/path/to/yourfolder
   ```
   This renames files, rsyncs to server, registers the bank in SuperDirt, restarts SuperCollider (~25s), reconnects JACK, restores patterns, and adds the bank to evolve.py automatically.

3. **For melodic/chord samples**, normalize after adding:
   ```bash
   ./scripts/normalize-samples.sh samples/path/to/yourfolder
   ```

4. **Commit and push:**
   ```bash
   git add samples/ scripts/evolve.py && git commit -m "add samples" && git push
   ```

---

## Self-evolution (evolve.py)

The engine evolves itself via `scripts/evolve.py` running in tmux window 6.

- **Full evolution** every 6 minutes — new mode, new samples, new patterns
- **Micro evolution** every 60 seconds — nudges gains, filter sweeps, texture speed

**Modes** bias what's prominent each session: `drums`, `chords`, `drone`, `glitch`, `balanced`

**Rules it never breaks:**
- Drone always on (d1)
- Drums and chords never overlap (complementary whenmod windows)
- Voice only during chord sections
- t99 melodic layer synced to chord window

**Trigger manually:**
```bash
./scripts/evolve.sh           # full evolution
./scripts/evolve.sh --micro   # micro evolution
```

**Restart the evolve loop** (after server restart or crash):
```bash
ssh root@204.168.163.80
tmux send-keys -t eul:6 'python3 -u /opt/eul/scripts/evolve.py 2>&1 | tee /var/log/eul/evolve.log' Enter
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
status            show active layers with gain bars
report            print final gain table
q                 quit and print report
```

---

## Changing patterns (live)

SSH in and type directly into the TidalCycles REPL:

```bash
ssh root@204.168.163.80
tmux attach -t eul
# Ctrl+b then 5  →  TidalCycles REPL (tidal> prompt)
```

```haskell
-- Change a layer
d1 $ sound "drone:0" # gain 0.8 # room 0.9

-- Silence one layer
d3 silence

-- Stop everything
hush
```

Save good patterns back to `patterns/main.tidal` and commit.

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

---

## Server

- **IP:** 204.168.163.80
- **Provider:** Hetzner CPX22 (~€8/mo)
- **OS:** Ubuntu 24.04
- **SSH:** `ssh root@204.168.163.80`
- **Logs:** `/var/log/eul/` — jack, superdirt, icecast, darkice, evolve

## tmux windows

| Window | What's running |
|--------|---------------|
| 0 | Xvfb (virtual display for sclang Qt) |
| 1 | JACK (virtual audio routing) |
| 2 | SuperCollider + SuperDirt |
| 3 | Icecast |
| 4 | DarkIce |
| 5 | **TidalCycles REPL ← work here** |
| 6 | evolve.py (auto-composer) |

Navigate: `Ctrl+b` + window number. Detach without stopping: `Ctrl+b d`.

---

## Sample banks

| Bank | Path | Contents | Role |
|------|------|----------|------|
| `drone` | `samples/drone/` | Whitney Dark Choir (x2), cataamb2 | d1 — always on |
| `texture` | `samples/texture/` | catafx7, disconeblip, droid11, droid14, rain | d2 — cycles in/out |
| `t99` | `samples/melodic/chords/t99/` | 1 sample | d3 — looped melodic, intervals |
| `dungeondrums` | `samples/percussive/dungeondrums/` | 14 slices | d4 — drums |
| `rad` | `samples/percussive/rad/` | 37 slices | d4 — drums |
| `shxc1` | `samples/percussive/shxc1/` | 15 slices | d4 — drums |
| `discoveryone` (voice) | `samples/melodic/singletone/discoveryone/` | 1 sample | d5 — voice |
| `akatosh` (voice) | `samples/melodic/singletone/akatosh/` | 1 sample | d5 — voice |
| `madonna` | `samples/melodic/singletone/madonna/` | Frozen acapella | d5 — voice |
| `ls` | `samples/melodic/chords/ls/` | 9 chord WAVs | d6 — chords |
| `akatosh` | `samples/melodic/chords/akatosh/` | 1 chord WAV | d6 — chords |
| `discoveryone` | `samples/melodic/chords/discoveryone/` | 1 pad WAV | d6 — chords |
| `blackmirror` | `samples/melodic/chords/blackmirror/` | 1 sample | d6 — chords |
| `shxc` | `samples/melodic/chords/shxc/` | 1 sample | d6 — chords |
