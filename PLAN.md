# eul — Generative Music Radio Station

## What this is

An always-on internet radio station that streams algorithmically generated music 24/7.
When someone opens the "generated" tab on demea.xyz, they tune in and hear whatever
is playing right now — like a radio station, not a playlist.

This is server infrastructure, not a webpage.

---

## How it works (signal chain)

```
TidalCycles (pattern code, runs in terminal)
    ↓ OSC messages
SuperCollider + SuperDirt (audio synthesis + sample playback)
    ↓ audio output
JACK (virtual audio routing, headless — no soundcard needed)
    ↓ audio stream
DarkIce (encodes to MP3/Opus in realtime)
    ↓ encoded stream
Icecast2 (HTTP streaming server, port 8000)
    ↓ HTTP stream URL
demea.xyz visitor (HTML <audio> tag, tunes in live)
```

Key insight: TidalCycles only sends *instructions* (via OSC). SuperCollider does the
actual sound work. JACK pipes that audio headlessly. Icecast serves it over HTTP.

---

## Stack

| Component | Role | Cost |
|-----------|------|------|
| Hetzner CPX22 VPS | Server (2 vCPU, 4GB RAM) | ~€8/mo |
| TidalCycles | Pattern language for generative music | free |
| SuperCollider + SuperDirt | Audio synthesis engine + sample playback | free |
| JACK (dummy driver) | Headless virtual audio routing | free |
| DarkIce | Encodes audio → sends to Icecast | free |
| Icecast2 | HTTP audio streaming server | free |
| icecast-metadata-js | JS lib for metadata on web player | free |

Total: ~€8/month.

---

## Folder structure (this repo)

```
eul/
  patterns/
    main.tidal          # the TidalCycles generative pattern (version controlled)
    ambient.tidal       # ambient-only layer
    rhythmic.tidal      # beat-heavy layer
  config/
    darkice.cfg         # DarkIce config (reads from JACK, outputs to Icecast)
    icecast.xml         # Icecast server config
  setup/
    install.sh          # idempotent VPS setup script
    start.sh            # start all services in tmux
    stop.sh             # graceful shutdown
  samples/              # your audio samples (committed to repo, rsync'd to VPS)
    drone/
    percussive/
    texture/
    melodic/
  PLAN.md
  README.md
```

The TidalCycles code lives in this repo. You edit patterns here, push to git,
then pull on the server and reload. The samples also live here and get rsync'd
to the VPS.

---

## Samples folder convention

Organise your audio files like this before Phase 1:

```
samples/
  drone/       # long sustained tones, slow pads, bowed things
  percussive/  # kicks, hits, impacts, transients
  texture/     # field recordings, noise, ambience, granular source material
  melodic/     # pitched fragments, tonal material
```

Format: WAV or FLAC preferred (lossless — DarkIce/Icecast handles the compression).
MP3 also works but avoid double-lossy-encoding.

---

## Phase 1 — Server setup + first stream

**Goal:** VPS is running, Icecast is serving a live stream, you can tune in.

### Steps

1. Provision Hetzner CPX22, Ubuntu 24.04
2. Run `setup/install.sh` which installs:
   - SuperCollider + sc3-plugins
   - SuperDirt (via sclang -e "Quarks.install('SuperDirt')")
   - TidalCycles + GHC (Haskell)
   - JACK + jackd dummy driver
   - DarkIce + Icecast2
3. rsync `samples/` to VPS
4. Configure `config/darkice.cfg` and `config/icecast.xml`
5. Run `start.sh` — launches everything in tmux:
   - tmux pane 1: `jackd -d dummy -r 44100`
   - tmux pane 2: `sclang` (boots SuperDirt)
   - tmux pane 3: `ghci` / TidalCycles REPL with `main.tidal` loaded
   - tmux pane 4: `darkice -c config/darkice.cfg`
   - tmux pane 5: `icecast2 -c config/icecast.xml`
6. Stream is live at `http://your-vps-ip:8000/stream`

### End state

You can open VLC or a browser and tune in. Hear audio. The stream stays up as long
as the server runs.

---

## Phase 2 — Generative patterns

**Goal:** The stream plays something interesting, not just noise.
Music evolves over time — no loops, no repetition.

### TidalCycles basics (explained)

TidalCycles uses a pattern language. Patterns describe *what sounds play, when, and
how*. The key thing: patterns can be randomised and evolve without your involvement.

```haskell
-- main.tidal

-- A drone that slowly shifts its filter frequency
d1 $ sound "drone:0" # gain 0.7 # lpf (slow 16 $ range 300 2000 perlin)

-- Sparse texture hits, random timing
d2 $ rarely id $ sound "texture:0 texture:1 ~ texture:2"
   # speed (range 0.4 1.8 rand)
   # delay 0.4 # delaytime 0.375 # room 0.8

-- Granular-style: slice random segment of a sample and loop it
d3 $ loopAt 4 $ chop 16 $ sound "melodic:0"
   # begin (range 0 0.8 perlin)
   # lpf (slow 8 $ range 400 1600 sine)
```

Key concepts:
- `perlin` — smoothly wandering random (good for slow filter sweeps)
- `rand` — fully random per event
- `rarely` — applies transform ~10% of events
- `slow N` — stretches pattern to N cycles
- `chop 16` — slices sample into 16 segments (granular effect)
- `d1`, `d2`, `d3` — independent pattern channels that play simultaneously

### Progression

- Start with ambient only: drones + textures, no beats
- Add rhythmic layer once the ambient material sounds good
- Use `xfade` to crossfade between different pattern states over time

### End state

The stream plays evolving ambient music made from your samples. Unrecognisable
as "just a sample" — processed into something textural.

---

## Phase 3 — Web player on demea.xyz

**Goal:** A tab on demea.xyz with a live player. Shows what's playing.

### Implementation (in the oresti-xyz portfolio repo)

```html
<!-- demea.xyz — generated tab section -->
<section id="generated">
  <audio id="stream-player" preload="none">
    <source src="https://music.demea.xyz:8000/stream" type="audio/mpeg">
  </audio>
  <button id="tune-in">tune in</button>
  <p id="now-playing"></p>
</section>
```

```js
// Uses icecast-metadata-js to decode ICY metadata from the stream
import IcecastMetadataPlayer from 'icecast-metadata-player';

const player = new IcecastMetadataPlayer('https://music.demea.xyz:8000/stream', {
  onMetadata: (meta) => {
    document.getElementById('now-playing').textContent = meta.StreamTitle || '';
  }
});

document.getElementById('tune-in').addEventListener('click', () => player.play());
```

The TidalCycles pattern can set stream metadata (track title / current pattern name)
via Icecast's admin API so the site can display "currently: ambient layer III" or
whatever you want to call it.

### Domain + HTTPS

- Point `music.demea.xyz` at the VPS IP (Cloudflare DNS, already manage demea.xyz there)
- Icecast listens on port 8000; use Nginx as a reverse proxy with Let's Encrypt SSL
- This lets the stream URL be `https://music.demea.xyz/stream` (required for HTTPS sites)

### End state

demea.xyz has a "generated" tab. Click "tune in". Hear the live stream. No page
reload needed. The stream continues as long as the tab is open.

---

## Keeping it running (ops)

- All services managed via `systemd` units (auto-restart on crash)
- TidalCycles itself runs in a tmux session (you SSH in to change patterns live)
- To update patterns: edit `patterns/main.tidal` locally, push to git, SSH + pull + reload
- Monitoring: simple uptime check via a cron job that tests `curl http://localhost:8000/stream`

---

## Verification (per phase)

- **Phase 1**: `vlc http://your-vps-ip:8000/stream` → hear audio
- **Phase 2**: Stream plays for 30+ minutes, sounds different at each listen
- **Phase 3**: demea.xyz generated tab → click tune in → hear live stream

---

## Before Phase 1 can start

1. Sort your samples into `samples/drone/`, `samples/percussive/`, `samples/texture/`, `samples/melodic/`
2. Decide on VPS: Hetzner CPX22 (~€8/mo) or you already have a server?
3. That's it — the setup script handles the rest
