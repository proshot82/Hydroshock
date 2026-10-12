#!/usr/bin/env python3
"""Пакет З3 (Акты II–III): из raw/ — версии для прослушки в listen/.

  python work/audio/candidates/s3_act23_1012/build.py

Эффекты — моно, −16 LUFS, пик ≤ −1,5 dBFS; амбиенты — стерео, −26 LUFS, склеены дважды (шов на 0:30).
Сборные: стук ×3 из одного удара ElevenLabs + тишина; «вестибюль затихает» из принятого amb_lobby
(гул обрывается до тишины). Писк табло — синтез (tools/audio/synth.py).
"""
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAW, OUT, TMP = HERE / "raw", HERE / "listen", HERE / "tmp"
SR = 44100
FINISH = [sys.executable, str(ROOT / "tools/audio/finish.py")]

# имя: (длина, затухание, варианты ElevenLabs) — спека §9.1
SFX = {
    "sfx_pump_dry": (3.0, 0.5, [1, 2, 3]),
    "sfx_phone_ring": (2.0, 0.3, [1, 2, 3]),
    "sfx_latch_click": (0.4, 0.1, [1, 2, 3]),
    "sfx_tag_fold": (0.8, 0.15, [1, 2, 3]),
    "sfx_plunger_press": (0.6, 0.1, [1, 2, 3]),
    "sfx_paint_scrape": (2.0, 0.3, [1, 2, 3]),
    "sfx_token_drop": (0.6, 0.1, [1, 2, 3]),
    "sfx_drawer_click": (0.6, 0.1, [1, 2, 3]),
    "sfx_key_door": (1.5, 0.3, [1, 2, 3]),
    "sfx_trolley_jam": (1.2, 0.3, [1, 2, 3]),
    "sfx_wheel_bump": (1.0, 0.2, [1, 2, 3]),
    "sfx_board_lay": (1.5, 0.3, [1, 2, 3]),
    "sfx_suction_glass": (1.2, 0.2, [1, 2, 3]),
    "sfx_switch": (0.4, 0.1, [1, 2, 3]),
    "sfx_lift_down": (4.0, 0.8, [1, 2, 3]),
    "sfx_lift_up": (4.0, 0.5, [1, 2, 3]),
    "sfx_stamp": (0.4, 0.1, [1, 2, 3]),
    "sfx_bottle_catch": (0.8, 0.15, [1, 2, 3]),
    "sfx_lobby_hush": (3.0, 0.3, [1, 2, 3]),
    "sfx_descent": (5.0, 0.8, [1, 2, 3]),
    "sfx_grille_shut": (0.8, 0.15, [1, 2, 3]),
}


def run(src, dst, *args):
    subprocess.run([*FINISH, str(src), str(dst), *args], check=True, stdout=subprocess.DEVNULL)


def tmp(y, name):
    TMP.mkdir(exist_ok=True)
    p = TMP / name
    sf.write(p, y.T if y.ndim > 1 else y, SR, subtype="PCM_24")
    return p


def knock(src, gaps, name):
    """Три стука из одного и «долгая тишина» после (титр «Стук. Тишина.»)."""
    y, _ = librosa.load(RAW / src, sr=SR)
    on = int(np.argmax(np.abs(y) > np.abs(y).max() * 0.2))
    k = y[max(0, on - 200): on + int(0.35 * SR)]
    k[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    out = np.zeros(int(2.0 * SR))
    pos = 0.02
    for i, g in enumerate([0] + gaps):
        pos += g
        s = int(pos * SR)
        out[s: s + len(k)] += k * (1.0, 0.92, 0.97)[i]
    return tmp(out, name)


def hush():
    """Из принятого amb_lobby: людный гул 1,5 с, затем за 1,2 с обрывается до тишины."""
    y, _ = librosa.load(ROOT / "assets/audio/amb_lobby.ogg", sr=SR, mono=False)
    y = y[:, : int(3.0 * SR)].copy()
    a, b = int(1.5 * SR), int(2.7 * SR)
    y[:, a:b] *= (np.linspace(1, 0, b - a) ** 3)
    y[:, b:] = 0
    return tmp(y, "hush.wav")


def amb(name):
    y, _ = librosa.load(RAW / name, sr=SR, mono=False)
    run(tmp(np.concatenate([y, y], axis=1), name + ".wav"), OUT / name.replace(".mp3", "_x2.mp3"),
        "--loop", "--lufs", "-26")


def main():
    OUT.mkdir(exist_ok=True)
    for name, (mx, fade, vs) in SFX.items():
        for v in vs:
            run(RAW / f"{name}_{v}.mp3", OUT / f"{name}_{v}.mp3", "--mono", "--max", str(mx), "--fade", str(fade), "--lufs", "-16")
    run(knock("knock_one_1.mp3", [0.30, 0.28], "knock_a.wav"), OUT / "sfx_knock_a.mp3", "--mono", "--keep-head", "--lufs", "-16", "--fade", "0")
    run(knock("knock_one_2.mp3", [0.36, 0.34], "knock_b.wav"), OUT / "sfx_knock_b.mp3", "--mono", "--keep-head", "--lufs", "-16", "--fade", "0")
    run(hush(), OUT / "sfx_lobby_hush_a.mp3", "--keep-head", "--lufs", "-20", "--fade", "0")
    for v in "abc":
        run(RAW / f"sfx_drum_beep_synth_{v}.wav", OUT / f"sfx_drum_beep_synth_{v}.mp3", "--mono", "--keep-head", "--lufs", "-16", "--fade", "0.05")
    for n in ("amb_laundry", "amb_hall"):
        for v in (1, 2, 3):
            amb(f"{n}_{v}.mp3")


# выбор автора 12.10.2026 → final/*.ogg (имена игры)
CHOICE = {"sfx_pump_dry": 1, "sfx_phone_ring": 3, "sfx_latch_click": 1, "sfx_tag_fold": 1, "sfx_plunger_press": 1,
          "sfx_paint_scrape": 2, "sfx_token_drop": 2, "sfx_drawer_click": 2, "sfx_key_door": 1, "sfx_trolley_jam": 2,
          "sfx_wheel_bump": 3, "sfx_board_lay": 1, "sfx_suction_glass": 3, "sfx_switch": 1, "sfx_grille_shut": 2,
          "sfx_lift_down": 3, "sfx_lift_up": 1, "sfx_stamp": 2, "sfx_bottle_catch": 1, "sfx_descent": 3}


def final():
    fin = HERE / "final"
    fin.mkdir(exist_ok=True)
    for name, v in CHOICE.items():
        mx, fade, _ = SFX[name]
        run(RAW / f"{name}_{v}.mp3", fin / f"{name}.ogg", "--mono", "--max", str(mx), "--fade", str(fade), "--lufs", "-16")
    run(knock("knock_one_2.mp3", [0.36, 0.34], "knock_b.wav"), fin / "sfx_knock.ogg", "--mono", "--keep-head", "--lufs", "-16", "--fade", "0")
    run(hush(), fin / "sfx_lobby_hush.ogg", "--keep-head", "--lufs", "-20", "--fade", "0")
    run(RAW / "sfx_drum_beep_synth_a.wav", fin / "sfx_drum_beep.ogg", "--mono", "--keep-head", "--lufs", "-16", "--fade", "0.05")
    run(RAW / "amb_laundry_2.mp3", fin / "amb_laundry.ogg", "--loop", "--lufs", "-26")
    run(RAW / "amb_hall_1.mp3", fin / "amb_hall.ogg", "--loop", "--lufs", "-26")


if __name__ == "__main__":
    final() if sys.argv[1:] == ["--final"] else main()
