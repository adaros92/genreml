#! /bin/bash
set -euo pipefail

env >> /etc/environment

python3 /opt/app.py