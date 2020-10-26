#! /bin/bash
set -euo pipefail

nohup bash -c "node /opt/upload.js" >/dev/null 2>&1 &
hypercorn --certfile /certs/server.crt --keyfile /certs/server.key --bind 0.0.0.0:443 /opt/app:app