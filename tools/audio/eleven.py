#!/usr/bin/env python3
"""Генерация через ElevenLabs: музыка (Music API) и звуковые эффекты (Sound Effects API).

Ключ — переменная окружения ELEVENLABS_API_KEY. Каждый запрос пишется в журнал
work/elevenlabs/log.jsonl (файл, промпт, параметры, дата) — как темы 06.10.2026.

  python tools/audio/eleven.py music ВЫХОД.mp3 --ms 90000 [--model music_v1] "промпт"
  python tools/audio/eleven.py music ВЫХОД.mp3 --plan ПЛАН.json [--model music_v2_5] "пометка"
  python tools/audio/eleven.py upload ФАЙЛ.mp3 "пометка"   — загрузить образец, печатает song_id
      (для conditioning_ref в плане: часть генерируется «по образцу» — вариация той же темы)
      — композиция по частям (composition_plan API: общие стили и части со своими стилями
        и длительностями); так тема и её вариация звучат в одной пьесе одной мелодией
  python tools/audio/eleven.py sfx ВЫХОД.mp3 [--sec 2.5] [--loop] [--influence 0.5] "промпт"
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "work" / "elevenlabs" / "log.jsonl"
API = "https://api.elevenlabs.io/v1"


def post(url, body, tries=8):
    """POST с повтором при 429: на тарифе Creator не больше двух запросов разом."""
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("нет ELEVENLABS_API_KEY")
    for i in range(tries):
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"xi-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            if e.code == 429 and i + 1 < tries:
                time.sleep(15 * (i + 1))
                continue
            sys.exit(f"ElevenLabs {e.code}: {msg}")


def upload(path):
    """Загрузить аудио в хранилище Music API (multipart), вернуть song_id."""
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("нет ELEVENLABS_API_KEY")
    bnd = "----bj3" + str(int(time.time() * 1000))
    body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: audio/mpeg\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{bnd}--\r\n".encode()
    req = urllib.request.Request(f"{API}/music/upload", data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": f"multipart/form-data; boundary={bnd}"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())["song_id"]
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {e.code}: {e.read().decode(errors='replace')[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["music", "sfx", "upload"])
    ap.add_argument("out")
    ap.add_argument("prompt")
    ap.add_argument("--ms", type=int, default=90000)
    ap.add_argument("--model", default="music_v1")
    ap.add_argument("--sec", type=float)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--influence", type=float, default=0.4)
    ap.add_argument("--plan", help="JSON с composition_plan (только music)")
    a = ap.parse_args()

    if a.kind == "upload":
        song_id = upload(Path(a.out))
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"kind": "upload", "file": a.out, "song_id": song_id, "note": a.prompt,
                                "date": datetime.date.today().isoformat()}, ensure_ascii=False) + "\n")
        print(song_id)
        return
    if a.kind == "music":
        if a.plan:
            plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
            body = {"composition_plan": plan, "model_id": a.model}
            rec = {"model": a.model, "plan": plan,
                   "ms": sum(s["duration_ms"] for s in plan.get("sections") or plan.get("chunks"))}
        else:
            body = {"prompt": a.prompt, "music_length_ms": a.ms, "model_id": a.model,
                    "force_instrumental": True}
            rec = {"ms": a.ms, "model": a.model}
        data = post(f"{API}/music?output_format=mp3_44100_192", body)
    else:
        body = {"text": a.prompt, "prompt_influence": a.influence, "loop": a.loop,
                "model_id": "eleven_text_to_sound_v2"}
        if a.sec:
            body["duration_seconds"] = a.sec
        data = post(f"{API}/sound-generation?output_format=mp3_44100_192", body)
        rec = {"kind": "sfx", "sec": a.sec, "loop": a.loop, "influence": a.influence}

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"file": str(out.relative_to(ROOT)) if out.is_absolute() else str(out),
                            "prompt": a.prompt, **rec,
                            "date": datetime.date.today().isoformat()}, ensure_ascii=False) + "\n")
    print(out, len(data), "байт")


if __name__ == "__main__":
    main()
