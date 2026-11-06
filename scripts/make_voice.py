"""Voice-over with Chatterbox (built-in default voice, no cloning), one WAV per script line.
Run with the vetted venv:  ~/.venvs/chatterbox/Scripts/python.exe scripts/make_voice.py
Telemetry off: HF_HUB_DISABLE_TELEMETRY=1, GRADIO_ANALYTICS_ENABLED=False (set below before imports).
"""
import os, json, time, pathlib
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
import torch, torchaudio
from chatterbox.tts import ChatterboxTTS

ROOT = pathlib.Path(__file__).resolve().parents[1]
script = json.loads((ROOT / "script.json").read_text(encoding="utf-8"))
out = ROOT / "voice"; out.mkdir(exist_ok=True)
torch.manual_seed(7)                     # repeatable takes
torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))

t0 = time.time()
model = ChatterboxTTS.from_pretrained(device="cpu")
print(f"model loaded in {time.time() - t0:.0f} s (sample rate {model.sr})", flush=True)
for line in script["lines"]:
    f = out / f"{line['id']}.wav"
    if f.exists():
        print(f"skip {f.name} (exists)"); continue
    t = time.time()
    # a little more energy than the default for a social explainer; lower cfg = slightly faster delivery
    wav = model.generate(line["say"], exaggeration=0.6, cfg_weight=0.45)
    torchaudio.save(str(f), wav, model.sr)
    print(f"{f.name}: {wav.shape[-1] / model.sr:.2f} s audio in {time.time() - t:.0f} s", flush=True)
print(f"done in {time.time() - t0:.0f} s")
