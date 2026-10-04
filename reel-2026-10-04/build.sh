#!/usr/bin/env bash
# Full rebuild: frames -> soundtrack -> final MP4 + cover.
# Requires: node 18+, python3 (numpy scipy soundfile), ffmpeg.
set -euo pipefail
cd "$(dirname "$0")"
npm install --silent
rm -rf build/frames
WORKERS="${WORKERS:-3}" node render.mjs
node render.mjs cover
python3 audio/mix.py
ffmpeg -y -hide_banner -loglevel warning \
  -framerate 30 -i build/frames/%05d.png -i build/mix.wav \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 \
  -c:v libx264 -preset slow -crf 16 -profile:v high -pix_fmt yuv420p -tune film \
  -c:a aac -b:a 320k -movflags +faststart -shortest \
  out/Nimra_Reel_2026-10-04_Founders_Run_Errands.mp4
ffmpeg -y -hide_banner -loglevel warning -i build/cover.png -q:v 2 out/Nimra_Reel_2026-10-04_Cover.jpg
echo "done -> out/"
