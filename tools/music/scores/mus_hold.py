#!/usr/bin/env python3
"""mus_hold — музыка ожидания автоответчика стойки (Z02.phone.call), петля ~29 с.

Гостиничная «музыка на удержании» — бодрая босса-нова в фа мажоре, 132 удара в минуту,
16 тактов. Флейта ведёт синкопированную мелодию, фортепиано кладёт аккорды босса-ритмом,
контрабас пиццикато — бас корень-квинта, клавесы стучат босса-клаву, шейкер — шестнадцатые,
низкая тумба — «сурдо» на 1 и 3, глокеншпиль подзванивает на вершинах фраз.
Две версии: «из трубки» (основная, мягкая полоса 220–5500 Гц, моно) и чистая (--clean).

  python tools/music/scores/mus_hold.py assets/audio/mus_hold.ogg [--clean]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sampler import Instrument, Perc, Piano, Song, chord  # noqa: E402

P = "VSCO 1 Percussion/varWood/"
# по такту: список (доля в такте, корень баса, корень аккорда, тип)
PROG = [
    [(0, 41, 65, "maj7")], [(0, 41, 65, "6")], [(0, 43, 67, "m7")], [(0, 36, 60, "7")],
    [(0, 45, 69, "m7")], [(0, 38, 62, "7")], [(0, 43, 67, "m7")], [(0, 36, 60, "7")],
    [(0, 41, 65, "maj7")], [(0, 41, 63, "7")], [(0, 46, 70, "maj7")], [(0, 46, 70, "m6")],
    [(0, 45, 69, "m7")], [(0, 38, 62, "7")], [(0, 43, 67, "m7"), (2, 36, 60, "7")],
    [(0, 41, 65, "maj7"), (2, 36, 60, "7")],
]
# мелодия флейты: (доля от начала, длительность в долях, MIDI)
MEL = [
    (0, .5, 81), (.5, .5, 84), (1.5, 1, 88), (2.5, .5, 86), (3, .5, 84), (3.5, 1.5, 81),
    (5.5, .5, 79), (6, .5, 81), (6.5, 1.5, 77),
    (8, .5, 79), (8.5, .5, 82), (9.5, 1, 86), (10.5, .5, 84), (11, .5, 82), (11.5, 1.5, 79),
    (13.5, .5, 76), (14, .5, 77), (14.5, 1.5, 79),
    (16, .5, 81), (16.5, .5, 84), (17.5, 1, 88), (18.5, .5, 86), (19, .5, 84), (19.5, 1.5, 84),
    (21.5, .5, 86), (22, .5, 84), (22.5, 1.5, 78),
    (24, .5, 79), (24.5, .5, 82), (25, .5, 86), (25.5, 1, 84), (27, .5, 82), (27.5, .5, 79),
    (28, 1, 79), (29.5, .5, 76), (30, 1.5, 72), (31.5, .5, 79),
    (32, .5, 81), (32.5, .5, 84), (33.5, 1, 89), (34.5, .5, 88), (35, .5, 86), (35.5, 1.5, 84),
    (37.5, .5, 87), (38, .5, 86), (38.5, 1.5, 84),
    (40, .5, 86), (40.5, .5, 84), (41, .5, 81), (41.5, 1, 86), (43, 1, 89),
    (44, .5, 85), (44.5, .5, 82), (45, 1, 79), (46.5, 1.5, 77),
    (48, .5, 76), (48.5, .5, 79), (49.5, 1, 84), (50.5, .5, 84), (51, 1, 81),
    (52, .5, 78), (52.5, .5, 81), (53.5, 1, 84), (54.5, .5, 86), (55, 1, 84),
    (56, .5, 82), (56.5, .5, 79), (57, .5, 82), (57.5, 1, 86), (58.5, .5, 84), (59, 1, 79),
    (60, .5, 81), (60.5, .5, 77), (61.5, 2, 77),
]
PIANO_HITS = ((0, .45), (1.5, .45), (3, .9)), ((.5, .45), (2, .45), (3.5, .45))  # чёт/нечёт такт
CLAVE = (0, 1.5, 3, 5, 6.5)                                                   # босса-клава на 2 такта


def main(out, clean=False):
    song = Song(bpm=132, beats=64)
    flute = Instrument("Woodwinds/Flute/susvib", gain=0.95, release=0.08)
    glock = Instrument("Percussion/Glock", gain=0.9, release=0.4)
    piano = Piano(layer="dyn2", gain=1.1, release=0.18)
    bass = Instrument("Strings/Solo Contrabass/Pizz", layer="v3", gain=2.2, release=0.08)
    claves = Perc([P + f"claves_{v}.wav" for v in ("mf", "mf_2", "mf_3", "mp")], gain=1.5, length=0.25)
    shaker = Perc([P + f"Camo's Shaker/shake{i}.wav" for i in range(1, 9)], gain=1.7, length=0.18)
    surdo = Perc([f"Percussion/Tumba-HitN_v{v}_rr{r}_Sum.wav" for v in (1, 2) for r in (1, 2)],
                 gain=4.5, length=0.5)
    t_fl = song.track(pan=0.05, wet=0.22)
    t_gl = song.track(pan=0.35, wet=0.3)
    t_pn = song.track(pan=-0.25, wet=0.18)
    t_bs = song.track(pan=0.0, wet=0.06)
    t_cl = song.track(pan=0.4, wet=0.12)
    t_sh = song.track(pan=-0.45, wet=0.08)
    t_su = song.track(pan=0.0, wet=0.08)
    for b, d, m in MEL:
        song.play(t_fl, flute, b, d * 0.9, m, 0.85 if d <= .5 else 0.75)
        if m >= 88:
            song.play(t_gl, glock, b, 0.5, m, 0.7)
    for bar, chords in enumerate(PROG):
        s = bar * 4
        for k, (at, broot, root, kind) in enumerate(chords):
            span = (chords[k + 1][0] if k + 1 < len(chords) else 4) - at
            # бас: корень (пунктирная четверть) — квинта на «и» — квинта — подхват корня
            for off, dur, iv, v in ((0, 1.4, 0, .95), (1.5, .45, 7, .7), (2, 1.4, 7, .85), (3.5, .45, 0, .7)):
                if off < span:
                    song.play(t_bs, bass, s + at + off, dur, broot + iv, v)
            notes = chord(root, kind)
            voicing = [n if n < 72 else n - 12 for n in notes[1:]] + [notes[0]]   # без баса, в середине
            for off, dur in PIANO_HITS[bar % 2]:
                if at <= off < at + span:
                    for n in voicing:
                        song.play(t_pn, piano, s + off, dur, n, 0.7 if off == int(off) else 0.6)
        for i in range(16):                                   # шейкер: шестнадцатые, акцент на «и»
            song.play(t_sh, shaker, s + i / 4, .2, 0, (0.9 if i % 4 == 2 else 0.45 if i % 2 == 0 else 0.3))
        song.play(t_su, surdo, s, .5, 0, 0.55)
        song.play(t_su, surdo, s + 2, .5, 0, 0.85)
    for two in range(0, 64, 8):
        for c in CLAVE:
            song.play(t_cl, claves, two + c, .2, 0, 0.8)
    dur = song.render(out, loop=True, reverb_s=1.0, phone=not clean, master=0.85)
    print(f"{out}: {dur:.1f} с")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "mus_hold.ogg", clean="--clean" in sys.argv)
