#!/usr/bin/env python3
"""Пакет З5а: все мелодии на ElevenLabs Music v2.5 (просьба автора 12.10.2026) — прослушка рядом с принятыми.

  python work/audio/candidates/s5_v25_1012/build.py

listen/<имя>_v25_N.mp3 — новые (−18 LUFS; mus_hold — через «трубку» 220–5500 Гц, как принятая;
стингеры — та же длина и затухание, что у принятых); listen/<имя>_cur.mp3 — принятые из assets/audio.
"""
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAW, OUT, TMP = HERE / "raw", HERE / "listen", HERE / "tmp"
AUD = ROOT / "assets" / "audio"
SR = 44100
FINISH = [sys.executable, str(ROOT / "tools/audio/finish.py")]
ARGS = {
    "bgm_title": ["--keep-head", "--fade", "0.05"], "bgm_hotel": ["--keep-head", "--fade", "0.05"],
    "bgm_service": ["--keep-head", "--fade", "0.05"], "bgm_below": ["--keep-head", "--fade", "0.05"],
    "bgm_deep": ["--keep-head", "--fade", "0.05"], "mus_hold": ["--keep-head", "--fade", "0.05"],
    "sting_solved": ["--max", "3.5", "--fade", "1.0"], "sting_relic": ["--max", "3.5", "--fade", "1.2"],
    "sting_water": ["--max", "7", "--fade", "1.5"],
}


def run(src, dst, *args):
    subprocess.run([*FINISH, str(src), str(dst), *args], check=True, stdout=subprocess.DEVNULL)


def phone(src):
    """Музыка ожидания через «трубку», как принятая mus_hold: полоса 220–5500 Гц."""
    y, _ = librosa.load(src, sr=SR, mono=True)
    y = sosfilt(butter(4, [220, 5500], btype="band", fs=SR, output="sos"), y)
    TMP.mkdir(exist_ok=True)
    p = TMP / (Path(src).stem + "_phone.wav")
    sf.write(p, y, SR, subtype="PCM_24")
    return p


def main():
    OUT.mkdir(exist_ok=True)
    for name, args in ARGS.items():
        for v in (1, 2):
            src = RAW / f"{name}_v25_{v}.mp3"
            if name == "mus_hold":
                src = phone(src)
            run(src, OUT / f"{name}_v25_{v}.mp3", "--lufs", "-18", *args)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(AUD / f"{name}.ogg"), "-b:a", "192k",
                        str(OUT / f"{name}_cur.mp3")], check=True)
    # тема глубины, вариант e из З1 — тоже v2.5
    run(HERE.parent / "s1_music_1012/raw/bgm_deep_e.mp3", OUT / "bgm_deep_v25_3.mp3", "--lufs", "-18", "--keep-head", "--fade", "0.05")


if __name__ == "__main__":
    main()
