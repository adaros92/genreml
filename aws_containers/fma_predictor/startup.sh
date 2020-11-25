#! /bin/bash
set -euo pipefail

env >> /etc/environment

nohup bash -c "node /opt/upload.js" >/dev/null 2>&1 &
hypercorn --bind 0.0.0.0:80 /opt/app:app