"""Join the per-line takes into one voice track and write blender/timing.json (line start/end times).
Run with the chatterbox venv (has torchaudio):  ~/.venvs/chatterbox/Scripts/python.exe scripts/join_voice.py
"""
import json, pathlib, torch, torchaudio

ROOT = pathlib.Path(__file__).resolve().parents[1]
FPS, SR = 30, 48000
LEAD, GAP, TAIL = 0.35, 0.30, 1.6          # seconds: before the first line, between lines, after the last
script = json.loads((ROOT / "script.json").read_text(encoding="utf-8"))

def trim(w, thr=0.01):
    """cut leading/trailing near-silence, keep 40 ms either side"""
    a = w.abs().max(0).values; idx = (a > thr).nonzero()
    if len(idx) == 0: return w
    pad = int(0.04 * SR); return w[:, max(0, idx[0].item() - pad): idx[-1].item() + pad]

parts, segs, t = [torch.zeros(1, int(LEAD * SR))], [], LEAD
for line in script["lines"]:
    w, sr = torchaudio.load(str(ROOT / "voice" / f"{line['id']}.wav"))
    w = trim(torchaudio.functional.resample(w.mean(0, keepdim=True), sr, SR))
    d = w.shape[-1] / SR
    segs.append({"id": line["id"], "start": round(t, 3), "end": round(t + d, 3), "onscreen": line["onscreen"]})
    parts += [w, torch.zeros(1, int(GAP * SR))]; t += d + GAP
parts[-1] = torch.zeros(1, int(TAIL * SR)); t += TAIL - GAP
total = round(t, 3)
torchaudio.save(str(ROOT / "voice" / "vo.wav"), torch.cat(parts, -1), SR)
(ROOT / "blender" / "timing.json").write_text(json.dumps({"fps": FPS, "total": total, "segments": segs}, indent=2))
print(json.dumps({"total": total, "segments": [(s["id"], s["start"], s["end"]) for s in segs]}))
