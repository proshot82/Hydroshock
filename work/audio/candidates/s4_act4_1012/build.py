#!/usr/bin/env python3
"""Пакет З4 (Акт IV и финальная вода): из raw/ — версии для прослушки в listen/ и демо сцен.

  python work/audio/candidates/s4_act4_1012/build.py

Эффекты — моно, −16 LUFS; амбиент низа — стерео, −26 LUFS, склеен дважды (шов на 0:30); блипы Кухтулху —
синтез, демо «строка печатается». Каскад финала — фонтан ElevenLabs + писк резиновой уточки на взлёте.
Демо: появление Кухтулху (обрыв bgm_deep → скрип пера → bgm_below), пуск воды (маховик → выдох здания +
sting_water), финальный монтаж — три варианта музыки (А bgm_epilogue, Б без музыки, В bgm_below).
"""
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import pyloudnorm
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAW, OUT, TMP = HERE / "raw", HERE / "listen", HERE / "tmp"
AUD = ROOT / "assets" / "audio"
SR = 44100
FINISH = [sys.executable, str(ROOT / "tools/audio/finish.py")]
METER = pyloudnorm.Meter(SR)

SFX = {
    "sfx_wet_steps": (3.0, 0.4), "sfx_wet_stamp": (0.4, 0.1), "sfx_pen_scratch": (1.5, 0.2),
    "sfx_door_clicks": (1.6, 0.2), "sfx_pen_roll": (1.0, 0.2), "sfx_soap_smear": (0.6, 0.1),
    "sfx_seal_tear": (0.5, 0.1), "sfx_valve_turn": (4.0, 0.3), "sfx_building_exhale": (8.0, 1.5),
    "sfx_pa_drown": (3.0, 0.4), "sfx_drums_turn": (3.0, 0.5), "sfx_fin_shower": (4.0, 0.5),
    "sfx_fin_spring": (3.0, 0.5),
}


def run(src, dst, *args):
    subprocess.run([*FINISH, str(src), str(dst), *args], check=True, stdout=subprocess.DEVNULL)


def tmp(y, name):
    TMP.mkdir(exist_ok=True)
    p = TMP / name
    sf.write(p, y.T if y.ndim > 1 else y, SR, subtype="PCM_24")
    return p


def mp3(y, dst):
    y = y / max(1.0, np.abs(y).max() / 0.89)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp(y, dst.stem + ".wav")), "-b:a", "192k", str(dst)], check=True)


def load(path, mono=True):
    y, _ = librosa.load(path, sr=SR, mono=mono)
    return y


def at(y, lufs):
    return y * 10 ** ((lufs - METER.integrated_loudness(y.T if y.ndim > 1 else y)) / 20)


def trim_head(y):
    on = int(np.argmax(np.abs(y) > np.abs(y).max() * 0.05))
    return y[max(0, on - 200):]


def cascade(v, duck):
    """Фонтан бьёт в потолок; на взлёте (1,1 с) пищит уточка — «Утки! Уууу-у!»."""
    c = trim_head(load(RAW / f"sfx_fin_cascade_{v}.mp3"))[: 3 * SR].copy()
    c[-int(0.5 * SR):] *= np.linspace(1, 0, int(0.5 * SR))
    d = trim_head(load(RAW / f"duck_squeak_{duck}.mp3"))[: int(0.45 * SR)]
    c, d = at(c, -18), at(d, -14)
    s = int(1.1 * SR)
    c[s: s + len(d)] += d[: len(c) - s]
    return tmp(c, f"cascade_{v}.wav")


def place(track, y, t):
    s = int(t * SR)
    n = min(len(y), len(track) - s)
    track[s: s + n] += y[:n]


def demo_come_out(pen_v):
    deep = load(AUD / "bgm_deep.ogg")[20 * SR: 35 * SR].copy()
    deep[: SR] *= np.linspace(0, 1, SR)
    deep[-200:] *= np.linspace(1, 0, 200)
    pen = at(trim_head(load(RAW / f"sfx_pen_scratch_{pen_v}.mp3"))[: int(1.5 * SR)], -20)
    below = load(AUD / "bgm_below.ogg")[: 15 * SR].copy()
    below[-2 * SR:] *= np.linspace(1, 0, 2 * SR)
    out = np.zeros(len(deep) + int(2.0 * SR) + len(below))
    place(out, deep, 0)
    place(out, pen, len(deep) / SR + 0.3)
    place(out, below, len(deep) / SR + 2.0)
    mp3(out, OUT / f"demo_come_out_pen_{pen_v}.mp3")


def demo_valve(v):
    valve = at(trim_head(load(RAW / f"sfx_valve_turn_{v}.mp3"))[: 4 * SR], -16)
    exhale = at(trim_head(load(RAW / f"sfx_building_exhale_{v}.mp3"))[: 8 * SR], -16)
    sting = at(load(AUD / "sting_water.ogg"), -18)
    out = np.zeros(int(13.5 * SR))
    place(out, valve, 0)
    place(out, exhale, 3.6)
    place(out, sting, 4.6)
    out[-SR:] *= np.linspace(1, 0, SR)
    mp3(out, OUT / f"demo_valve_{v}.mp3")


def demo_finale(music):
    """Громкая связь тонет → четыре кадра монтажа по ~3,5 с; музыка — по варианту."""
    pa = at(trim_head(load(RAW / "sfx_pa_drown_2.mp3"))[: 3 * SR], -16)
    shots = [at(trim_head(load(RAW / "sfx_fin_shower_1.mp3"))[: int(3.6 * SR)], -16),
             at(load(cascade(1, 3)), -16),
             at(trim_head(load(RAW / "sfx_drums_turn_2.mp3"))[: 3 * SR], -16),
             at(trim_head(load(RAW / "sfx_fin_spring_2.mp3"))[: 3 * SR], -16)]
    total = 3.2 + sum(len(s) / SR + 0.3 for s in shots) + 3.0
    out = np.zeros(int(total * SR))
    place(out, pa, 0)
    t = 3.2
    for s in shots:
        s = s.copy()
        s[-int(0.25 * SR):] *= np.linspace(1, 0, int(0.25 * SR))
        place(out, s, t)
        t += len(s) / SR + 0.3
    if music:
        m = at(load(AUD / f"{music}.ogg")[: int((total - 3.2) * SR)], -24)
        m[: int(0.8 * SR)] *= np.linspace(0, 1, int(0.8 * SR))
        m[-2 * SR:] *= np.linspace(1, 0, 2 * SR)
        place(out, m, 3.2)
    out[-SR:] *= np.linspace(1, 0, SR)
    mp3(out, OUT / f"demo_finale_{ {'bgm_epilogue': 'A', None: 'B', 'bgm_below': 'V'}[music] }.mp3")


def blip_demo(name, step=0.058):
    b = load(RAW / f"{name}.wav")
    out = np.zeros(int(2.6 * SR))
    pos = 0.1
    for i in range(22):
        if i in (5, 11, 16):
            pos += step * 1.5
        place(out, b, pos)
        pos += step
    mp3(out, OUT / f"{name}_demo.mp3")


def main():
    OUT.mkdir(exist_ok=True)
    for name, (mx, fade) in SFX.items():
        for v in (1, 2, 3):
            run(RAW / f"{name}_{v}.mp3", OUT / f"{name}_{v}.mp3", "--mono", "--max", str(mx), "--fade", str(fade), "--lufs", "-16")
    for v, duck in ((1, 3), (2, 1), (3, 3)):
        run(cascade(v, duck), OUT / f"sfx_fin_cascade_{v}.mp3", "--mono", "--keep-head", "--lufs", "-16", "--fade", "0")
    for v in (1, 2, 3):
        y = load(RAW / f"amb_below_{v}.mp3", mono=False)
        run(tmp(np.concatenate([y, y], axis=1), f"below_{v}.wav"), OUT / f"amb_below_{v}_x2.mp3", "--loop", "--lufs", "-26")
        demo_come_out(v)
        demo_valve(v)
    for m in ("bgm_epilogue", None, "bgm_below"):
        demo_finale(m)
    for b in ("blip_kuh_a", "blip_kuh_b"):
        blip_demo(b)


if __name__ == "__main__":
    main()
