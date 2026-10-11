#!/usr/bin/env python3
"""Архив всех картинок игры для просмотра автором — по местам, латинскими именами.

  python tools/assets/pack_art.py ВЫХОД.zip [--candidates ПАПКА ...]

Принятое — assets/gfx (экраны, зумы, слои состояний «в кадре», портреты, курсоры); кандидаты на приёмке —
из папок work/higgsfield/candidates/* (основы зумов zoom_*.png и слои с cutouts.json), с приставкой NEW_.
Состояние показывается целым кадром «база + слой»: принятое — кадр-вариант из work/higgsfield/variants,
если он есть, иначе склейка; кандидат — склейка из work/higgsfield/cutout_preview. Картинки — JPEG 90
в полном размере (портреты — на сером фоне), схемы docs/assets — PNG. Имена в архиве только латиницей
(русские имена Windows показывает «кракозябрами»), README.txt — UTF-8 с BOM.
"""
import argparse
import io
import json
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GFX = ROOT / "assets" / "gfx"
VAR = ROOT / "work" / "higgsfield" / "variants"
PREV = ROOT / "work" / "higgsfield" / "cutout_preview"
TOP = "Hydroudar_art"

PLACE = {"room_w1": "W1_room317", "zoom_z01": "W1_room317", "zoom_z02": "W1_room317", "zoom_z03": "W1_room317",
         "room_w2": "W2_lobby", "zoom_z04": "W2_lobby", "zoom_z05": "W2_lobby",
         "cu_z04_forms": "W2_lobby", "cu_z04_folder": "W2_lobby", "cu_z04_key": "W2_lobby", "cu_z04_kefir_hands": "W2_lobby",
         "room_w2_under": "W2u_lobby_under_trolley",
         "room_w3": "W3_laundry", "zoom_z06": "W3_laundry", "zoom_z07": "W3_laundry", "zoom_z08": "W3_laundry",
         "room_w4": "W4_hall", "zoom_z09": "W4_hall", "zoom_z10": "W4_hall", "zoom_z11": "W4_hall",
         "zoom_z12": "W4_hall_stairs_bottom",
         "room_w5": "W5_reception_cave", "room_w5_under": "W5_reception_cave",
         "room_w6": "W6_office", "zoom_z13": "W6_office"}
SCHEMES = {"hotel_topology.png": "hotel_topology.png", "ground_floor_plan.png": "ground_floor_plan.png",
           "w2_counter_layout.png": "W2_counter_layout.png", "w3_plan.png": "W3_laundry_plan.png",
           "w4_plan.png": "W4_hall_plan.png", "stairs_lift_route.png": "stairs_and_lift_route.png"}

README = """«Латунный янычар: Гидроудар» — все картинки игры (копия для просмотра)

Папки — по местам игры: экран (room_*), его зумы (zoom_*) и все их состояния целым кадром,
как их видит игрок (<экран или зум>__<состояние>).
NEW_ в начале имени — кандидат на приёмке, ещё не в игре; без приставки — принято в игру.
Если у NEW_ и у принятой картинки одно имя — NEW_ её заменит после «да» автора (например, NEW_zoom_z11__st_z11_mirror_aside).

W1_room317 — номер 317 (Z01 душевая, Z02 стол и мини-бар, Z03 тележка)
W2_lobby — вестибюль (Z04 стойка Изольды и её крупные планы cu_z04_*, Z05 витрина из-под тележки)
W2u_lobby_under_trolley — вестибюль из-под юбки тележки
W3_laundry — прачечная (Z06 барабаны, Z07 декоративная стена, Z08 шкаф)
W4_hall — зал прекраснодушия (Z09 доска почёта, Z10 стол и люк, Z11 лифт)
W4_hall_stairs_bottom — Z12, низ служебной лестницы из зала, дверь конторы
W5_reception_cave — приёмный пункт (и вид из-под юбки)
W6_office — контора старшего по воде
portraits — портреты (lap — Лапидус, iz — Изольда, kuh — Кухтулху, anc — Предок), на сером фоне
cursors — курсоры из BJ2
schemes — топология отеля, план первого этажа, схема стойки W2, планы W3 и W4,
  куда ведёт винтовая лестница и куда приходит лифт (stairs_and_lift_route)

Картинки — JPEG высокого качества в полном размере 1920×1080; схемы — PNG.
Оригиналы PNG — в репозитории proshot82/Hydroshock: assets/gfx (принятое) и work/higgsfield/candidates (кандидаты).
"""


def jpg(im):
    if "A" in im.getbands():
        bg = Image.new("RGBA", im.size, (128, 128, 128, 255))
        bg.alpha_composite(im.convert("RGBA"))
        im = bg
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=90)
    return buf.getvalue()


def compose(base_name, layer_png, x, y):
    sub = "rooms" if base_name.startswith("room") else "zooms"
    im = Image.open(GFX / sub / base_name).convert("RGBA")
    im.alpha_composite(Image.open(layer_png).convert("RGBA"), (x, y))
    return im


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--candidates", nargs="*", default=[])
    a = ap.parse_args(argv)
    files = {}
    for p in sorted((GFX / "rooms").glob("*.png")) + sorted((GFX / "zooms").glob("*.png")):
        files[f"{PLACE[p.stem]}/{p.stem}.jpg"] = jpg(Image.open(p))
    cj = json.loads((GFX / "cutouts" / "cutouts.json").read_text(encoding="utf-8"))
    for n, e in sorted(cj.items()):
        stem = e["base"][:-4]
        v = VAR / f"{stem}__{n}.png"
        im = Image.open(v) if v.exists() else compose(e["base"], GFX / "cutouts" / f"{n}.png", e["x"], e["y"])
        files[f"{PLACE[stem]}/{stem}__{n}.jpg"] = jpg(im)
    for c in a.candidates:
        c = Path(c)
        for p in sorted(c.glob("zoom_*.png")):
            files[f"{PLACE[p.stem]}/NEW_{p.stem}.jpg"] = jpg(Image.open(p))
        cjp = c / "cutouts.json"
        if cjp.exists():
            for n, e in sorted(json.loads(cjp.read_text(encoding="utf-8")).items()):
                stem = e["base"][:-4]
                pv = PREV / f"{n}__in_scene.png"
                pv = pv if pv.exists() else PREV / f"{n}.png"
                files[f"{PLACE[stem]}/NEW_{stem}__{n}.jpg"] = jpg(Image.open(pv))
    for p in sorted((GFX / "portraits").glob("*.png")):
        files[f"portraits/{p.stem}.jpg"] = jpg(Image.open(p))
    for p in sorted((GFX / "cursors").glob("*.png")):
        files[f"cursors/{p.name}"] = p.read_bytes()
    for k, v in SCHEMES.items():
        files[f"schemes/{v}"] = (ROOT / "docs" / "assets" / k).read_bytes()
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_STORED) as z:
        z.writestr(f"{TOP}/README.txt", "﻿" + README.replace("\n", "\r\n"))
        for name, data in sorted(files.items()):
            full = f"{TOP}/{name}"
            assert full.isascii(), full
            z.writestr(full, data)
    print(len(files), "файлов,", Path(a.out).stat().st_size // 1048576, "МБ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
