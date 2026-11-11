#!/bin/sh
# Copy build outputs into source/, assemble the package, zip to outputs.
set -e
cd "$(dirname "$0")/.."
python3 tools/draw_pictures.py html/game/pictures >/dev/null
python3 tools/experiments/screen_test.py html/game/pictures/screen.png >/dev/null
cp game.ctl game.skool game.ref map.svg source/
rm -rf source/tools source/__pycache__ tools/__pycache__ tools/experiments/__pycache__ /tmp/claude-0/pkg
mkdir -p /tmp/claude-0/pkg/html
cp README.md HISTORY.md /tmp/claude-0/pkg/
cp -r source /tmp/claude-0/pkg/
cp -r tools /tmp/claude-0/pkg/
cp p.bin s.bin game.ctl.baseline sherlock.css map.svg /tmp/claude-0/pkg/
cp -r html/game /tmp/claude-0/pkg/html/
rm -f /mnt/user-data/outputs/sherlock-disassembly.zip
cd /tmp/claude-0/pkg && zip -r -q /mnt/user-data/outputs/sherlock-disassembly.zip . -x "*.pyc"
ls -la /mnt/user-data/outputs/sherlock-disassembly.zip
