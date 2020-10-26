#! /bin/bash
set -euo pipefail

if [[ -z "$@" ]]; then
  CONTAINER_IMAGE="spectrogrampredictor:latest"
else
  CONTAINER_IMAGE=$1
fi

read -s -p "Enter Secret Token: " DOCKER_TOKEN
echo ""
docker run --restart always --name spectrogrampredictor --hostname=spectrogrampredictor --cap-add=SYS_MODULE --cap-add=NET_ADMIN -e TAILSCALE_AUTH=$DOCKER_TOKEN -dit $CONTAINER_IMAGE
