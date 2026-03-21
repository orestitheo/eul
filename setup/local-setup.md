# Local setup (Mac)

For experimenting with patterns locally before deploying to the server.
No streaming — you hear output through your speakers/headphones directly.

## Steps

### 1. SuperCollider

Download and install the Mac app from https://supercollider.github.io

### 2. SuperDirt + Vowel quarks

Open SuperCollider IDE, paste this in the editor, press Cmd+Enter:

```supercollider
Quarks.install("SuperDirt");
Quarks.install("Vowel");
```

Wait for it to finish, then restart SuperCollider.

### 3. TidalCycles

```bash
cabal update && cabal install tidal --lib
```

Takes 5-10 minutes.

### 4. Verify

```bash
echo "import Sound.Tidal.Context" | ghci
```

Should load without errors.

## Running locally

**1. Boot SuperDirt** — in SuperCollider IDE, paste and run (Cmd+Enter):

```supercollider
SuperDirt.start;
```

To load your own samples instead of the defaults:

```supercollider
SuperDirt.start;
~dirt.loadSoundFiles("/path/to/eul/samples/drone");
~dirt.loadSoundFiles("/path/to/eul/samples/texture");
// etc.
```

**2. Start TidalCycles** — in Terminal:

```bash
ghci -ghci-script config/tidal_boot.hs
```

You'll get a `tidal>` prompt. Type patterns, hear them immediately.

**3. Detach from session** — when done, type `hush` to stop all patterns, then `:quit`.

## Workflow

- Experiment locally until a pattern sounds good
- Copy it into `patterns/main.tidal`
- Commit and push
- SSH into the server, paste the pattern into the live REPL
