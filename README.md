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
- **evolve.py** — Python script that runs every 30 minutes, generates new pattern lines and sends them to the REPL automatically

---

## Adding new samples (full workflow)

1. **Drop files** into the right subfolder under `samples/`:
   ```
   samples/
     drone/              — sustained tones, pads, anything long and ambient
     texture/            — field recordings, noise, found sounds
     percussive/         — one subfolder per kit (e.g. percussive/mykick/)
     melodic/chords/     — one subfolder per chord set (e.g. melodic/chords/mypack/)
     melodic/singletone/ — one subfolder for voice/single tone sources
   ```
   Each subfolder = one bank name in TidalCycles. So `percussive/mykick/` = `sound "mykick"`.

2. **Rename** (strips timestamps, lowercases, fixes spaces):
   ```bash
   ./scripts/rename-samples.sh
   ```

3. **Commit and push**:
   ```bash
   git add samples/ && git commit -m "add new samples" && git push
   ```

4. **Sync to server + register bank + restart SuperDirt**:
   ```bash
   ./scripts/add-samples.sh samples/path/to/yourfolder
   # e.g: ./scripts/add-samples.sh samples/percussive/mykick
   ```
   This rsyncs the folder, adds it to the SuperDirt boot config, and restarts SuperCollider (~25s to reload).

5. **Add the new bank to the evolve script** if you want it used in auto-evolution:
   - For chord banks: add samples to `CHORD_SAMPLES` in `scripts/evolve.py`
   - For drum banks: add to `DRUM_BANKS`
   - For voice: add to `VOICE_SAMPLES`
   Then rsync the updated script: `rsync -avz scripts/evolve.py root@204.168.163.80:/opt/eul/scripts/evolve.py`

---

## Changing patterns (live, immediate)

SSH in and type directly into the TidalCycles REPL:

```bash
ssh root@204.168.163.80
tmux attach -t eul
# Ctrl+b then 5  →  TidalCycles REPL (tidal> prompt)
```

Each line replaces one channel instantly on the next cycle. Everything else keeps playing.

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

## Self-evolution (evolve.py)

The engine evolves itself via `scripts/evolve.py` running in tmux window 6. Full evolution every 6 minutes (new mode, new samples, new patterns). Micro-evolution every 60 seconds (nudges gains, filter sweeps, speeds).

**What it randomises each session:**
- Tempo range (always slow perlin drift, within 0.5–1.2 cps)
- Drone filter range and sweep speed
- Texture on/off timing
- Drum bank (dungeondrums or rad), random slice selection
- Chord samples (random subset from all melodic banks)
- `whenmod` ratios — how long drums vs chords sections last
- Whether voice appears (coin flip), which voice sample, how slow
- Whether glitch fires at all

**Rules it never breaks:**
- Drone always on
- Drums and chords never overlap
- Voice only during chord sections
- Max 3 layers active at once
- No bitcrush on chords or drums

**Trigger a manual evolution:**
```bash
ssh root@204.168.163.80 "python3 /opt/eul/scripts/evolve.py --once"   # full evolve
ssh root@204.168.163.80 "python3 /opt/eul/scripts/evolve.py --micro"  # micro evolve
```

**Restart the evolve loop** (after server restart or crash):
```bash
ssh root@204.168.163.80
tmux send-keys -t eul:6 'python3 -u /opt/eul/scripts/evolve.py 2>&1 | tee /var/log/eul/evolve.log' Enter
```

---

## Scripts

| Script | Usage | What it does |
|--------|-------|-------------|
| `./scripts/rename-samples.sh` | After adding files | Strips timestamps, lowercases, fixes spaces |
| `./scripts/add-samples.sh <folder>` | After rename + commit | Syncs folder, registers bank, restarts SuperDirt |
| `./scripts/sync-patterns.sh` | After editing patterns | Pushes pattern file to server |
| `./scripts/status.sh` | Anytime | Checks all processes, stream, JACK routing, loaded banks |

---

## Restarting everything

If the stream goes down:

```bash
ssh root@204.168.163.80
bash /opt/eul/setup/start.sh
# wait ~30 seconds for SuperDirt to boot
tmux attach -t eul
# Ctrl+b 5 — TidalCycles REPL, run evolve.py --once to restore patterns
python3 /opt/eul/scripts/evolve.py --once
# Ctrl+b 6 — restart evolve loop
python3 -u /opt/eul/scripts/evolve.py 2>&1 | tee /var/log/eul/evolve.log
```

---

## Checking stream health

```bash
./scripts/status.sh
```

Or manually:
```bash
curl -I http://204.168.163.80:8000/stream
# 200 = live, anything else = Icecast down
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

## Sample banks

| Bank | Path | Contents | Used as |
|------|------|----------|---------|
| `drone` | `samples/drone/` | Whitney Dark Choir, cataamb2 | d1 — always on |
| `texture` | `samples/texture/` | disconeblip, droid11, droid14, catafx7, rain | d2 — cycles in/out |
| `t99` | `samples/melodic/chords/t99/` | 1 sample | d3 — looped ambient layer, seconds+fifths |
| `dungeondrums` | `samples/percussive/dungeondrums/` | 14 slices | d4 — drums |
| `rad` | `samples/percussive/rad/` | 37 slices | d4 — drums |
| `shxc1` | `samples/percussive/shxc1/` | 15 slices | d4 — drums |
| `discoveryone` (voice) | `samples/melodic/singletone/discoveryone/` | 1 sample | d5 — voice |
| `akatosh` (voice) | `samples/melodic/singletone/akatosh/` | 1 sample | d5 — voice |
| `madonna` | `samples/melodic/singletone/madonna/` | Frozen acapella | d5 — voice |
| `ls` | `samples/melodic/chords/ls/` | 9 chord WAVs | d6 — chords |
| `discoveryone` | `samples/melodic/chords/discoveryone/` | bridge pad | d6 — chords |
| `akatosh` | `samples/melodic/chords/akatosh/` | 2 chord WAVs | d6 — chords |
| `blackmirror` | `samples/melodic/chords/blackmirror/` | 1 sample | d6 — chords |
| `shxc` | `samples/melodic/chords/shxc/` | 1 sample | d6 — chords |
