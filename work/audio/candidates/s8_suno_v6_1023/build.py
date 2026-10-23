#!/usr/bin/env python3
"""Пакет З8 (Suno v6): из raw/ — готовые к игре версии в final/ и файлы для прослушки в listen/.

  python work/audio/candidates/s8_suno_v6_1023/build.py [--only имя,имя]

Доводка — та же, что у принятых звуков (спека §9): мелодии — петля tools/music/make_loop.py
(−18 LUFS, длина не короче принятой ≈ на 10 %), музыка ожидания — через «трубку» 220–5500 Гц;
стингеры — tools/audio/finish.py до длины принятого; эффекты — вырезка с первого звука до
длины принятого, моно, −16 LUFS (удар −12, душ и затихание вестибюля −20); амбиенты — петля
30 с с кроссфейдом 2 с, стерео, −26 LUFS; блипы — пик −6 dBFS, как блипы BJ2.
В listen/: <имя>_cur.mp3 — принятый файл из assets/audio/, <имя>_a/_b.mp3 — версии Suno после
доводки, <имя>_a_full/_b_full.mp3 — что Suno выдал целиком (для эффектов: вдруг лучшее не в начале).
Амбиенты и душ для прослушки склеены дважды подряд — шов посередине.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import librosa
import numpy as np
import pyloudnorm
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAW, FINAL, LISTEN = HERE / "raw", HERE / "final", HERE / "listen"
AUD = ROOT / "assets" / "audio"
SR = 44100
PY = sys.executable
STEREO_SFX = {"sfx_shock_thud", "sfx_shower_run", "sfx_lobby_hush"}
LUFS_SFX = {"sfx_shock_thud": -12, "sfx_shower_run": -20, "sfx_lobby_hush": -20}
LOOP_XFADE = {"bgm_deep": 2.0}


def sh(*cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout).strip()[-400:])
    return r.stdout.strip()


def dur(p):
    return float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p))


def mp3(src, dst, twice=False):
    if twice:
        sh("ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "1", "-i", src, "-b:a", "160k", dst)
    else:
        sh("ffmpeg", "-y", "-loglevel", "error", "-i", src, "-b:a", "160k", dst)


def write(y, out, lufs=None, peak=-1.5):
    """y — (каналы, отсчёты); громкость по BS.1770, пик не выше peak; OGG q5."""
    y = np.atleast_2d(y).astype(np.float64)
    if lufs is not None:
        meter = pyloudnorm.Meter(SR, block_size=min(0.4, y.shape[1] / SR * 0.9))
        y *= 10 ** ((lufs - meter.integrated_loudness(y.T)) / 20)
    pk = np.abs(y).max() + 1e-12
    if pk > 10 ** (peak / 20):
        y *= 10 ** (peak / 20) / pk
    with tempfile.NamedTemporaryFile(suffix=".wav") as t:
        sf.write(t.name, y.T, SR, subtype="PCM_24")
        sh("ffmpeg", "-y", "-loglevel", "error", "-i", t.name, "-ar", SR, "-c:a", "libvorbis", "-q:a", "5", out)


def phone_band(src, dst):
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", "highpass=f=220:poles=2,lowpass=f=5500:poles=2", dst)


def music(name, src, out):
    target = dur(AUD / f"{name}.ogg")
    if name == "mus_hold":
        tmp = HERE / "tmp" / f"{src.stem}_phone.wav"
        tmp.parent.mkdir(exist_ok=True)
        phone_band(src, tmp)
        src = tmp
    for k in (0.9, 0.75, 0.6):
        try:
            return sh(PY, ROOT / "tools/music/make_loop.py", src, out, "--min", f"{target * k:.1f}",
                      "--xfade", LOOP_XFADE.get(name, 0.5))
        except RuntimeError:
            continue
    return sh(PY, ROOT / "tools/audio/finish.py", src, out, "--max", f"{target:.2f}", "--fade", "2", "--lufs", "-18") \
        + " (петля не нашлась — просто отрезок с затуханием)"


def sting(name, src, out):
    target = dur(AUD / f"{name}.ogg")
    return sh(PY, ROOT / "tools/audio/finish.py", src, out, "--max", f"{target:.2f}",
              "--fade", f"{min(1.2, target * 0.3):.2f}", "--lufs", "-18")


def first_sound(y, thr_db=-30):
    env = np.abs(y).max(axis=0)
    hop = int(0.005 * SR)
    frames = np.array([env[i:i + hop].max() for i in range(0, len(env) - hop, hop)])
    on = np.flatnonzero(frames > frames.max() * 10 ** (thr_db / 20))
    return max(0, on[0] * hop - int(0.02 * SR)) if len(on) else 0


def sfx(name, src, out):
    target = dur(AUD / f"{name}.ogg")
    stereo = name in STEREO_SFX
    y, _ = librosa.load(src, sr=SR, mono=not stereo)
    y = np.atleast_2d(y)
    if name == "sfx_shower_run":
        return amb_loop(y, out, -20, 10.0)
    s = first_sound(y)
    y = y[:, s:s + int(target * SR)].copy()
    n = int(min(0.4, target * 0.25) * SR)
    y[:, -n:] *= np.linspace(1, 0, n) ** 2
    y[:, :int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
    write(y, out, LUFS_SFX.get(name, -16))
    return f"с {s / SR:.2f} с исходника, {target:.2f} с"


def short(name, src, out):
    """Блипы и звуки интерфейса: самый сильный щелчок трека, длина принятого."""
    target = dur(AUD / f"{name}.ogg")
    y, _ = librosa.load(src, sr=SR, mono=True)
    env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=256)
    peak = int(np.argmax(env)) * 256
    s = max(0, peak - int(0.01 * SR))
    y = y[s:s + int(target * SR)].copy()
    n = max(1, int(target * 0.3 * SR))
    y[-n:] *= np.linspace(1, 0, n) ** 2
    y[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    if name.startswith("blip_"):
        write(y / (np.abs(y).max() + 1e-12) * 10 ** (-6 / 20), out)
    else:
        write(y, out, -16)
    return f"щелчок на {s / SR:.2f} с исходника, {target:.3f} с"


def amb_loop(y, out, lufs, length, xf=2.0):
    """Петля length с: отрезок после первых 5 с, конец сшит с тем, что было до начала."""
    s = min(int(5 * SR), max(0, y.shape[1] - int((length + xf) * SR)))
    s = max(s, int(xf * SR))
    loop = y[:, s:s + int(length * SR)].copy()
    n = int(xf * SR)
    fade = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
    loop[:, -n:] = loop[:, -n:] * (1 - fade) + y[:, s - n:s] * fade
    write(loop, out, lufs)
    return f"петля {s / SR:.1f}–{s / SR + length:.1f} с исходника"


def amb(name, src, out):
    y, _ = librosa.load(src, sr=SR, mono=False)
    y = np.atleast_2d(y)
    if y.shape[0] == 1:
        y = np.vstack([y, y])
    return amb_loop(y, out, -26, 30.0)


KIND = {"music": music, "sting": sting, "sfx": sfx, "short": short, "amb": amb}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = set(filter(None, a.only.split(",")))
    FINAL.mkdir(exist_ok=True)
    LISTEN.mkdir(exist_ok=True)
    report = {}
    for it in json.loads((HERE / "manifest.json").read_text(encoding="utf-8")):
        n, kind = it["name"], it["kind"]
        if only and n not in only:
            continue
        twice = kind == "amb" or n == "sfx_shower_run"
        mp3(AUD / f"{n}.ogg", LISTEN / f"{n}_cur.mp3", twice)
        for v in "ab":
            src = RAW / f"{n}_{v}.mp3"
            if not src.exists():
                print(f"{n}_{v}: нет исходника")
                continue
            out = FINAL / f"{n}_{v}.ogg"
            try:
                msg = KIND[kind](n, src, out)
                mp3(out, LISTEN / f"{n}_{v}.mp3", twice)
                if kind != "music":
                    mp3(src, LISTEN / f"{n}_{v}_full.mp3")
                report[f"{n}_{v}"] = {"ok": True, "note": msg.splitlines()[-1] if msg else "",
                                      "raw_sec": round(dur(src), 1), "sec": round(dur(out), 2)}
            except Exception as e:
                report[f"{n}_{v}"] = {"ok": False, "note": str(e)}
            print(n, v, report[f"{n}_{v}"], flush=True)
    rp = HERE / "build_report.json"
    old = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else {}
    old.update(report)
    rp.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
