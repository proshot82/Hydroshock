#!/usr/bin/env python3
"""Доводка короткого звука: срез тишины в начале, длина, затухание, громкость, OGG/MP3.

  python tools/audio/finish.py ВХОД ВЫХОД.ogg [--max 3.5] [--fade 1.0] [--lufs -18]
                               [--peak -1.5] [--mono] [--keep-head]

Громкость меряется по ITU-R BS.1770 (pyloudnorm); если после нормировки пик выше
--peak, громкость снижается до пика. Формат выхода — по расширению (.ogg q5 / .mp3 192k).
Нужны: librosa, soundfile, pyloudnorm, ffmpeg.
"""
import argparse
import subprocess
import tempfile

import librosa
import numpy as np
import pyloudnorm
import soundfile as sf

SR = 44100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--max", type=float, default=0.0, help="длина, с (0 — не резать)")
    ap.add_argument("--fade", type=float, default=0.05, help="затухание в конце, с")
    ap.add_argument("--lufs", type=float, default=-18.0)
    ap.add_argument("--peak", type=float, default=-1.5)
    ap.add_argument("--mono", action="store_true")
    ap.add_argument("--keep-head", action="store_true", help="не срезать тишину в начале")
    a = ap.parse_args()

    y, _ = librosa.load(a.src, sr=SR, mono=a.mono)
    y = np.atleast_2d(y)                                   # (каналы, отсчёты)
    if not a.keep_head:
        env = np.abs(y).max(axis=0)
        on = np.flatnonzero(env > 10 ** (-50 / 20))
        start = max(0, on[0] - int(0.005 * SR)) if len(on) else 0
        y = y[:, start:]
    if a.max:
        y = y[:, : int(a.max * SR)]
    n = min(int(a.fade * SR), y.shape[1])
    if n:
        y[:, -n:] *= np.linspace(1, 0, n) ** 2
    y[:, : int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))

    meter = pyloudnorm.Meter(SR, block_size=min(0.4, y.shape[1] / SR * 0.9))
    loud = meter.integrated_loudness(y.T)
    gain = 10 ** ((a.lufs - loud) / 20)
    pk = np.abs(y).max() * gain
    lim = 10 ** (a.peak / 20)
    if pk > lim:
        gain *= lim / pk
    y = y * gain

    with tempfile.NamedTemporaryFile(suffix=".wav") as t:
        sf.write(t.name, y.T, SR, subtype="PCM_24")
        codec = ["-c:a", "libvorbis", "-q:a", "5"] if a.out.endswith(".ogg") else ["-c:a", "libmp3lame", "-b:a", "192k"]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", t.name, "-ar", str(SR), *codec, a.out], check=True)
    final = meter.integrated_loudness(y.T)
    print(f"{a.out}: {y.shape[1] / SR:.2f} с, {final:.1f} LUFS, пик {20 * np.log10(np.abs(y).max()):.1f} dBFS")


if __name__ == "__main__":
    main()
