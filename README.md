# eul

Always-on generative music radio station. Streams 24/7 at `http://204.168.163.80:8000/stream`.

## How it works

```
TidalCycles (patterns) → SuperCollider/SuperDirt (audio engine) → JACK (routing) → DarkIce (encoder) → Icecast (HTTP stream)
```

- **TidalCycles** — you write patterns here, they play immediately
- **SuperDirt** — loads your samples, handles effects, synthesis
- **JACK** — virtual audio cable between SuperCollider and DarkIce
- **DarkIce** — encodes audio to MP3 192kbps
- **Icecast** — serves the stream over HTTP

---

## Workflows

### Adding new samples

1. Drop files into `samples/` in the right subfolder:
   ```
   samples/
     drone/        — long sustained tones, pads
     texture/      — field recordings, noise, ambience
     percussive/   — add a new subfolder per kit (e.g. percussive/mykick/)
     melodic/      — pitched material
   ```
2. Run the rename script to clean up filenames:
   ```bash
   ./scripts/rename-samples.sh
   ```
3. Sync to the server:
   ```bash
   rsync -avz samples/ root@204.168.163.80:/opt/eul/samples/
   ```
4. SSH in and reload SuperDirt so it picks up the new files:
   ```bash
   ssh root@204.168.163.80
   tmux attach -t eul
   # go to window 2 (SuperCollider): Ctrl+b then 2
   # press Ctrl+c to stop sclang, then restart it:
   DISPLAY=:99 QTWEBENGINE_CHROMIUM_FLAGS='--no-sandbox' sclang -D -i none >/var/log/eul/superdirt.log 2>&1
   ```
5. Add the new bank to `config/superdirt_boot.scd`:
   ```
   ~dirt.loadSoundFiles("/opt/eul/samples/percussive/mykick");
   ```
   Then rsync the config too:
   ```bash
   rsync -avz config/superdirt_boot.scd root@204.168.163.80:/root/.config/SuperCollider/startup.scd
   ```

---

### Changing patterns (live, immediate)

SSH into the server and send commands directly to the TidalCycles REPL:

```bash
ssh root@204.168.163.80
tmux attach -t eul
# Ctrl+b then 5  →  TidalCycles REPL
```

Type patterns at the `tidal>` prompt. They take effect on the next cycle (~1 second).

```haskell
-- Change a layer
d1 $ sound "drone:0" # gain 0.8 # room 0.9

-- Silence one layer
d3 silence

-- Stop everything
hush
```

When you're happy with a pattern, copy it back into `patterns/main.tidal` on your Mac and commit.

---

### Updating patterns from the repo

Edit `patterns/main.tidal` locally, commit, then paste the updated lines into the REPL:

```bash
# On your Mac — edit and commit
git add patterns/main.tidal && git commit -m "..." && git push

# Then SSH in and paste the new lines into the tidal> prompt
ssh root@204.168.163.80
tmux attach -t eul
# Ctrl+b 5, paste pattern lines
```

There's no auto-deploy of pattern changes — TidalCycles is a live coding environment, you're always typing directly into the REPL. The repo is just version control for patterns you want to keep.

---

### Restarting everything

If the stream goes down or something crashes:

```bash
ssh root@204.168.163.80
bash /opt/eul/setup/start.sh
# wait ~30 seconds for SuperDirt to boot
tmux attach -t eul
# Ctrl+b 5 — paste your patterns to resume
```

---

### Checking if the stream is up

```bash
curl -I http://204.168.163.80:8000/stream
# HTTP/1.0 200 OK = live
# connection refused = Icecast is down, restart
```

Or open `http://204.168.163.80:8000` in a browser — Icecast has a status page.

---

## Server

- **IP:** 204.168.163.80
- **Provider:** Hetzner CPX22 (~€8/mo)
- **OS:** Ubuntu 24.04
- **SSH:** `ssh root@204.168.163.80`
- **Logs:** `/var/log/eul/` (jack, superdirt, icecast, darkice)

## tmux windows

| Window | What's running |
|--------|---------------|
| 0 | Xvfb (virtual display for sclang) |
| 1 | JACK (virtual audio) |
| 2 | SuperCollider + SuperDirt |
| 3 | Icecast |
| 4 | DarkIce |
| 5 | TidalCycles REPL ← **this is where you work** |

Navigate between windows: `Ctrl+b` then the window number.
Detach without stopping anything: `Ctrl+b d`.

## Sample banks

| Bank | Path | Notes |
|------|------|-------|
| `drone` | `samples/drone/` | Whitney Dark Choir |
| `texture` | `samples/texture/` | disconeblip, droid11, droid14 |
| `glitch1` | `samples/percussive/glitch1/` | 55 slices |
| `dungeondrums` | `samples/percussive/dungeondrums/` | 14 slices |
| `rad` | `samples/percussive/rad/` | 37 slices |
| `ls` | `samples/melodic/chords/ls/` | 9 chord WAVs |
| `discoveryone` | `samples/melodic/chords/discoveryone/` | bridge pad |
| `disconevoice` | `samples/melodic/singletone/discoveryone/` | voice sample |
