#! /bin/bash
set -euo pipefail

if [[ -z "$@" ]]; then
  CONTAINER_IMAGE="spectrogrampredictor:latest"
else
  CONTAINER_IMAGE=$1
fi

read -s -p "Enter Signing Token: " SIGNING_TOKEN
echo ""
docker run --restart always --name spectrogrampredictor --hostname=spectrogrampredictor -v /certs:/certs -v /model_store:/opt/model_store -p 443:443 -p 4443:4443 -e SIGNING_TOKEN=$SIGNING_TOKEN -dit $CONTAINER_IMAGE
