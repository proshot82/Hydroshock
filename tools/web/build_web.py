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
        m = re.match(r"([a-z0-9_]+)\s*\|\s*(\S.*)$", line.strip())
        if not m:
            continue   # заголовки, пояснения
        k, v = m.group(1), m.group(2).strip()
        if k in out:
            sys.exit(f"{src.name}:{n}: ключ {k} повторяется")
        out[k] = v
    return out


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
    ap.add_argument("--serve", type=int, help="после сборки поднять локальный сервер на порту")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(GAME, out)

    manifest = {"build": build_id(), "gfx": {}, "audio": {}}
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
