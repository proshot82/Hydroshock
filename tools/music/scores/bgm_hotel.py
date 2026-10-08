#!/usr/bin/env python3
"""bgm_hotel — главная тема отеля (W1–W2), петля ~80 с.

Ориентир автора — музыка классических юмористических квестов (The Neverhood), но приятно
и уютно, без «смешных» гармоний (решение автора 06.10.2026): живой маленький состав, свинг.
Си-бемоль мажор, 120 ударов в минуту, шаффл. Форма: вступление 4 — A 8 — A 8 — B 8 — A 8 — кода 4.
  A1: кларнет ведёт тему, туба мягко «умпа», пианино страйдом, щётки и стиральная доска (гуиро).
  A2: тему берёт флейта, кларнет подпевает длинными нотами, струнные — тёплая подложка.
  B:  мост поёт кларнет в низком тёплом регистре, контрабас идёт шагом, струнные держат аккорды.
  A3: флейта и кларнет в терцию, струнные, в конце — пианино ведёт обратно к вступлению.

  python tools/music/scores/bgm_hotel.py assets/audio/bgm_hotel.ogg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sampler import Instrument, Perc, Piano, Song, chord  # noqa: E402

P1 = "VSCO 1 Percussion/"
SW = 1 / 6                                    # шаффл: «и» сдвигается на треть доли

# аккорды по тактам: [(доля в такте, корень MIDI в 3-й октаве, тип)]
INTRO = [[(0, 46, "6")], [(0, 43, "7")], [(0, 48, "m7")], [(0, 41, "7")]]
A = [[(0, 46, "6")], [(0, 43, "7")], [(0, 48, "m7")], [(0, 41, "7")],
     [(0, 46, "6")], [(0, 46, "7")], [(0, 51, "maj7"), (2, 48, "m7")], [(0, 46, "6"), (2, 41, "7")]]
A_END = A[:7] + [[(0, 46, "6")]]
B = [[(0, 51, "maj7")], [(0, 48, "m7")], [(0, 46, "6")], [(0, 43, "7")],
     [(0, 48, "m7")], [(0, 41, "7")], [(0, 46, "6"), (2, 43, "7")], [(0, 48, "m7"), (2, 41, "7")]]
CODA = [[(0, 46, "6")], [(0, 43, "7")], [(0, 48, "m7")], [(0, 41, "7")]]
FORM = [("intro", INTRO), ("A1", A), ("A2", A), ("B", B), ("A3", A_END), ("coda", CODA)]

# тема A: (доля от начала части, длительность, MIDI) — игриво, но по звукам аккордов
MEL_A = [
    (0, .5, 74), (.5, .5, 72), (1, 1, 74), (2, .5, 77), (2.5, .5, 79), (3, 1, 77),
    (4, .5, 71), (4.5, .5, 74), (5, .5, 77), (5.5, 1, 74), (7, .5, 71), (7.5, .5, 72),
    (8, 1.5, 75), (9.5, .5, 74), (10, .5, 72), (10.5, .5, 70), (11, 1, 67),
    (12, .5, 69), (12.5, .5, 72), (13, .5, 75), (13.5, .5, 74), (14, 1.5, 72), (15.5, .5, 72),
    (16, 1, 74), (17, .5, 77), (17.5, .5, 79), (18, 1, 82), (19, .5, 79), (19.5, .5, 77),
    (20, 1.5, 80), (21.5, .5, 79), (22, .5, 77), (22.5, .5, 74), (23, 1, 77),
    (24, .5, 79), (24.5, .5, 82), (25, 1, 84), (26, .5, 82), (26.5, .5, 79), (27, 1, 75),
    (28, 1, 77), (29, .5, 74), (29.5, .5, 72), (30, 1.5, 70),
]
# мост: кларнет в низком тёплом регистре, (доля, длит., MIDI)
MEL_B = [
    (0, 2, 70), (2, 1, 72), (3, 1, 75), (4, 3, 75), (7, 1, 74),
    (8, 1, 74), (9, 1, 72), (10, 2, 70), (12, 3, 71),
    (16, 1.5, 75), (17.5, .5, 74), (18, 2, 72), (20, 3, 69),
    (24, 1, 70), (25, 1, 74), (26, 2, 77), (28, 2, 75), (30, 2, 72),
]


def tones(root, kind):
    return {n % 12 for n in chord(root, kind)}


def below(m, pcs):
    """Терция-секста под мелодией: ближайший звук аккорда на 3–9 полутонов ниже."""
    for d in range(3, 10):
        if (m - d) % 12 in pcs:
            return m - d
    return m - 12


def main(out):
    bars = sum(len(c) for _, c in FORM)
    song = Song(bpm=120, beats=bars * 4, humanize=0.008)
    pno = Piano(layer="dyn2", gain=1.05, release=0.2)
    tuba = Instrument("Brass/Tuba/stac", layer="v1", gain=2.8, release=0.15)
    clar = Instrument("Woodwinds/Clarinet/susLong", layer="v2", gain=0.9, release=0.12)
    clar_st = Instrument("Woodwinds/Clarinet/stac", gain=0.9, release=0.08)
    flute = Instrument("Woodwinds/Flute/susvib", gain=1.2, release=0.1)
    bass = Instrument("Strings/Solo Contrabass/Pizz", layer="v3", gain=1.6, release=0.1)
    vla = Instrument("Strings/Viola Section/susvib", layer="_v1", gain=1.0, release=0.5)
    vc = Instrument("Strings/Cello Section/susvib", layer="_v1", gain=1.0, release=0.5)
    ride = Perc([P1 + "varMetal/Cymbals/susp/susp_hit_woodmall_p.wav",
                 P1 + "varMetal/Cymbals/susp/susp_hit_woodmall_mp.wav"], gain=8, length=0.9)
    snare = Perc([P1 + f"drums/snare/OldSnare/snare_{v}.wav" for v in ("pp", "pp2", "pp3", "p", "p2")],
                 gain=3, length=0.35)
    kick = Perc([P1 + f"drums/bass/bdrum_muted_pp_{i}.wav" for i in (1, 2, 3)], gain=0.8, length=0.4)
    board = Perc([f"Percussion/Guiro-Hit_v1_rr{i}_Sum.wav" for i in (1, 2)], gain=8, length=0.25)

    T = {k: song.track(pan=p, wet=w) for k, p, w in (
        ("pno", -0.2, 0.2), ("tuba", 0.0, 0.1), ("clar", 0.25, 0.22), ("fl", -0.25, 0.25),
        ("bass", 0.05, 0.08), ("str", 0.0, 0.35), ("ride", 0.4, 0.15),
        ("sn", -0.1, 0.1), ("kick", 0.0, 0.05), ("board", -0.45, 0.1))}

    def pl(track, inst, b, d, m, v, **kw):
        song.play(T[track], inst, b, d, m, v, swing=SW, **kw)

    bar0 = 0
    for name, prog in FORM:
        s0 = bar0 * 4
        for i, chords in enumerate(prog):
            s = s0 + i * 4
            for k, (at, root, kind) in enumerate(chords):
                span = (chords[k + 1][0] if k + 1 < len(chords) else 4) - at
                notes = chord(root, kind)
                low = root - 12 if root >= 46 else root
                mid = sorted(n if n >= 55 else n + 12 for n in notes)
                # пианино: страйд — бас на 1 и 3, аккорд на 2 и 4
                for off in range(0, int(span)):
                    b = s + at + off
                    if off % 2 == 0:
                        pl("pno", pno, b, .9, low + (7 if (off == 2 and span == 4) else 0) - 12, .65)
                    else:
                        for n in mid:
                            pl("pno", pno, b, .45, n, .5)
                # бас: туба «умпа» в A, контрабас шагает в мосте и в A3
                if name in ("B", "A3"):
                    third = 3 if kind in ("m7", "m") else 4
                    walk = [low, low + third, low + 7, low + (9 if kind == "6" else 10 if kind in ("7", "m7") else 11)]
                    for off in range(int(span)):
                        pl("bass", bass, s + at + off, .9, walk[off % 4] - 12, .85)
                elif name != "intro":
                    for off in range(0, int(span), 2):
                        pl("tuba", tuba, s + at + off, .8, low - 12 + (7 if off == 2 and span == 4 else 0), .8)
                # струнные: тёплая подложка — альты и виолончели держат аккорд
                if name in ("A2", "B", "A3", "coda"):
                    for n in mid[:3]:
                        pl("str", vla if n >= 60 else vc, s + at, span * .98, n, .45)
                    pl("str", vc, s + at, span * .98, low, .4)
            # барабаны: райд «дин, дин-да-дин», малый мягко на 2 и 4, бочка-«перо», доска на «и» 2 и 4
            if name != "intro":
                for b, v in ((0, .8), (1, .9), (1.5, .55), (2, .8), (3, .9), (3.5, .55)):
                    pl("ride", ride, s + b, .5, 0, v)
                for b in (1, 3):
                    pl("sn", snare, s + b, .3, 0, .8)
                for b in range(4):
                    pl("kick", kick, s + b, .3, 0, .55)
                for b in (1.5, 3.5):
                    pl("board", board, s + b, .2, 0, .6)
        if name in ("A1", "A2", "A3"):
            for b, d, m in MEL_A:
                if name == "A1":
                    pl("clar", clar_st if d <= .5 else clar, s0 + b, d * .9, m, .8)
                elif name == "A2":
                    pl("fl", flute, s0 + b, d * .9, m, .8)
                else:
                    pl("fl", flute, s0 + b, d * .9, m, .8)
                    c = FORM[4][1][int(b // 4)]
                    c = c[-1] if (b % 4 >= 2 and len(c) > 1) else c[0]
                    pl("clar", clar, s0 + b, d * .9, below(m, tones(c[1], c[2])), .55)
            if name == "A1":                       # пианино отвечает в конце фраз
                for b, m in ((14.5, 77), (15, 79), (15.5, 81), (30.5, 82), (31, 81), (31.5, 77)):
                    pl("pno", pno, s0 + b, .4, m, .5)
        if name == "B":
            for b, d, m in MEL_B:
                pl("clar", clar, s0 + b, d * .95, m - 12 if m > 72 else m, .8)
        if name == "coda":                         # пианино ведёт обратно к вступлению
            for b, m in ((12, 74), (12.5, 77), (13, 82), (13.5, 81), (14, 79), (14.5, 77), (15, 74), (15.5, 72)):
                pl("pno", pno, s0 + b, .45, m, .5)
        bar0 += len(prog)
    dur = song.render(out, loop=True, reverb_s=1.6, master=0.85)
    print(f"{out}: {dur:.1f} с")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bgm_hotel.ogg")
