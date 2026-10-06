#!/usr/bin/env python3
"""bgm_hotel — главная тема отеля (W1–W2), петля ~80 с.

Ориентир автора — музыка классических юмористических квестов (The Neverhood): живой
небольшой состав, чуть расстроенное пианино, свинг, медь с «кулисой», смешные сбросы нот.
Си-бемоль мажор, 120 ударов в минуту, шаффл. Форма: вступление 4 — A 8 — A 8 — B 8 — A 8 — кода 4.
  A1: кларнет ведёт тему, туба «умпа», пианино страйдом, щётки и стиральная доска (гуиро).
  A2: тему берёт труба с сурдиной, кларнет подпевает длинными нотами.
  B:  тромбон поёт мост с подъездами кулисой, фагот и контрабас идут шагом.
  A3: труба и кларнет в терцию, в конце — тромбонный «сброс» и возврат к вступлению.

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
     [(0, 46, "6")], [(0, 46, "7")], [(0, 51, "6"), (2, 52, "dim")], [(0, 41, "maj"), (2, 41, "7")]]
A_END = A[:7] + [[(0, 46, "6")]]
B = [[(0, 51, "6")], [(0, 52, "dim")], [(0, 46, "6")], [(0, 43, "7")],
     [(0, 48, "m7")], [(0, 41, "7")], [(0, 46, "6"), (2, 43, "7")], [(0, 48, "m7"), (2, 41, "7")]]
CODA = [[(0, 46, "6")], [(0, 43, "7")], [(0, 48, "m7")], [(0, 41, "7")]]
FORM = [("intro", INTRO), ("A1", A), ("A2", A), ("B", B), ("A3", A_END), ("coda", CODA)]

# тема A: (доля от начала части, длительность, MIDI) — игриво, с хроматическими подходами
MEL_A = [
    (0, .5, 74), (.5, .5, 73), (1, 1, 74), (2, .5, 77), (2.5, .5, 79), (3, 1, 77),
    (4, .5, 71), (4.5, .5, 74), (5, .5, 77), (5.5, 1, 74), (7, .5, 71), (7.5, .5, 72),
    (8, 1.5, 75), (9.5, .5, 74), (10, .5, 72), (10.5, .5, 70), (11, 1, 67),
    (12, .5, 69), (12.5, .5, 72), (13, .5, 75), (13.5, .5, 74), (14, 1.5, 72), (15.5, .5, 73),
    (16, 1, 74), (17, .5, 77), (17.5, .5, 79), (18, 1, 82), (19, .5, 79), (19.5, .5, 77),
    (20, 1.5, 80), (21.5, .5, 79), (22, .5, 77), (22.5, .5, 74), (23, 1, 77),
    (24, .5, 79), (24.5, .5, 82), (25, 1, 84), (26, .5, 85), (26.5, .5, 82), (27, 1, 79),
    (28, 1, 77), (29, .5, 74), (29.5, .5, 72), (30, 1.5, 70),
]
# мост: тромбон, (доля, длит., MIDI, подъезд кулисой в полутонах, сброс в конце)
MEL_B = [
    (0, 2, 58, -3, 0), (2, 1, 60, 0, 0), (3, 1, 63, 0, 0), (4, 3, 61, -2, 0),
    (8, 1, 62, 0, 0), (9, 1, 60, 0, 0), (10, 2, 58, 0, 0), (12, 3, 59, -3, 0),
    (16, 1.5, 63, 0, 0), (17.5, .5, 62, 0, 0), (18, 2, 60, 0, 0), (20, 3, 57, -2, 0),
    (24, 1, 58, 0, 0), (25, 1, 62, 0, 0), (26, 1.5, 65, -2, -6), (28, 2, 63, 0, 0), (30, 2, 60, 0, 0),
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
    pno = Piano(layer="dyn2", gain=0.75, release=0.15)
    pno2 = Instrument("Keys/Upright Nr1", layer="_mf_", gain=0.45, release=0.15)   # второе пианино чуть выше — «хонки-тонк»
    tuba = Instrument("Brass/Tuba/stac", layer="v2", gain=1.9, release=0.12)
    clar = Instrument("Woodwinds/Clarinet/susLong", layer="v2", gain=0.9, release=0.1)
    clar_st = Instrument("Woodwinds/Clarinet/stac", gain=0.9, release=0.06)
    tpt = Instrument("Brass/Trumpet/straightM-sus", gain=0.9, release=0.1)
    tbn = Instrument("Brass/OldTrombone/Sustain", gain=0.9, release=0.15)
    tbn_fall = Instrument("Brass/OldTrombone/Fall", gain=0.9, release=0.2, octave=12)
    bsn = Instrument("Woodwinds/Bassoon/stac", gain=0.55, release=0.06)
    bass = Instrument("Strings/Solo Contrabass/Pizz", layer="v3", gain=1.6, release=0.08)
    ride = Perc([P1 + "varMetal/Cymbals/susp/susp_hit_woodmall_p.wav",
                 P1 + "varMetal/Cymbals/susp/susp_hit_woodmall_mp.wav"], gain=10, length=0.9)
    snare = Perc([P1 + f"drums/snare/OldSnare/snare_{v}.wav" for v in ("pp", "pp2", "pp3", "p", "p2")],
                 gain=3.5, length=0.35)
    kick = Perc([P1 + f"drums/bass/bdrum_muted_pp_{i}.wav" for i in (1, 2, 3)], gain=0.9, length=0.4)
    board = Perc([f"Percussion/Guiro-Hit_v1_rr{i}_Sum.wav" for i in (1, 2)], gain=10, length=0.25)
    blk = Perc([P1 + "varWood/claves_mf.wav", P1 + "varWood/claves_mf_2.wav"], gain=0.6, length=0.3)

    T = {k: song.track(pan=p, wet=w) for k, p, w in (
        ("pno", -0.2, 0.18), ("tuba", 0.0, 0.08), ("clar", 0.3, 0.2), ("tpt", -0.3, 0.2),
        ("tbn", 0.15, 0.22), ("bsn", 0.35, 0.12), ("bass", 0.05, 0.06), ("ride", 0.4, 0.15),
        ("sn", -0.1, 0.1), ("kick", 0.0, 0.05), ("board", -0.45, 0.1), ("blk", 0.5, 0.15))}

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
                # пианино: страйд — бас на 1 и 3, аккорд на 2 и 4; второе пианино дублирует аккорд
                for off in range(0, int(span)):
                    b = s + at + off
                    if off % 2 == 0:
                        pl("pno", pno, b, .9, low + (7 if (off == 2 and span == 4) else 0) - 12, .75)
                    else:
                        for n in mid:
                            pl("pno", pno, b, .45, n, .55)
                            pl("pno", pno2, b, .45, n + 0.18, .5)
                # бас: туба «умпа» в A, контрабас и фагот шагают в мосте
                if name == "B":
                    walk = [low, low + (4 if "m" not in kind else 3), low + 7, low + 9 if kind != "dim" else low + 6]
                    for off in range(int(span)):
                        pl("bass", bass, s + at + off, .9, walk[off % 4] - 12, .85)
                        pl("bsn", bsn, s + at + off, .4, walk[off % 4], .55)
                elif name != "intro":
                    for off in range(0, int(span), 2):
                        pl("tuba", tuba, s + at + off, .8, low - 12 + (7 if off == 2 and span == 4 else 0), .85)
                if name == "A2":
                    gt = [n for n in notes if (n - root) % 12 in (3, 4, 10, 9)][:1]
                    for n in gt:
                        pl("clar", clar, s + at, span * .95, n + 12 if n < 62 else n, .4)
            # барабаны: райд «дин, дин-да-дин», малый мягко на 2 и 4, бочка-«перо» на каждую, доска на «и» 2 и 4
            if name != "intro":
                for b, v in ((0, .8), (1, .9), (1.5, .55), (2, .8), (3, .9), (3.5, .55)):
                    pl("ride", ride, s + b, .5, 0, v)
                for b in (1, 3):
                    pl("sn", snare, s + b, .3, 0, .8)
                for b in range(4):
                    pl("kick", kick, s + b, .3, 0, .6)
                for b in (1.5, 3.5):
                    pl("board", board, s + b, .2, 0, .7)
        # мелодии частей
        if name in ("A1", "A2", "A3"):
            for b, d, m in MEL_A:
                if name == "A1":
                    pl("clar", clar_st if d <= .5 else clar, s0 + b, d * .9, m, .8)
                elif name == "A2":
                    pl("tpt", tpt, s0 + b, d * .9, m, .8, scoop=-1 if d >= 1 else 0, glide=.06)
                else:
                    pl("tpt", tpt, s0 + b, d * .9, m, .85)
                    c = [ch for ch in FORM[4][1][int(b // 4)]][-1 if b % 4 >= 2 else 0]
                    pl("clar", clar_st if d <= .5 else clar, s0 + b, d * .9, below(m, tones(c[1], c[2])), .6)
            if name == "A2":                       # фагот «хрюкает» в конце фразы
                for b, m in ((30.5, 46), (31, 45), (31.5, 41)):
                    pl("bsn", bsn, s0 + b, .4, m, .9)
            if name == "A1":                       # пианино-ответ в конце фразы
                for b, m in ((14.5, 77), (15, 79), (15.5, 80), (30.5, 82), (31, 81), (31.5, 79)):
                    pl("pno", pno, s0 + b, .4, m, .55)
        if name == "B":
            for b, d, m, sc, fl in MEL_B:
                pl("tbn", tbn, s0 + b, d * .95, m, .85, scoop=sc, fall=fl, glide=.15)
        if name == "intro":
            pl("blk", blk, s0 + 14.5, .2, 0, .8)
            pl("blk", blk, s0 + 15, .2, 0, .9)
        if name == "A3":
            pl("tbn", tbn_fall, s0 + 31, 1.5, 58, .8)
        if name == "coda":                         # кода — вступление пианино плюс тромбонный «зевок» к повтору
            pl("tbn", tbn, s0 + 12, 3.5, 53, .7, scoop=-4, fall=-3, glide=.25)
        bar0 += len(prog)
    dur = song.render(out, loop=True, reverb_s=1.3, master=0.85)
    print(f"{out}: {dur:.1f} с")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bgm_hotel.ogg")
