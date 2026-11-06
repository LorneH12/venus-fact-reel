#!/usr/bin/env bash
# Assemble the Reel: Blender frames + voice + burned-in captions -> output/venus-reel.mp4 (Instagram Reels spec).
#   1080 x 1920 (9:16) · 30 fps CFR · H.264 High 4.1, yuv420p, ~10 Mbps · AAC-LC 48 kHz stereo 192 kbps
#   loudness -14 LUFS integrated, true peak <= -1 dBTP · +faststart · plus a 1080 x 1920 cover JPEG
set -euo pipefail
cd "$(dirname "$0")/.."
FPS=30
# 1) two-pass loudness on the voice (measure, then correct linearly)
J=$(ffmpeg -hide_banner -nostats -i voice/vo.wav -af loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | sed -n "s/.*\"$1\" : \"\(.*\)\".*/\1/p"; }
NORM="loudnorm=I=-14:TP=-1.5:LRA=7:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true"
# 2) video: frames -> captions burned in (fonts from Windows) -> encode; audio: voice, mono -> stereo, normalised
MSYS_NO_PATHCONV=1 ffmpeg -y -v error -framerate $FPS -i blender/frames/%04d.jpg -i voice/vo.wav \
  -vf "scale=1080:1920:flags=lanczos:in_range=pc:out_range=tv,subtitles=captions/captions.ass:fontsdir='C\:/Windows/Fonts',format=yuv420p" \
  -c:v libx264 -profile:v high -level 4.1 -preset slow -crf 17 -maxrate 12M -bufsize 24M -pix_fmt yuv420p -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -r $FPS -g 60 \
  -af "$NORM,aresample=48000" -ac 2 -c:a aac -b:a 192k -ar 48000 \
  -shortest -movflags +faststart output/venus-reel.mp4
# 3) cover: the hook frame with its headline (first second)
ffmpeg -y -v error -ss 1.2 -i output/venus-reel.mp4 -frames:v 1 -q:v 2 output/cover.jpg
echo "built output/venus-reel.mp4 and output/cover.jpg"
