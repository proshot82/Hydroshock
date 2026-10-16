#!/usr/bin/env python3
"""Сборка браузерной версии «Гидроудара» (движок Б, решение автора 13.10.2026).

  python tools/web/build_web.py [--out dist/web] [--gfx ПАПКА ...] [--serve ПОРТ]

Что делает:
  * game/ (страница, стили, код) → OUT/ как есть;
  * assets/gfx/**/*.png → OUT/assets/gfx/**/*.webp: без прозрачности — WebP q90,
    с прозрачностью — WebP q90 с альфой без потерь; курсоры остаются PNG (их рисует
    браузер в CSS). --gfx ui rooms … — только эти папки (быстрая сборка превью);
  * assets/audio/*.ogg → OUT/assets/audio/ + копия .mp3 для браузеров без Vorbis (старые Safari);
  * assets/fonts/*.ttf и лицензии → OUT/assets/fonts/;
  * OUT/data/manifest.json — имена ассетов → файлы, номер сборки;
  * OUT/data/ui.json — строки интерфейса из texts/ui/UI_TEXTS.md.

Перекодированное кэшируется в work/web_cache/ (по SHA-256 исходника и настройкам),
повторная сборка берёт готовое. Собранное (dist/) руками не править.
"""
import argparse
import hashlib
import http.server
import json
import re
import functools
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / "game"
ASSETS = ROOT / "assets"
CACHE = ROOT / "work" / "web_cache"
WEBP_Q = 90
MP3_RATE = {"bgm": "160k", "mus": "160k", "amb": "128k", "sting": "160k"}   # остальное — 96k
PNG_AS_IS = {"cursors"}   # папки gfx, которые остаются PNG


def sha(path, extra=""):
    h = hashlib.sha256(extra.encode())
    h.update(path.read_bytes())
    return h.hexdigest()[:20]


def to_webp(src, dst):
    key = sha(src, f"webp{WEBP_Q}")
    cached = CACHE / "gfx" / f"{key}.webp"
    if not cached.exists():
        cached.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(src)
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im = im.convert("RGBA")
            im.save(cached, "WEBP", quality=WEBP_Q, alpha_quality=100, method=6, exact=True)
        else:
            im.convert("RGB").save(cached, "WEBP", quality=WEBP_Q, method=6)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cached, dst)


def to_mp3(src, dst):
    rate = MP3_RATE.get(src.stem.split("_")[0], "96k")
    key = sha(src, f"mp3{rate}")
    cached = CACHE / "audio" / f"{key}.mp3"
    if not cached.exists():
        cached.parent.mkdir(parents=True, exist_ok=True)
        tmp = cached.with_suffix(".tmp.mp3")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                        "-c:a", "libmp3lame", "-b:a", rate, str(tmp)], check=True)
        tmp.replace(cached)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cached, dst)


def ui_texts():
    src = ROOT / "texts" / "ui" / "UI_TEXTS.md"
    out = {}
    for n, line in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
        m = re.match(r"([a-zа-яё0-9_]+)\s*\|\s*(\S.*)$", line.strip())
        if not m:
            continue   # заголовки, пояснения
        k, v = m.group(1), m.group(2).strip()
        if k in out:
            sys.exit(f"{src.name}:{n}: ключ {k} повторяется")
        out[k] = v
    return out


def act_data(acts):
    """Данные движка из файлов логики (tools/data/gen_design.py) и всё, на что они ссылаются."""
    sys.path.insert(0, str(ROOT / "tools" / "data"))
    import gen_design as G
    out, gfx, audio = {}, set(), set()
    for act in acts:
        try:
            d = G.build(act)
        except G.DesignError as e:
            sys.exit(f"Акт {act}: ошибки логики —\n  " + "\n  ".join(e.errors))
        out[act] = d

        def lay(lst):
            if isinstance(lst, dict):          # кадр «вид:Z04+слой» — вид и слои поверх
                lst = lst.get("extra", [])
            for l in lst:
                if "plans" in l:               # плёнки P05: стекло и три плана
                    gfx.update(f["img"] for f in l["plans"])
                    if l.get("box"):
                        gfx.add(l["box"])
                else:
                    gfx.add(l["img"])

        for v in d["views"].values():
            gfx.add(v["bg"])
            lay(v["layers"])
            for z in v["zones"]:
                if "layer" in z:
                    gfx.add(z["layer"]["img"])
            for k in ("music", "amb"):
                if v[k]:
                    audio.add(v[k])

        def effs(es):
            for e in es:
                for k in ("sfx", "loop", "stop", "music", "amb"):
                    if k in e and not (k == "music" and e[k] == "стоп"):   # «музыка:стоп» — обрыв, не файл
                        audio.add(e[k])
                if "frame" in e:
                    for f in e["frame"]:
                        lay(f)

        for z in d["rules"].values():
            for rs in z.values():
                for r in rs:
                    effs(r["effects"])
        for g in d["chains"].values():
            for r in g:
                effs(r["effects"])
        for m in d["menus"].values():
            for it in m:
                for r in it["rules"]:
                    effs(r["effects"])
        for steps in d["scenes"].values():
            for stp in steps:
                effs(stp["sound"])
                effs(stp["effects"])
                for f in stp["frames"]:
                    lay(f)
        for it in d["items"].values():
            gfx.add(it["icon"])
        for doc in d["docs"].values():
            gfx.add(doc["carrier"])
            if doc.get("plan"):
                gfx.add(doc["plan"]["img"])
        gfx.update({"docs/stamp_kuh", "docs/stamp_hotel", "docs/mark_thumb"})
        for t in d["texts"].values():
            for l in t["lines"]:
                e = l["e"]
                if l["s"] in ("lap", "iz", "kuh", "anc") and e and e != "none":
                    gfx.add(f"portraits/port_{e}")
                    if e.startswith("lap_soap_"):
                        gfx.update({f"portraits/port_{e}_foam", f"portraits/port_{e}_cap"})
    audio.update({"bgm_title", "ui_click", "ui_error", "ui_paper", "ui_pickup", "ui_transition", "ui_zoom_in",
                  "ui_zoom_out", "blip_lap", "blip_anc", "blip_iz", "blip_kuh", "blip_pa", "blip_guest"})
    return out, gfx, audio


def build_id():
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        rev = "без git"
    return f"{datetime.now(timezone.utc):%d.%m.%Y %H:%M} UTC · {rev}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist" / "web"))
    ap.add_argument("--gfx", nargs="*", help="только эти папки assets/gfx (по умолчанию все)")
    ap.add_argument("--acts", type=int, nargs="*",
                    help="только эти акты: данные и их ассеты (лёгкая сборка превью); по умолчанию — все акты с логикой")
    ap.add_argument("--serve", type=int, help="после сборки поднять локальный сервер на порту")
    ap.add_argument("--try", dest="try_", nargs="*", default=[], metavar="ПАПКА/ИМЯ=ФАЙЛ",
                    help="превью с кандидатом вместо картинки assets/gfx (до «да» автора; assets/ не трогается), "
                         "например zooms/zoom_z03=work/higgsfield/candidates/act1_fix_1013/zoom_z03__a.png")
    a = ap.parse_args(argv)
    tries = {}
    for t in a.try_:
        k, v = t.split("=", 1)
        if not Path(v).is_file():
            sys.exit(f"кандидата {v} нет")
        tries[k] = Path(v)
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(GAME, out)
    acts = a.acts or sorted(int(p.name[3]) for p in (ROOT / "design" / "logic").glob("ACT*_LOGIC.md"))
    acts_data, need_gfx, need_audio = act_data(acts)
    only = bool(a.acts)

    manifest = {"build": build_id(), "gfx": {}, "audio": {}, "candidates": sorted(tries)}
    gfx_root = ASSETS / "gfx"
    folders = sorted(p.name for p in gfx_root.iterdir() if p.is_dir())
    if a.gfx:
        unknown = set(a.gfx) - set(folders)
        if unknown:
            sys.exit(f"нет таких папок в assets/gfx: {', '.join(sorted(unknown))}")
        folders = [f for f in folders if f in a.gfx or f in PNG_AS_IS]
    n_img = 0
    b_png = b_web = 0
    for folder in folders:
        for src in sorted((gfx_root / folder).glob("*.png")):
            name = f"{folder}/{src.stem}"
            if name in tries:
                print(f"[web] кандидат вместо {name}: {tries[name]}")
                src = tries[name]
            if only and folder not in ("ui", "cursors") and name not in need_gfx:
                continue
            if folder in PNG_AS_IS:
                rel = f"{folder}/{src.name}"
                dst = out / "assets" / "gfx" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
            else:
                rel = f"{folder}/{src.stem}.webp"
                dst = out / "assets" / "gfx" / rel
                to_webp(src, dst)
            manifest["gfx"][name] = rel
            n_img += 1
            b_png += src.stat().st_size
            b_web += dst.stat().st_size

    n_snd = 0
    for src in sorted((ASSETS / "audio").glob("*.ogg")):
        if only and src.stem not in need_audio:
            continue
        dst = out / "assets" / "audio" / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        to_mp3(src, dst.with_suffix(".mp3"))
        manifest["audio"][src.stem] = {"ogg": src.name, "mp3": src.stem + ".mp3"}
        n_snd += 1

    fonts = out / "assets" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    for f in sorted((ASSETS / "fonts").iterdir()):
        if f.suffix in (".ttf", ".txt"):
            shutil.copyfile(f, fonts / f.name)

    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    (data / "ui.json").write_text(json.dumps(ui_texts(), ensure_ascii=False, indent=1), encoding="utf-8")
    for act, d in acts_data.items():
        (data / f"act{act}.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    manifest["acts"] = sorted(acts_data)
    (data / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    missing = sorted(n for n in need_gfx if n not in manifest["gfx"]) + sorted(n for n in need_audio if n not in manifest["audio"])
    if missing:
        sys.exit("нет ассетов, на которые ссылаются данные: " + ", ".join(missing))

    # Страница для приватного превью на claude.ai: там документ оборачивается в свой
    # каркас (doctype/head/body), поэтому кладём содержимое head и body без обёртки.
    html = (GAME / "index.html").read_text(encoding="utf-8")
    head = re.search(r"<head>(.*?)</head>", html, re.S).group(1)
    body = re.search(r"<body>(.*?)</body>", html, re.S).group(1)
    head = "\n".join(l for l in head.splitlines() if l.strip().startswith(("<title", "<link")))
    (out / "artifact.html").write_text(head + "\n" + body.strip() + "\n", encoding="utf-8")

    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    mb = 1024 * 1024
    print(f"[web] картинок {n_img}: {b_png / mb:.1f} МБ PNG → {b_web / mb:.1f} МБ; звуков {n_snd}")
    print(f"[web] {out}: {sum(1 for p in out.rglob('*') if p.is_file())} файлов, {total / mb:.1f} МБ; сборка {manifest['build']}")

    if a.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
        http.server.ThreadingHTTPServer.allow_reuse_address = True
        with http.server.ThreadingHTTPServer(("127.0.0.1", a.serve), handler) as srv:
            print(f"[web] http://127.0.0.1:{a.serve}/")
            srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
