#!/usr/bin/env python3
"""Проба голосов ElevenLabs (Voice Design): описание голоса + текст реплик → 3 пробных голоса.

Голоса в аккаунте не сохраняются (только пробы). Журнал — work/elevenlabs/log.jsonl.

  python tools/audio/voice.py ПАПКА ИМЯ "описание голоса (англ.)" "текст 100–1000 знаков"
         [--model eleven_ttv_v3] [--guidance 4]
"""
import argparse
import base64
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eleven import API, LOG, ROOT, post  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("name")
    ap.add_argument("description")
    ap.add_argument("text")
    ap.add_argument("--model", default="eleven_ttv_v3")
    ap.add_argument("--guidance", type=float, default=4.0)
    a = ap.parse_args()
    if not 100 <= len(a.text) <= 1000:
        sys.exit(f"текст {len(a.text)} знаков, нужно 100–1000")

    body = {"voice_description": a.description, "text": a.text, "model_id": a.model,
            "guidance_scale": a.guidance, "loudness": 0.5}
    data = json.loads(post(f"{API}/text-to-voice/design?output_format=mp3_44100_192", body))
    out = Path(a.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for i, p in enumerate(data["previews"], 1):
        f = out / f"{a.name}_{i}.mp3"
        f.write_bytes(base64.b64decode(p["audio_base_64"]))
        files.append({"file": str(f.relative_to(ROOT)), "generated_voice_id": p["generated_voice_id"],
                      "sec": p.get("duration_secs")})
        print(f, p.get("duration_secs"), "с")
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "voice_design", "model": a.model, "description": a.description,
                             "prompt": a.text, "previews": files,
                             "date": datetime.date.today().isoformat()}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
