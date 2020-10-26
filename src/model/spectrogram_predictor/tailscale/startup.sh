#! /bin/bash
set -euo pipefail

mkdir /dev/net 
mknod /dev/net/tun c 10 200
nohup tailscaled >/dev/null 2>&1 &
sleep 3
while [[ -z "$(ps aux|grep tailscaled|grep -v grep)" ]]; do sleep 1; done
tailscale up --authkey $TAILSCALE_AUTH --advertise-tags tag:spectrogrampredictor
unset TAILSCALE_AUTH
#hypercorn --certfile /certs/server.crt --keyfile /certs/server.key --bind 0.0.0.0:$TAILSCALE_PORT /opt/app:app
nohup bash -c "node /opt/upload.js" >/dev/null 2>&1 &
hypercorn --bind 0.0.0.0:$TAILSCALE_PORT /opt/app:app