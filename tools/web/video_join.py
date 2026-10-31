#!/usr/bin/env python3
"""Сборка видеопрохождения из записей актов (tools/web/record_full.js → ПАПКА/actN.webm).

  python tools/web/video_join.py ПАПКА [--crf 24]

Каждый акт — в MP4 (H.264 30 к/с, AAC 160 кбит/с; WebM из браузера идёт с переменной частотой
кадров — приводится к 30), затем один файл ПАПКА/hydroshock_full.mp4 с главами «Акт I…IV»
(главы видны в плеерах VLC, mpv, QuickTime, на YouTube — по таймкодам из ПАПКА/chapters.txt).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}


def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--crf", default="24")
    a = ap.parse_args(argv)
    d = Path(a.dir)
    acts = sorted(int(p.stem[3:]) for p in d.glob("act*.webm"))
    if not acts:
        sys.exit("нет записей actN.webm")
    parts = []
    for n in acts:
        src, dst = d / f"act{n}.webm", d / f"act{n}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", "fps=30", "-c:v", "libx264",
                        "-preset", "medium", "-crf", a.crf, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                        "-ar", "48000", "-movflags", "+faststart", str(dst)], check=True)
        parts.append((n, dst, dur(dst)))
        print(f"акт {n}: {dst.name}, {parts[-1][2] / 60:.1f} мин, {dst.stat().st_size / 1e6:.0f} МБ", flush=True)
    lst = d / "concat.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for _, p, _ in parts), encoding="utf-8")
    meta = [";FFMETADATA1", "title=Латунный янычар: Гидроудар — полное прохождение"]
    chapters = []
    t = 0.0
    for n, _, du in parts:
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(t * 1000)}", f"END={int((t + du) * 1000)}",
                 f"title=Акт {ROMAN[n]}"]
        chapters.append(f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{int(t % 60):02d} Акт {ROMAN[n]}")
        t += du
    (d / "meta.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")
    (d / "chapters.txt").write_text("\n".join(chapters) + "\n", encoding="utf-8")
    out = d / "hydroshock_full.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(d / "meta.txt"),
                    "-map_metadata", "1", "-map_chapters", "1", "-c", "copy", "-movflags", "+faststart", str(out)],
                   check=True)
    print(f"готово: {out} — {t / 60:.0f} мин, {out.stat().st_size / 1e6:.0f} МБ")


if __name__ == "__main__":
    main()
