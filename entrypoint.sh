#!/bin/sh

mkdir -p ~/.config/rclone
mkdir -p /config/torrents
mkdir -p /config/resume
mkdir -p /storage_root

# Rclone config set
echo "$RCLONE_CONFIG_DATA" > ~/.config/rclone/rclone.conf

REMOTE="gdrive"
if ! rclone lsd "${REMOTE}:" > /dev/null 2>&1; then
  REMOTE="maindrive"
fi

echo "Fetching resume and torrents from ${REMOTE}:qbit_config..."
rclone copy "${REMOTE}:qbit_config" /config/temp_fetch/ --include "*/resume/**" --include "*/torrents/**" || true
find /config/temp_fetch/ -type f -path "*/resume/*" -exec mv -t /config/resume/ {} + 2>/dev/null || true
find /config/temp_fetch/ -type f -path "*/torrents/*" -exec mv -t /config/torrents/ {} + 2>/dev/null || true
rm -rf /config/temp_fetch

# Generate sparse files
python3 /generate_sparse.py

# Transmission settings file
cat << 'EOF' > /config/settings.json
{
  "download-dir": "/storage_root",
  "incomplete-dir-enabled": false,
  "rpc-enabled": true,
  "rpc-port": 9091,
  "rpc-bind-address": "0.0.0.0",
  "rpc-authentication-required": false,
  "rpc-whitelist-enabled": false,
  "rpc-host-whitelist-enabled": false,
  "peer-limit-global": 0,
  "peer-limit-per-torrent": 0,
  "port-forwarding-enabled": false,
  "dht-enabled": false,
  "pex-enabled": false,
  "lpd-enabled": false,
  "speed-limit-up": 1,
  "speed-limit-up-enabled": true,
  "speed-limit-down": 1,
  "speed-limit-down-enabled": true
}
EOF

# Start Transmission Daemon
transmission-daemon -g /config -e /var/log/transmission.log
sleep 3
transmission-remote -t all --find /storage_root || true
transmission-remote -t all --start || true

# Announce Loop & Keepalive
while true; do
  transmission-remote -t all --start || true
  transmission-remote -t all --reannounce || true
  sleep 600
done
