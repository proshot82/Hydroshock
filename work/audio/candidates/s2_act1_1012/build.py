#!/usr/bin/env python3
"""Пакет З2 (Акт I): из raw/ (ElevenLabs и синтез) — версии для прослушки в listen/.

  python work/audio/candidates/s2_act1_1012/build.py

Эффекты — моно, −16 LUFS, пик ≤ −1,5 dBFS (tools/audio/finish.py); амбиенты — стерео, −26 LUFS
(тихо, под текст), для прослушки склеены дважды подряд (шов петли на 0:30); блипы — как есть
(пик −6 dBFS, как блипы BJ2), плюс демо «строка печатается». Сборные звуки: звёзды ×4 из одного
щелчка ElevenLabs; трубка = щелчок ElevenLabs + гудок 425 Гц. Душ (предложение, нет в спеке) — петля
−20 LUFS; демо начала игры: душ → удар обрывает воду → тишина номера.
"""
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAW, OUT = HERE / "raw", HERE / "listen"
SR = 44100
FINISH = [sys.executable, str(ROOT / "tools/audio/finish.py")]
rng = np.random.default_rng(317)

# имя: (длина, затухание) — по спеке §9.1
SFX = {
    "sfx_shock_thud": (2.5, 0.4, [1, 2, 3]),
    "sfx_shower_sigh": (1.0, 0.2, [1, 2, 3]),
    "sfx_plunger_pop": (0.5, 0.1, [1, 2, 3]),
    "sfx_foam_swell": (1.5, 0.3, [1, 2, 3]),
    "sfx_phone_pickup": (1.0, 0.1, [1, 3]),
    "sfx_stars_fold": (1.5, 0.1, [1]),
    "sfx_trolley_creak": (1.5, 0.3, [1, 2, 3]),
    "sfx_crowd_part": (2.0, 0.3, [1, 2, 3]),
    "sfx_pa_chime": (1.5, 0.2, [1]),
}


def run(src, dst, *args):
    subprocess.run([*FINISH, str(src), str(dst), *args], check=True)


def mp3(wav_path, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path), "-b:a", "192k", str(dst)], check=True)


def load(name, mono=True):
    y, _ = librosa.load(RAW / name, sr=SR, mono=mono)
    return y


def write_tmp(y, name):
    p = HERE / "tmp" / name
    p.parent.mkdir(exist_ok=True)
    sf.write(p, y.T if y.ndim > 1 else y, SR, subtype="PCM_24")
    return p


def stars(spacing, name):
    """Четыре щелчка латунных петель из одного: каждый чуть иной по высоте и силе."""
    click = load("star_click_1.mp3")
    on = int(0.13 * SR)
    click = click[on: on + int(0.30 * SR)]
    click[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    out = np.zeros(int((0.05 + spacing * 3 + 0.35) * SR))
    for i in range(4):
        c = librosa.effects.pitch_shift(click, sr=SR, n_steps=float(rng.uniform(-0.6, 0.6)))
        s = int((0.05 + i * spacing + rng.uniform(-0.02, 0.02)) * SR)
        out[s: s + len(c)] += c * rng.uniform(0.8, 1.0)
    return write_tmp(out, name)


def phone():
    """Щелчок трубки (ElevenLabs, вариант 3) + короткий гудок соединения 425 Гц через «трубку»."""
    click = load("sfx_phone_pickup_3.mp3")[: int(0.25 * SR)]
    t = np.arange(int(0.35 * SR)) / SR
    tone = 0.25 * np.sin(2 * np.pi * 425 * t)
    tone[: 300] *= np.linspace(0, 1, 300)
    tone[-600:] *= np.linspace(1, 0, 600)
    out = np.zeros(int(0.75 * SR))
    out[: len(click)] += click
    s = int(0.32 * SR)
    out[s: s + len(tone)] += tone
    return write_tmp(out, "phone4.wav")


def amb(name):
    y = load(name, mono=False)
    p = write_tmp(np.concatenate([y, y], axis=1), name.replace(".mp3", "_x2.wav"))
    lufs = "-20" if name.startswith("sfx_") else "-26"
    run(p, OUT / name.replace(".mp3", "_x2.mp3"), "--keep-head", "--lufs", lufs, "--fade", "0")
    a, b = y[:, -2048:], y[:, :2048]
    jump = float(np.abs(y[:, 0] - y[:, -1]).max())
    rms = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    print(f"  шов {name}: скачок отсчёта {jump:.4f}, уровень конец/начало {rms(a):.1f}/{rms(b):.1f} dB")


def blip_demo(name, step=0.058):
    """Строка в 40 знаков: блип на каждый второй знак, паузы на пробелах."""
    b, _ = librosa.load(RAW / f"{name}.wav", sr=SR)
    out = np.zeros(int(2.6 * SR))
    pos = 0.1
    for i in range(22):
        if i in (5, 11, 16):
            pos += step * 1.5
        s = int(pos * SR)
        out[s: s + len(b)] += b * rng.uniform(0.85, 1.0)
        pos += step
    p = write_tmp(out, f"{name}_demo.wav")
    mp3(p, OUT / f"{name}_demo.mp3")


def lufs_gain(y, target):
    import pyloudnorm
    m = pyloudnorm.Meter(SR)
    return y * 10 ** ((target - m.integrated_loudness(y.T if y.ndim > 1 else y)) / 20)


def big_boom(v):
    """Гидроудар «почти взрыв» (замечание автора 12.10.2026): удар ElevenLabs + инфранизкий «бум»
    + гул содрогающегося здания (дрожь 9 Гц) + большой зал (стерео); громче всех эффектов, −12 LUFS."""
    from scipy.signal import butter, sosfilt, fftconvolve
    lp = lambda x, f: sosfilt(butter(4, f, btype="low", fs=SR, output="sos"), x)
    el = load(f"sfx_shock_boom_{v}.mp3")
    on = int(np.argmax(np.abs(el) > np.abs(el).max() * 0.1))
    el = el[max(0, on - 100):]
    n = int(6.5 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    out[: min(n, len(el))] += el[:n] / (np.abs(el).max() + 1e-9)
    f = 68 * np.exp(-t / 0.6) + 32                      # «бум»: тон падает 100 → 32 Гц
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    sub[: int(0.005 * SR)] *= np.linspace(0, 1, int(0.005 * SR))
    out += 0.9 * sub
    rumble = lp(rng.standard_normal(n), 120)
    rumble *= np.exp(-t / 1.6) * (1 + 0.6 * np.sin(2 * np.pi * 9 * t))
    out += 0.5 * rumble / np.abs(rumble).max()
    out = np.tanh(1.6 * out) / np.tanh(1.6)              # мягкое насыщение
    stereo = []
    for ch in range(2):                                    # зал: свой хвост на каждый канал
        m = int(4.0 * SR)
        ir = lp(rng.standard_normal(m), 3500) * np.exp(-np.linspace(0, 7, m))
        ir /= np.sqrt((ir ** 2).sum())
        stereo.append(out + 0.45 * fftconvolve(out, ir)[:n])
    y = np.vstack(stereo)
    y[:, -int(1.0 * SR):] *= np.linspace(1, 0, int(1.0 * SR))
    p = write_tmp(y, f"boom_{v}.wav")
    run(p, OUT / f"sfx_shock_boom_{v}.mp3", "--keep-head", "--lufs", "-12", "--peak", "-1", "--fade", "0")
    return p


def opening(thud_v, boom=None):
    """Демо начала игры: номер, душ льётся; удар — вода обрывается; тишина номера."""
    room = lufs_gain(load("amb_room_1.mp3"), -30)[: 11 * SR]
    shower = lufs_gain(load("sfx_shower_run_1.mp3"), -20)
    thud = lufs_gain(load(f"sfx_shock_thud_{thud_v}.mp3"), -16) if boom is None else \
        lufs_gain(librosa.load(boom, sr=SR, mono=True)[0], -12)
    on = int(np.argmax(np.abs(thud) > np.abs(thud).max() * 0.1))
    thud = thud[max(0, on - 200):]
    cut = int(5.5 * SR)
    sh = shower[:cut].copy()
    sh[-int(0.06 * SR):] *= np.linspace(1, 0, int(0.06 * SR))
    out = np.concatenate([room, np.zeros(max(0, cut + len(thud) - len(room)))])
    out[:cut] += sh[:cut]
    out[cut: cut + len(thud)] += thud[: len(out) - cut]
    out[-SR:] *= np.linspace(1, 0, SR)
    name = f"demo_opening_{thud_v}" if boom is None else f"demo_opening_boom_{thud_v}"
    out = out / max(1.0, np.abs(out).max() / 0.89)
    mp3(write_tmp(out, f"{name}.wav"), OUT / f"{name}.mp3")


def main():
    OUT.mkdir(exist_ok=True)
    for name, (mx, fade, vs) in SFX.items():
        for v in vs:
            run(RAW / f"{name}_{v}.mp3", OUT / f"{name}_{v}.mp3", "--mono", "--max", str(mx), "--fade", str(fade), "--lufs", "-16")
    run(stars(0.32, "stars_a.wav"), OUT / "sfx_stars_fold_a.mp3", "--mono", "--keep-head", "--lufs", "-16")
    run(stars(0.24, "stars_b.wav"), OUT / "sfx_stars_fold_b.mp3", "--mono", "--keep-head", "--lufs", "-16")
    run(phone(), OUT / "sfx_phone_pickup_4.mp3", "--mono", "--lufs", "-16")
    for v in "abc":
        run(RAW / f"sfx_pa_chime_synth_{v}.wav", OUT / f"sfx_pa_chime_synth_{v}.mp3", "--mono", "--lufs", "-16", "--fade", "0.05")
    for v in (1, 2, 3, 4):
        opening(v, big_boom(v))
    for v in (4, 5, 6):
        run(RAW / f"sfx_crowd_part_{v}.mp3", OUT / f"sfx_crowd_part_{v}.mp3", "--mono", "--max", "2.5", "--fade", "0.4", "--lufs", "-16")
    for v in (1, 2, 3):
        amb(f"sfx_shower_run_{v}.mp3")
        opening(v)
    for n in ("amb_room", "amb_lobby"):
        for v in (1, 2, 3):
            amb(f"{n}_{v}.mp3")
    for b in ("blip_iz_a", "blip_iz_b", "blip_pa_a", "blip_pa_b", "blip_guest_a"):
        x, _ = librosa.load(RAW / f"{b}.wav", sr=SR)
        sf.write(OUT / f"{b}.wav", x, SR, subtype="PCM_16")
        blip_demo(b)
    for b in ("blip_lap", "blip_anc"):                     # для сравнения — блипы BJ2
        x, _ = librosa.load(ROOT / f"assets/audio/{b}.ogg", sr=SR)
        sf.write(HERE / "tmp" / f"{b}.wav", x, SR)
        sf.write(RAW / f"{b}_bj2.wav", x, SR)
        blip_demo(f"{b}_bj2")


if __name__ == "__main__":
    main()
