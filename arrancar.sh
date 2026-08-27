#!/bin/sh
set -eu
PACKAGE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$PACKAGE_DIR"
docker compose up -d trazo backend
