#!/usr/bin/env python3
"""Сэмплер BJ3: партитура в коде → WAV/OGG из записей живых инструментов.

Библиотека — VSCO 2 Community Edition (CC0), путь — переменная окружения
BJ3_SAMPLES (по умолчанию /home/user/samples/vsco2). В git сэмплы не хранятся:
  git clone --depth 1 https://github.com/sgossner/VSCO-2-CE <путь>

Ноты в именах файлов VSCO: «A#3», «Gb2» и т. п. Октавная нумерация в VSCO у разных
инструментов разная (у кларнета, трубы, контрабаса и маримбы имя на октаву ниже
звучания), поэтому сдвиг октавы определяется по реальной высоте одного сэмпла
(спектр, произведение гармоник) и округляется до 12 полутонов.
Нота играется ближайшим по высоте сэмплом нужного слоя динамики, транспонированным
пересэмплированием (без растяжения времени — как у настоящего сэмплера).
"""
import os
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

SR = 44100
LIB = Path(os.environ.get("BJ3_SAMPLES", "/home/user/samples/vsco2"))
NOTE = re.compile(r"(?<![A-Za-z])([A-Ga-g])([#b]?)(-?\d)(?![0-9])")
STEP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def name_to_midi(name):
    m = None
    for m in NOTE.finditer(name):
        pass                                    # последнее совпадение — нота
    if not m:
        return None
    n = STEP[m.group(1).upper()] + {"#": 1, "b": -1, "": 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + n


def measure_midi(x):
    """Высота сэмпла: спектр после атаки, произведение гармоник."""
    i = int(np.argmax(np.abs(x)))
    seg = x[i + int(0.05 * SR): i + int(0.05 * SR) + 8192]
    if len(seg) < 2048:
        return None
    seg = seg * np.hanning(len(seg))
    sp = np.abs(np.fft.rfft(seg, 1 << 16))
    fr = np.fft.rfftfreq(1 << 16, 1 / SR)
    h = sp.copy()
    for k in (2, 3):
        h[: len(sp) // k] *= sp[::k][: len(sp) // k]
    lo = np.searchsorted(fr, 30)
    f = fr[lo + int(np.argmax(h[lo: len(sp) // 3]))]
    return 69 + 12 * np.log2(f / 440)


class Instrument:
    """Набор сэмплов: каталог, фильтр имени, слой динамики (подстрока)."""

    def __init__(self, subdir, include="", layer="", gain=1.0, release=0.12, attack_trim=0.0):
        self.samples = {}
        self.gain, self.release, self.attack_trim = gain, release, attack_trim
        for p in sorted((LIB / subdir).rglob("*.wav")):
            if include and include not in p.name:
                continue
            if layer and layer not in p.name:
                continue
            midi = name_to_midi(p.stem)
            if midi is not None:
                self.samples.setdefault(midi, []).append(p)
        if not self.samples:
            raise ValueError(f"нет сэмплов: {subdir} {include} {layer}")
        self._cache = {}
        self._rr = 0
        keys = sorted(self.samples)
        probe = keys[len(keys) // 2]
        heard = measure_midi(self._load(self.samples[probe][0]))
        shift = 0 if heard is None else int(round((heard - probe) / 12)) * 12
        if shift:
            self.samples = {m + shift: v for m, v in self.samples.items()}
        self.octave_shift = shift

    def _load(self, path):
        if path not in self._cache:
            x, sr = sf.read(path, always_2d=True)
            x = x.mean(axis=1) if x.shape[1] > 1 else x[:, 0]
            if sr != SR:
                x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
            if self.attack_trim:
                x = x[int(self.attack_trim * SR):]
            self._cache[path] = x.astype(np.float32)
        return self._cache[path]

    def note(self, midi, seconds, vel=0.8):
        root = min(self.samples, key=lambda m: (abs(m - midi), m))
        paths = self.samples[root]
        self._rr += 1
        x = self._load(paths[self._rr % len(paths)])
        ratio = 2 ** ((midi - root) / 12)
        idx = np.arange(0, len(x) - 1, ratio)
        y = np.interp(idx, np.arange(len(x)), x)
        n = int((seconds + self.release) * SR)
        y = y[:n] if len(y) >= n else np.pad(y, (0, n - len(y)))
        rel = int(self.release * SR)
        if rel:
            y[-rel:] *= np.linspace(1, 0, rel) ** 2
        return (y * vel * self.gain).astype(np.float32)


class Song:
    def __init__(self, bpm, beats):
        self.bpm, self.beats = bpm, beats
        self.length = int(self.sec(beats) * SR)
        self.tracks = []

    def sec(self, beats):
        return beats * 60.0 / self.bpm

    def track(self, pan=0.0, wet=0.2):
        t = {"buf": np.zeros(self.length + SR * 8, np.float32), "pan": pan, "wet": wet}
        self.tracks.append(t)
        return t

    def play(self, t, inst, beat, dur, midi, vel=0.8, swing=0.0):
        if swing and (beat * 2) % 2 == 1:
            beat += swing
        y = inst.note(midi, self.sec(dur), vel)
        s = int(self.sec(beat) * SR)
        t["buf"][s:s + len(y)] += y

    def render(self, out_path, loop=True, reverb_s=1.6, phone=False, master=0.89, lufs=-18):
        rng = np.random.default_rng(17)
        ir_n = int(reverb_s * SR)
        ir = rng.standard_normal(ir_n) * np.exp(-np.linspace(0, 7, ir_n))
        ir[0] = 0
        ir /= np.sqrt((ir ** 2).sum())
        mix = np.zeros((2, self.length + SR * 8), np.float32)
        for t in self.tracks:
            dry = t["buf"]
            wet = fftconvolve(dry, ir)[: len(dry)] * t["wet"]
            l, r = np.cos((t["pan"] + 1) * np.pi / 4), np.sin((t["pan"] + 1) * np.pi / 4)
            mix[0] += (dry + wet) * l
            mix[1] += (dry + wet) * r
        if loop:                                # хвост после конца — в начало: бесшовная петля
            tail = mix[:, self.length:]
            mix = mix[:, : self.length].copy()
            mix[:, : tail.shape[1]] += tail[:, : self.length]
        else:
            nz = np.where(np.abs(mix).max(axis=0) > 1e-4)[0]
            mix = mix[:, : (nz[-1] + 1 if len(nz) else self.length)]
        if phone:                               # маленький динамик трубки: срез низа и верха, моно, без искажений
            sos = butter(2, [220, 5500], btype="band", fs=SR, output="sos")
            m = sosfilt(sos, mix.mean(axis=0))
            mix = np.vstack([m, m])
        peak = np.abs(mix).max()
        mix = mix / peak * master if peak else mix
        wav = Path(out_path).with_suffix(".wav")
        sf.write(wav, mix.T, SR)
        # громкость всей музыки игры — одна: интегральная −18 LUFS, истинный пик −1,5 dBFS
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                        "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11", "-ar", str(SR),
                        "-c:a", "libvorbis", "-q:a", "5", str(out_path)], check=True)
        wav.unlink()
        return mix.shape[1] / SR


def chord(root, kind):
    """Аккорд от MIDI-корня: maj7, m7, 7, maj6, dim, maj, m."""
    shapes = {"maj7": (0, 4, 7, 11), "m7": (0, 3, 7, 10), "7": (0, 4, 7, 10), "6": (0, 4, 7, 9),
              "m6": (0, 3, 7, 9), "dim": (0, 3, 6, 9), "maj": (0, 4, 7), "m": (0, 3, 7)}
    return [root + i for i in shapes[kind]]


class Piano(Instrument):
    """Upright Piano VSCO: имя файла — номер строки в MappingChart.txt (000=21 …), слои dyn1–dyn3."""

    def __init__(self, layer="dyn2", gain=1.0, release=0.25):
        d = LIB / "Keys" / "Upright Piano"
        mapping = {}
        for line in (d / "MappingChart.txt").read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"^(\d{3})=(\d+)", line.strip())
            if m:
                mapping[m.group(1)] = int(m.group(2))
        self.samples, self._cache, self._rr = {}, {}, 0
        self.gain, self.release, self.attack_trim, self.octave_shift = gain, release, 0.0, 0
        for p in sorted(d.glob(f"Player_{layer}_*.wav")):
            key = mapping.get(p.stem[-3:])
            if key is not None:
                self.samples.setdefault(key, []).append(p)
        if not self.samples:
            raise ValueError("нет сэмплов фортепиано")


class Perc:
    """Перкуссия без высоты: набор файлов, круговая смена (round robin)."""

    def __init__(self, files, gain=1.0, length=0.6):
        self.files = [LIB / f for f in files]
        self.gain, self.length, self._rr, self._cache = gain, length, 0, {}

    def note(self, midi, seconds, vel=0.8):
        self._rr += 1
        p = self.files[self._rr % len(self.files)]
        if p not in self._cache:
            x, sr = sf.read(p, always_2d=True)
            x = x.mean(axis=1)
            if sr != SR:
                x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
            self._cache[p] = x[: int(self.length * SR)].astype(np.float32)
        y = self._cache[p].copy()
        f = min(len(y), int(0.03 * SR))
        y[-f:] *= np.linspace(1, 0, f)
        return y * vel * self.gain
