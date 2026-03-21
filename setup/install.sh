#!/usr/bin/env bash
# VPS setup script for eul — generative music radio station
# Run once (or re-run safely) on a fresh Ubuntu 24.04 server.
# Usage: bash setup/install.sh

set -euo pipefail

echo "==> Updating system packages"
apt-get update -qq
apt-get upgrade -y -qq

echo "==> Installing dependencies"
apt-get install -y -qq \
  build-essential git curl wget tmux \
  jackd2 darkice icecast2 \
  supercollider supercollider-server sc3-plugins \
  cabal-install ghc \
  libsamplerate0 libsndfile1 \
  nginx certbot python3-certbot-nginx \
  ufw

echo "==> Configuring audio (JACK dummy driver, no soundcard needed)"
# Allow real-time scheduling for audio
echo '@audio - rtprio 99'  >> /etc/security/limits.conf
echo '@audio - memlock unlimited' >> /etc/security/limits.conf
groupadd -f audio
usermod -aG audio root

echo "==> Installing TidalCycles via cabal"
cabal update
cabal install tidal --lib

echo "==> Installing SuperDirt (SuperCollider quark)"
# Run sclang headlessly to install SuperDirt
sclang -e "
Quarks.install('SuperDirt', '1.7.3');
Quarks.install('Dirt-Samples');
0.exit;
" || true

echo "==> Setting up eul directory"
mkdir -p /opt/eul/samples
mkdir -p /opt/eul/patterns
mkdir -p /opt/eul/config
mkdir -p /var/log/eul

echo "==> Configuring firewall"
ufw allow OpenSSH
ufw allow 8000/tcp   # Icecast stream
ufw allow 80/tcp     # HTTP (nginx)
ufw allow 443/tcp    # HTTPS (nginx)
ufw --force enable

echo "==> Writing Icecast config"
cat > /opt/eul/config/icecast.xml << 'EOF'
<icecast>
  <location>Malmö</location>
  <admin>oresti.theodoridis@gmail.com</admin>
  <limits>
    <clients>100</clients>
    <sources>1</sources>
  </limits>
  <authentication>
    <source-password>CHANGE_ME_SOURCE</source-password>
    <relay-password>CHANGE_ME_RELAY</relay-password>
    <admin-user>admin</admin-user>
    <admin-password>CHANGE_ME_ADMIN</admin-password>
  </authentication>
  <hostname>204.168.163.80</hostname>
  <listen-socket>
    <port>8000</port>
  </listen-socket>
  <mount>
    <mount-name>/stream</mount-name>
    <max-listeners>100</max-listeners>
  </mount>
  <fileserve>1</fileserve>
  <paths>
    <basedir>/usr/share/icecast2</basedir>
    <logdir>/var/log/icecast2</logdir>
    <webroot>/usr/share/icecast2/web</webroot>
    <adminroot>/usr/share/icecast2/admin</adminroot>
  </paths>
  <logging>
    <accesslog>access.log</accesslog>
    <errorlog>error.log</errorlog>
    <loglevel>3</loglevel>
  </logging>
</icecast>
EOF

echo "==> Writing DarkIce config"
cat > /opt/eul/config/darkice.cfg << 'EOF'
[general]
duration        = 0        # stream forever
bufferSecs      = 5
reconnect       = yes

[input]
device          = default  # JACK default input
sampleRate      = 44100
bitsPerSample   = 16
channel         = 2

[icecast2-0]
bitrateMode     = cbr
format          = mp3
bitrate         = 192
server          = localhost
port            = 8000
password        = CHANGE_ME_SOURCE
mountPoint      = stream
name            = eul
description     = generative music by demea
url             = https://demea.xyz
genre           = experimental electronic
public          = no
EOF

echo "==> Writing SuperDirt boot file"
cat > /opt/eul/config/superdirt_boot.scd << 'EOF'
// SuperDirt boot — loads samples from /opt/eul/samples
SuperDirt.start;
~dirt = SuperDirt(2, s);
~dirt.loadSoundFiles("/opt/eul/samples/*");
~dirt.start(57120, [0, 0]);
EOF

echo "==> Writing TidalCycles boot file"
cat > /opt/eul/config/tidal_boot.hs << 'EOF'
:set -XOverloadedStrings
:set prompt ""
import Sound.Tidal.Context
tidal <- startTidal (superdirtTarget {oLatency = 0.05}) (defaultConfig {cVerbose = True})
let p = streamReplace tidal
let hush = streamHush tidal
let d1 = p 1 . (|< orbit 0)
let d2 = p 2 . (|< orbit 1)
let d3 = p 3 . (|< orbit 2)
let d4 = p 4 . (|< orbit 3)
let d5 = p 5 . (|< orbit 4)
let d6 = p 6 . (|< orbit 5)
:set prompt "tidal> "
EOF

echo "==> Writing start script"
cat > /opt/eul/start.sh << 'EOF'
#!/usr/bin/env bash
# Start all eul services in a tmux session

SESSION="eul"
tmux kill-session -t $SESSION 2>/dev/null || true
tmux new-session -d -s $SESSION -x 220 -y 50

# Pane 0: JACK (virtual audio, headless)
tmux send-keys -t $SESSION "jackd -d dummy -r 44100 -p 1024 2>&1 | tee /var/log/eul/jack.log" Enter
sleep 3

# Pane 1: SuperCollider + SuperDirt
tmux new-window -t $SESSION
tmux send-keys -t $SESSION "sclang /opt/eul/config/superdirt_boot.scd 2>&1 | tee /var/log/eul/superdirt.log" Enter
sleep 10

# Pane 2: Icecast
tmux new-window -t $SESSION
tmux send-keys -t $SESSION "icecast2 -c /opt/eul/config/icecast.xml 2>&1 | tee /var/log/eul/icecast.log" Enter
sleep 2

# Pane 3: DarkIce
tmux new-window -t $SESSION
tmux send-keys -t $SESSION "darkice -c /opt/eul/config/darkice.cfg 2>&1 | tee /var/log/eul/darkice.log" Enter
sleep 2

# Pane 4: TidalCycles REPL (interactive)
tmux new-window -t $SESSION
tmux send-keys -t $SESSION "ghci -ghci-script /opt/eul/config/tidal_boot.hs" Enter

echo "eul started. Attach with: tmux attach -t eul"
EOF
chmod +x /opt/eul/start.sh

echo ""
echo "==> Install complete."
echo ""
echo "Next steps:"
echo "  1. rsync your samples:  rsync -avz samples/ root@204.168.163.80:/opt/eul/samples/"
echo "  2. SSH in and run:      bash /opt/eul/start.sh"
echo "  3. Attach to tmux:      tmux attach -t eul"
echo "  4. Stream URL:          http://204.168.163.80:8000/stream"
