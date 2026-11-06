"""Captions from the real voice track: faster-whisper word timestamps -> word-by-word ASS captions,
plus the on-screen headline for each line. Also checks the transcript against the script.
Run with the vetted venv:  ~/.venvs/faster-whisper/Scripts/python.exe scripts/make_captions.py
Layout respects Instagram Reels safe zones (1080 x 1920): nothing above y=270, captions clear of the
bottom ~480 px (caption/username/audio UI) and the right-hand buttons.
"""
import os, json, re, difflib, pathlib, subprocess
import numpy as np
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
from faster_whisper import WhisperModel

ROOT = pathlib.Path(__file__).resolve().parents[1]
script = json.loads((ROOT / "script.json").read_text(encoding="utf-8"))
timing = json.loads((ROOT / "blender" / "timing.json").read_text())

model = WhisperModel("small", device="cpu", compute_type="int8")
prompt = "A day on Venus is longer than its year. 243 Earth days. 225. The Sun would rise in the west."
# decode with ffmpeg to 16 kHz mono float (faster-whisper's own decoder, PyAV, is incompatible with av 16+)
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ROOT / "voice" / "vo.wav"), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
audio = np.frombuffer(pcm, dtype=np.float32)
segments, info = model.transcribe(audio, language="en", word_timestamps=True, initial_prompt=prompt, beam_size=5, vad_filter=False)
words = [{"w": w.word.strip(), "s": w.start, "e": w.end} for s in segments for w in s.words if w.word.strip()]
(ROOT / "captions" / "words.json").write_text(json.dumps(words, indent=1))

# ---- check: does what was heard match what was written?
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower().replace("-", " "))
num = {"243": "two hundred and forty three", "225": "two hundred and twenty five"}
heard = norm(" ".join(num.get(re.sub(r"\D", "", w["w"]), w["w"]) if re.sub(r"\D", "", w["w"]) in num else w["w"] for w in words))
wrote = norm(" ".join(l["say"] for l in script["lines"]))
ratio = difflib.SequenceMatcher(None, heard.split(), wrote.split()).ratio()
print(f"transcript vs script word match: {ratio:.3f}")
print("heard:", " ".join(w["w"] for w in words))

# ---- ASS
def ts(t): t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60; return f"{h}:{m:02d}:{s:05.2f}"
head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat ExtraBold,82,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,7,3,5,60,140,0,1
Style: Head,Montserrat Black,92,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,1,0,1,0,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
YELLOW = r"{\c&H3FD7FF&}"; WHITE = r"{\c&HFFFFFF&}"
ev = []
# word-by-word captions in chunks of up to 3 words (break at punctuation); the spoken word is highlighted
chunks, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) == 3 or re.search(r"[.,!?]$", w["w"]): chunks.append(cur); cur = []
if cur: chunks.append(cur)
nxt = {id(w): (words[k + 1]["s"] if k + 1 < len(words) else w["e"] + 0.5) for k, w in enumerate(words)}
for c in chunks:
    for i, w in enumerate(c):
        # each word holds until the next word starts; a chunk's last word lingers up to 0.25 s but never overlaps the next chunk
        end = nxt[id(w)] if i + 1 < len(c) else min(w["e"] + 0.25, nxt[id(w)])
        txt = " ".join((YELLOW if j == i else WHITE) + x["w"].upper().strip(".,") for j, x in enumerate(c))
        pop = r"{\fscx108\fscy108\t(0,90,\fscx100\fscy100)}" if i == 0 else ""
        ev.append(f"Dialogue: 1,{ts(w['s'])},{ts(end)},Cap,,0,0,0,,{{\\pos(500,1270)}}{pop}{txt}")
# headline per line: a dark pill with big text, popped in, inside the top safe area
for s in timing["segments"]:
    if not s["onscreen"]: continue
    a, b = s["start"], s["end"] + 0.25
    ev.append(f"Dialogue: 2,{ts(a)},{ts(b)},Head,,0,0,0,,{{\\pos(540,430)\\fad(120,160)\\fscx80\\fscy80\\t(0,160,\\fscx100\\fscy100)\\3c&H101010&\\bord0\\shad0}}{s['onscreen']}")
    # backing pill in absolute coordinates (top-left anchored), under the headline
    ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Head,,0,0,0,,{{\\an7\\pos(0,0)\\fad(120,160)\\1c&H141414&\\1a&H30&\\bord0\\shad0\\p1}}m 150 362 b 110 362 110 498 150 498 l 930 498 b 970 498 970 362 930 362{{\\p0}}")
(ROOT / "captions" / "captions.ass").write_text(head + "\n".join(ev) + "\n", encoding="utf-8")
# plain SRT too (for Instagram's own caption upload / accessibility)
srt = []
for k, c in enumerate(chunks, 1):
    def st(t): return f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(round((t%1)*1000)):03d}"
    srt.append(f"{k}\n{st(c[0]['s'])} --> {st(c[-1]['e'])}\n{' '.join(x['w'] for x in c)}\n")
(ROOT / "captions" / "captions.srt").write_text("\n".join(srt), encoding="utf-8")
print(f"{len(words)} words, {len(chunks)} caption chunks")
