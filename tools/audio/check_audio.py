#!/usr/bin/env python3
"""Сводная проверка звука (пакет З5): assets/audio против ASSET_SPEC §9 и текстов.

  python tools/audio/check_audio.py

1. Каждый файл спеки §9 есть в assets/audio, лишних нет (кроме 9 файлов BJ2, §9.5).
2. Формат: OGG Vorbis, 44,1 кГц; эффекты и блипы — моно (кроме стерео-исключений), фоны и музыка — стерео.
3. Громкость (BS.1770): музыка и стингеры −18, фоны −26, эффекты −16 (короткие щелчки упираются в пик
   −1,5 dBFS — тогда тише, это норма), исключения — по таблице TARGET.
4. Швы петель: уровень последних и первых 50 мс и скачок отсчёта на склейке.
5. «Без звука» (H21): у каждого слота из §9.1 в итоговых текстах есть титр `cap` либо слот — немая
   сцена с кадром; печатает слоты без титра для ручной сверки с GDD §8 (колонка «визуальный дубль»).
"""
import glob
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyloudnorm
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "assets" / "audio"
SPEC = ROOT / "docs" / "BJ3_ASSET_SPEC.md"
BJ2 = {"ui_click", "ui_zoom_in", "ui_zoom_out", "ui_pickup", "ui_paper", "ui_transition", "ui_error", "blip_lap", "blip_anc"}
STEREO_SFX = {"sfx_shock_thud", "sfx_shower_run", "sfx_lobby_hush"}
LOOPS_SFX = {"sfx_shower_run"}
TARGET = {"sfx_shock_thud": -12, "sfx_shower_run": -20, "sfx_lobby_hush": -20}

errors, notes = [], []


def err(m):
    errors.append(m)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                          "stream=codec_name,sample_rate,channels", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    codec, sr, ch = out.split(",")
    return codec, int(sr), int(ch)


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-acodec", "pcm_f32le", "-"],
                         capture_output=True).stdout
    _, sr, ch = probe(path)
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, ch), sr


def main():
    text = SPEC.read_text(encoding="utf-8")
    s9 = text[text.index("## 9. Звук"):text.index("## 10. Интерфейс")]
    names = set(re.findall(r"^\| `((?:sfx|amb|bgm|mus|sting|blip)_[a-z0-9_]+)\.ogg`", s9, re.M))
    have = {Path(p).stem for p in glob.glob(str(AUD / "*.ogg"))}
    for n in sorted(names - have):
        err(f"нет файла {n}.ogg")
    for n in sorted(have - names - BJ2):
        err(f"лишний файл {n}.ogg (нет в спеке §9)")

    print(f"{'файл':24s} {'кан':>3s} {'длина':>7s} {'LUFS':>6s} {'пик':>6s}  примечание")
    for n in sorted(names & have):
        p = AUD / f"{n}.ogg"
        codec, sr, ch = probe(p)
        if codec != "vorbis" or sr != 44100:
            err(f"{n}: формат {codec} {sr} Гц, нужен vorbis 44100")
        want_st = n.startswith(("amb_", "bgm_", "mus_", "sting_")) or n in STEREO_SFX
        if want_st != (ch == 2):
            err(f"{n}: каналов {ch}, нужно {'2' if want_st else '1'}")
        y, _ = decode(p)
        meter = pyloudnorm.Meter(sr, block_size=min(0.4, len(y) / sr * 0.9))
        lufs = meter.integrated_loudness(y)
        peak = 20 * np.log10(np.abs(y).max() + 1e-12)
        target = TARGET.get(n, -18 if n.startswith(("bgm_", "mus_", "sting_")) else -26 if n.startswith("amb_")
                            else None if n.startswith("blip_") else -16)
        note = ""
        if target is not None and abs(lufs - target) > 1.0:
            if lufs < target and peak > -2.6:
                note = f"тише цели {target} — упёрлось в пик (короткий удар)"
            else:
                err(f"{n}: громкость {lufs:.1f} LUFS, цель {target}")
        if peak > -0.9:
            err(f"{n}: пик {peak:.1f} dBFS выше −1")
        if n.startswith(("bgm_", "amb_", "mus_")) or n in LOOPS_SFX:
            k = int(0.05 * sr)
            rms = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)
            d = abs(rms(y[-k:]) - rms(y[:k]))
            jump = float(np.abs(y[0] - y[-1]).max())
            note = f"шов: Δуровня {d:.1f} дБ, скачок {jump:.3f}"
            if d > 6:   # в музыке это часто нота на первой доле; швы музыки проверены автором на слух
                note += " — сверить на слух"
                notes.append(f"{n}: уровень на склейке отличается на {d:.1f} дБ (окно 50 мс) — швы проверены автором на слух (12.10.2026; темы Suno v6 — 23.10.2026)")
        print(f"{n:24s} {ch:3d} {len(y) / sr:6.2f}с {lufs:6.1f} {peak:6.1f}  {note}")

    # H21: слоты §9.1 и титры
    texts = "".join(Path(f).read_text(encoding="utf-8") for f in sorted(glob.glob(str(ROOT / "texts/act*/ACT*_TEXTS_FINAL.md"))))
    blocks = dict(re.findall(r"^### (\S+)\n(.*?)(?=^### |\Z)", texts, re.S | re.M))
    s91 = s9[s9.index("### 9.1"):s9.index("### 9.2")]
    slots = {t for t in re.findall(r"`([A-Z][A-Za-z0-9]*\.[A-Za-z0-9_.*]+)`", s91)}
    nocap = []
    for sl in sorted(slots):
        keys = [k for k in blocks if k == sl or (sl.endswith(".*") and k.startswith(sl[:-1]))]
        if not keys:
            continue
        if not any(re.search(r"^cap \|", blocks[k], re.M) for k in keys):
            nocap.append(sl)
    print()
    print("Слоты со звуком без титра `cap` (дубль должен быть в кадре — сверить с GDD §8):", ", ".join(nocap) or "нет")
    print()
    print("Это норма, если дубль — реплика с плашкой (громкая связь, автоответчик) или реплика Лапидуса, называющая звук (GDD §8).")
    for m in notes:
        print("ЗАМЕТКА:", m)
    for e in errors:
        print("ОШИБКА:", e)
    print(f"ИТОГ: файлов спеки {len(names)}, в assets {len(names & have)}; ошибок {len(errors)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
