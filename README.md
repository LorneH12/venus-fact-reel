# Venus fact reel: a tool test

A 19-second vertical explainer, **"A day on Venus is longer than its year"**. It tests three tools from start to finish:

| Step | Tool | Files |
|---|---|---|
| Script (fact-checked against NASA) | written by hand | `script.json` |
| Voice-over | **Chatterbox TTS** 0.1.7 with its built-in default voice (no cloning), on CPU, with the Perth watermark on | `scripts/make_voice.py`, `scripts/join_voice.py` → `voice/vo.wav`, `blender/timing.json` |
| Captions | **faster-whisper** 1.2.1 (`small`, int8, CPU): word timestamps → word-by-word ASS captions, plus an SRT | `scripts/make_captions.py` → `captions/` |
| 3D | **Blender 4.5** through the Blender MCP (built and checked live), with the final render headless in EEVEE | `blender/build_scene.py` → `blender/venus-reel.blend` |
| Assembly | ffmpeg | `scripts/assemble.sh` → `output/venus-reel.mp4`, `output/cover.jpg` |

## Instagram Reels spec (verified with ffprobe and ebur128)

- **Picture:** 1080 × 1920 (9:16) · 30 fps CFR · 19.2 s
- **Video:** H.264 High, level 4.1 · yuv420p, TV range, BT.709 · keyframe every 2 s · moov atom at the front (faststart)
- **Audio:** AAC-LC, 48 kHz stereo, 192 kbps · **-14.4 LUFS** integrated, peak -4.4 dBFS
- **On-screen text:** stays inside the Reels safe zone. Nothing sits above y = 270, captions sit at y ≈ 1270 (clear of the bottom 480 px of UI), and text stays clear of the right-hand button column.
- **Captions:** burned in. `captions/captions.srt` is also there for upload.

## Rebuild

```bash
~/.venvs/chatterbox/Scripts/python.exe scripts/make_voice.py      # ~3 min on CPU
~/.venvs/chatterbox/Scripts/python.exe scripts/join_voice.py
~/.venvs/faster-whisper/Scripts/python.exe scripts/make_captions.py
"/c/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P blender/build_scene.py   # or run it through the MCP
"/c/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b blender/venus-reel.blend -o "//frames/####" -F JPEG -a   # ~21 min
bash scripts/assemble.sh
```

**Source:** NASA Science, Venus facts (https://science.nasa.gov/venus/venus-facts/). One spin takes about 243 Earth days and is retrograde (backwards). One orbit takes about 225 Earth days. The Sun would rise in the west.

**Not published.** This is a private test repo; posting to Instagram needs the owner's go-ahead.
