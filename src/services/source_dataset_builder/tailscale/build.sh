#! /bin/bash
set -euo pipefail

git pull origin master
docker build -t datasetbuilder .