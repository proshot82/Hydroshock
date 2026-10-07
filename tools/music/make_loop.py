"""Петля из готового трека: шов по долям, кроссфейд, −18 LUFS, OGG.

Ищет пару долей (начало петли после вступления, конец до концовки), чтобы звук
после конца был максимально похож на звук после начала, а между ними — целое
число тактов (4 доли). Конец петли сшивается с аудио перед её началом
кроссфейдом, поэтому при повторе музыка продолжается без щелчка.

python tools/music/make_loop.py ВХОД.mp3 ВЫХОД.ogg [--min 60] [--xfade 0.5]
Нужны: librosa, soundfile, pyloudnorm, ffmpeg.
"""
import argparse, os, subprocess, sys, tempfile

import librosa
import numpy as np
import pyloudnorm
import soundfile as sf

SR = 44100
LUFS, PEAK_DB = -18.0, -1.5


def beat_features(y, sr, beats):
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512)
    rms = librosa.feature.rms(y=y, hop_length=512)
    feat = np.vstack([chroma, mfcc / 50.0, rms * 10])
    sync = librosa.util.sync(feat, beats, aggregate=np.mean)
    return sync / (np.linalg.norm(sync, axis=0, keepdims=True) + 1e-9)


def find_loop(path, min_len, head_max=12.0, tail_min=3.5):
    y, sr = librosa.load(path, sr=22050, mono=True)
    dur = len(y) / sr
    _, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    times = librosa.frames_to_time(beats, sr=sr, hop_length=512)
    f = beat_features(y, sr, beats)
    win = 8  # сравниваем 8 долей после точки
    best = None
    for i, ts in enumerate(times):
        if ts < 0.6 or ts > head_max:
            continue
        for j in range(i + 4, len(times)):
            te = times[j]
            if (j - i) % 4 or te - ts < min_len or te > dur - tail_min:
                continue
            if j + win > f.shape[1] or i + win > f.shape[1]:
                continue
            # после конца должно звучать то же, что после начала; до — тоже
            sim = np.mean(np.sum(f[:, i:i + win] * f[:, j:j + win], axis=0))
            pre = np.mean(np.sum(f[:, max(i - 4, 0):i] * f[:, j - 4:j], axis=0)) if i >= 4 else sim
            score = 0.7 * sim + 0.3 * pre + 0.002 * (te - ts)
            if best is None or score > best[0]:
                best = (score, ts, te, j - i)
    return best, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--min", type=float, default=60.0, help="минимальная длина петли, с")
    ap.add_argument("--xfade", type=float, default=0.5)
    a = ap.parse_args()

    best, dur = find_loop(a.src, a.min)
    if not best:
        sys.exit(f"не нашёл петлю ≥ {a.min} с в {a.src} ({dur:.1f} с)")
    score, ts, te, nbeats = best

    y, sr = librosa.load(a.src, sr=SR, mono=False)
    if y.ndim == 1:
        y = np.vstack([y, y])
    s, e, xf = int(round(ts * SR)), int(round(te * SR)), int(a.xfade * SR)
    xf = min(xf, s)
    loop = y[:, s:e].copy()
    if xf:
        fade = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2  # равная мощность
        loop[:, -xf:] = loop[:, -xf:] * (1 - fade) + y[:, s - xf:s] * fade

    meter = pyloudnorm.Meter(SR)
    lufs = meter.integrated_loudness(loop.T)
    loop *= 10 ** ((LUFS - lufs) / 20)
    up = librosa.resample(loop, orig_sr=SR, target_sr=SR * 4)  # пик с передискретизацией
    peak = 20 * np.log10(np.max(np.abs(up)) + 1e-12)
    if peak > PEAK_DB:
        loop *= 10 ** ((PEAK_DB - peak) / 20)
    final_lufs = meter.integrated_loudness(loop.T)

    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "loop.wav")
        sf.write(wav, loop.T, SR, subtype="PCM_24")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "5",
                        "-ar", str(SR), a.dst], check=True)
    print(f"{os.path.basename(a.dst)}: петля {ts:.2f}–{te:.2f} с ({te - ts:.1f} с, {nbeats} долей), "
          f"сходство {score:.3f}, громкость {final_lufs:.1f} LUFS, пик ≤ {PEAK_DB} dBFS")


if __name__ == "__main__":
    main()
