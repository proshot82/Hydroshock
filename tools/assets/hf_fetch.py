#!/usr/bin/env python3
"""Забрать результат генерации Higgsfield и довести до размера спеки.

  python tools/assets/hf_fetch.py ИМЯ.png URL JOB_ID [--size 1920x1080] [--note "..."]

Оригинал → work/higgsfield/raw/<имя>__<job>.png (как пришёл, для повторяемости);
подогнанный → work/higgsfield/staging/<имя>.png: кадрирование по центру до пропорции
размера и Lanczos до точного размера (ASSET_SPEC §14). В assets/ кладёт только
приёмка после утверждения автора. Каждая запись — строка в work/higgsfield/log.jsonl.
"""
import argparse
import datetime
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work" / "higgsfield"


def fit(im, w, h):
    sw, sh = im.size
    target = w / h
    if sw / sh > target:                      # шире — режем бока
        nw = round(sh * target)
        im = im.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
    else:                                     # выше — режем верх и низ поровну
        nh = round(sw / target)
        im = im.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))
    return im.resize((w, h), Image.LANCZOS)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("url")
    ap.add_argument("job")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    w, h = (int(x) for x in a.size.split("x"))
    raw = WORK / "raw" / f"{Path(a.name).stem}__{a.job}.png"
    raw.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(a.url, raw)
    im = Image.open(raw)
    mode = "RGBA" if "A" in im.getbands() or "transparency" in im.info else "RGB"
    out = fit(im.convert(mode), w, h)
    stage = WORK / "staging" / a.name
    stage.parent.mkdir(parents=True, exist_ok=True)
    out.save(stage)
    lum = round(ImageStat.Stat(out.convert("L")).mean[0] / 2.55, 1)
    rec = {"date": datetime.date.today().isoformat(), "kind": "fetch", "target": a.name, "job_id": a.job,
           "raw_size": "%dx%d" % im.size, "size": f"{w}x{h}", "mode": mode, "lum_pct": lum, "note": a.note}
    with open(WORK / "log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
