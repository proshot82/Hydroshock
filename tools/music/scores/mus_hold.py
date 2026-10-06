#!/usr/bin/env python3
"""mus_hold — музыка ожидания автоответчика стойки (Z02.phone.call), петля ~26 с.

Гостиничная «музыка на удержании»: босса-нова в фа мажоре, 108 ударов в минуту,
12 тактов. Кларнет ведёт сладкую мелодию, глокеншпиль подзванивает на сильных
долях, арфа перебирает аккорды, контрабас пиццикато — бас корень-квинта.
Пропущено через «телефонную линию» (300–3400 Гц, моно): звучит из трубки.

  python tools/music/scores/mus_hold.py assets/audio/mus_hold.ogg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sampler import Instrument, Song, chord  # noqa: E402

F2, C3, D3, G2, A2, Bb2 = 41, 48, 50, 43, 45, 46
PROG = [  # (корень баса, корень аккорда, тип) — по такту
    (F2, 53, "maj7"), (D3 - 12, 50, "m7"), (G2, 55, "m7"), (C3 - 12, 48, "7"),
    (F2, 53, "maj7"), (A2, 57, "m7"), (Bb2, 58, "maj7"), (C3 - 12, 48, "7"),
    (D3 - 12, 50, "m7"), (G2, 55, "7"), (G2, 55, "m7"), (C3 - 12, 48, "7"),
]
# мелодия: (доля от начала, длительность в долях, MIDI)
MEL = [
    (0, 1.5, 72), (1.5, 0.5, 74), (2, 2, 76),
    (4, 1, 74), (5, 1, 72), (6, 2, 69),
    (8, 1.5, 70), (9.5, 0.5, 72), (10, 2, 74),
    (12, 1, 72), (13, 1, 70), (14, 2, 67),
    (16, 1.5, 72), (17.5, 0.5, 74), (18, 2, 76),
    (20, 1, 79), (21, 1, 77), (22, 2, 76),
    (24, 1.5, 74), (25.5, 0.5, 72), (26, 2, 70),
    (28, 1, 69), (29, 1, 70), (30, 2, 72),
    (32, 1, 74), (33, 1, 72), (34, 2, 69),
    (36, 1, 71), (37, 1, 74), (38, 2, 77),
    (40, 1.5, 76), (41.5, 0.5, 74), (42, 2, 70),
    (44, 1, 72), (45, 3, 67),
]


def main(out):
    song = Song(bpm=108, beats=48)
    clar = Instrument("Woodwinds/Clarinet/susLong", layer="v2", gain=0.9, release=0.15)
    glock = Instrument("Percussion/Glock", gain=0.25, release=0.3)
    harp = Instrument("Strings/Harp", gain=0.55, release=0.4)
    bass = Instrument("Strings/Solo Contrabass/Pizz", layer="v3", gain=1.0, release=0.1)
    t_mel = song.track(pan=0.1, wet=0.25)
    t_gl = song.track(pan=0.3, wet=0.35)
    t_harp = song.track(pan=-0.3, wet=0.3)
    t_bass = song.track(pan=0.0, wet=0.1)
    for b, d, m in MEL:
        song.play(t_mel, clar, b, d * 0.92, m, 0.8)
        if b % 4 == 0:
            song.play(t_gl, glock, b, 0.5, m + 12, 0.6)
    for bar, (bass_root, root, kind) in enumerate(PROG):
        s = bar * 4
        song.play(t_bass, bass, s, 1.4, bass_root, 0.9)              # босса: 1 и «и» второй
        song.play(t_bass, bass, s + 1.5, 0.5, bass_root + 7, 0.7)
        song.play(t_bass, bass, s + 2, 1.4, bass_root + 7, 0.85)
        song.play(t_bass, bass, s + 3.5, 0.5, bass_root, 0.7)
        notes = chord(root, kind)
        for k, off in enumerate((0, 0.5, 1.5, 2, 2.5, 3.5)):
            song.play(t_harp, harp, s + off, 0.9, notes[k % len(notes)] - 12 + (12 if k >= 4 else 0), 0.55)
    dur = song.render(out, loop=True, reverb_s=1.2, phone=True, master=0.8)
    print(f"{out}: {dur:.1f} с")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mus_hold.ogg")
