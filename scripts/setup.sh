#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cc65_revision=555282497c3ecf8b313d87d5973093af19c35bd5
for tool in python3 git make cc; do
    command -v "$tool" >/dev/null || { echo "Missing $tool; see docs/DEVELOPMENT.md" >&2; exit 1; }
done
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements.txt
mkdir -p .tools
if [ ! -d .tools/cc65 ]; then
    git clone --branch V2.19 --depth 1 https://github.com/cc65/cc65.git .tools/cc65
fi
if [ "$(git -C .tools/cc65 rev-parse HEAD)" != "$cc65_revision" ]; then
    echo "Unexpected cc65 revision; expected $cc65_revision. Existing checkout left untouched." >&2
    exit 1
fi
if [ -n "$(git -C .tools/cc65 status --porcelain --untracked-files=no)" ]; then
    echo "Local cc65 source has changes; inspect before building." >&2
    exit 1
fi
make -C .tools/cc65 -j "${JOBS:-2}" ca65 ld65
.tools/cc65/bin/ca65 --version
.tools/cc65/bin/ld65 --version
.venv/bin/python -c 'from py65.devices.mpu6502 import MPU; print("Py65 NMOS 6502 import OK")'
