#!/usr/bin/env python3
"""Синтез точных коротких звуков: блипы печати текста, позывной громкой связи.

Блипы BJ2 (blip_lap 263 Гц, blip_anc 145 Гц) — короткие тоновые всплески с яркими
обертонами; блипы BJ3 сделаны в той же манере, каждому голосу — своя высота и тембр.

  python tools/audio/synth.py ПАПКА        # все звуки в ПАПКА/*.wav

Нужны: numpy, scipy, soundfile.
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(1908)


def t_(sec):
    return np.arange(int(sec * SR)) / SR


def band(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def env_ar(n, attack, release_pow=1.0):
    a = max(1, int(attack * SR))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e[a:] = np.linspace(1, 0, n - a) ** release_pow
    return e


def pulse(f0, sec, duty=0.5, harmonics=12):
    """Ограниченный по полосе прямоугольник (сумма гармоник) — «электронный» тон BJ2."""
    t = t_(sec)
    x = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        amp = np.sin(np.pi * k * duty) / k
        x += amp * np.sin(2 * np.pi * f0 * k * t)
    return x / np.abs(x).max()


def norm(x, peak_db=-6.0):
    return x / (np.abs(x).max() + 1e-12) * 10 ** (peak_db / 20)


def room(x, sec=0.6, wet=0.25, lo=200, hi=6000):
    n = int(sec * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 8, n))
    ir = band(ir, lo, hi, 2)
    ir /= np.sqrt((ir ** 2).sum())
    y = np.concatenate([x, np.zeros(n)])
    return y + wet * fftconvolve(y, ir)[: len(y)]


# ---- блипы -----------------------------------------------------------------

def blip_iz():
    """Изольда: сухой высокий щелчок — узкий прямоугольник 660 Гц, 40 мс, резкий спад."""
    x = pulse(660, 0.040, duty=0.3, harmonics=10) * env_ar(int(0.040 * SR), 0.002, 2.0)
    return norm(x, -6)


def blip_iz_b():
    """Вариант: 590 Гц, чуть мягче."""
    x = pulse(590, 0.045, duty=0.4, harmonics=8) * env_ar(int(0.045 * SR), 0.002, 1.5)
    return norm(x, -6)


def blip_pa():
    """Громкая связь: хрипловатый радиощелчок — тон 350 Гц + треск, полоса динамика 400–3000 Гц."""
    n = int(0.050 * SR)
    x = pulse(350, 0.050, duty=0.5, harmonics=14) + 0.6 * rng.standard_normal(n)
    x = band(x, 400, 3000) * env_ar(n, 0.003, 1.2)
    x = np.tanh(3 * x / np.abs(x).max())                   # перегруз старого динамика
    return norm(x, -6)


def blip_pa_b():
    """Вариант: больше треска, ниже тон (300 Гц)."""
    n = int(0.055 * SR)
    x = pulse(300, 0.055, duty=0.5, harmonics=14) + 1.0 * rng.standard_normal(n)
    x = band(x, 500, 2800) * env_ar(n, 0.002, 1.0)
    x = np.tanh(4 * x / np.abs(x).max())
    return norm(x, -6)


def blip_guest():
    """Гости, официант: нейтральный мягкий тон 392 Гц (соль), треугольник, 45 мс."""
    n = int(0.045 * SR)
    t = t_(0.045)
    x = sum(((-1) ** k) / (2 * k + 1) ** 2 * np.sin(2 * np.pi * 392 * (2 * k + 1) * t) for k in range(6))
    x = x * env_ar(n, 0.003, 1.5)
    return norm(x, -6)


# ---- позывной громкой связи ------------------------------------------------

def bell(f, sec, bright=1.0):
    """Колокольчик-вибрафон: несколько неровных обертонов с разным затуханием."""
    t = t_(sec)
    partials = [(1.0, 1.0, 1.6), (2.0, 0.35 * bright, 3.0), (3.98, 0.18 * bright, 5.0), (6.1, 0.06 * bright, 8.0)]
    x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-d * t) for r, a, d in partials)
    x[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return x


def mic_click():
    n = int(0.03 * SR)
    x = rng.standard_normal(n) * np.exp(-np.linspace(0, 12, n))
    return band(x, 300, 4000) * 0.8


def pa_chime(notes, gap=0.32, tail=0.9):
    """Щелчок микрофона, три ноты, «динамик» 300–5000 Гц, зал."""
    total = 0.12 + gap * (len(notes) - 1) + tail
    out = np.zeros(int(total * SR))
    c = mic_click()
    out[: len(c)] += c
    for i, f in enumerate(notes):
        s = int((0.12 + i * gap) * SR)
        b = bell(f, total - 0.12 - i * gap)
        out[s: s + len(b)] += b[: len(out) - s]
    hum = 0.02 * np.sin(2 * np.pi * 50 * t_(total)) * np.linspace(1, 0.3, len(out))
    out = band(out + hum, 300, 5000, 2)
    out = room(out, 0.9, 0.35)
    return norm(out, -3)


SOUNDS = {
    "blip_iz_a": blip_iz,
    "blip_iz_b": blip_iz_b,
    "blip_pa_a": blip_pa,
    "blip_pa_b": blip_pa_b,
    "blip_guest_a": blip_guest,
    # нисходящее «динь-дон-дон»: до–ля–фа (мажорное трезвучие сверху вниз)
    "sfx_pa_chime_synth_a": lambda: pa_chime([1046.5, 880.0, 698.5]),
    # восходящее «динь-динь-дон»: соль–си–ре
    "sfx_pa_chime_synth_b": lambda: pa_chime([784.0, 987.8, 1174.7]),
    # вокзальное: ми–до–соль ниже
    "sfx_pa_chime_synth_c": lambda: pa_chime([659.3, 523.3, 392.0], gap=0.38),
}


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in SOUNDS.items():
        x = fn()
        sf.write(out / f"{name}.wav", x, SR, subtype="PCM_24")
        print(name, f"{len(x) / SR:.3f} с")


if __name__ == "__main__":
    main()
