#!/usr/bin/env python3
"""Генерация через Suno (AceDataCloud API), только флагманская модель chirp-v6.

Ключ — переменная окружения ACEDATACLOUD_API_TOKEN. Каждый запрос пишется в журнал
work/suno/log.jsonl (имя, стиль, исключения, длина, task_id, id треков, стоимость, дата).
На один запрос Suno отдаёт две версии — они сохраняются как <имя>_a.mp3 и <имя>_b.mp3.

  python tools/audio/suno.py one ПАПКА ИМЯ --sec 90 "стиль" [--neg "vocals, choir"]
  python tools/audio/suno.py batch МАНИФЕСТ.json ПАПКА [--jobs 6] [--only имя,имя]
      — манифест: список {"name", "style", "neg", "sec"}; уже скачанные пропускаются
"""
import argparse
import concurrent.futures as cf
import datetime
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "work" / "suno" / "log.jsonl"
API = "https://api.acedata.cloud/suno"
MODEL = "chirp-v6"          # решение автора 23.10.2026: только флагманская v6
_log_lock = threading.Lock()


def call(path, body, tries=6):
    key = os.environ.get("ACEDATACLOUD_API_TOKEN")
    if not key:
        sys.exit("нет ACEDATACLOUD_API_TOKEN")
    for i in range(tries):
        req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode(), method="POST",
                                     headers={"authorization": f"Bearer {key}", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            if e.code in (429, 500, 502, 503, 504) and i + 1 < tries:
                time.sleep(10 * (i + 1))
                continue
            raise RuntimeError(f"Suno {e.code}: {msg}")
        except (urllib.error.URLError, TimeoutError) as e:
            if i + 1 < tries:
                time.sleep(10 * (i + 1))
                continue
            raise RuntimeError(f"Suno: нет связи ({e})")


def generate(name, style, sec, neg=""):
    """Отправить запрос и дождаться обеих версий; вернуть (task, [трек, трек])."""
    body = {"action": "generate", "model": MODEL, "custom": True, "instrumental": True,
            "title": name, "style": style, "duration": int(min(360, max(10, round(sec)))), "async": True}
    if neg:
        body["negative_tags"] = neg
    sub = call("audios", body)
    tid = sub.get("task_id")
    if not tid:
        raise RuntimeError(f"Suno не принял запрос {name}: {json.dumps(sub, ensure_ascii=False)[:300]}")
    t0 = time.time()
    while time.time() - t0 < 900:
        time.sleep(15)
        task = call("tasks", {"action": "retrieve", "id": tid})
        resp = task.get("response") or {}
        data = resp.get("data") or []
        states = [d.get("state") for d in data]
        if resp.get("success") is False or "error" in states:
            raise RuntimeError(f"Suno ошибка {name}: {json.dumps(resp, ensure_ascii=False)[:400]}")
        if data and all(s == "succeeded" for s in states):
            bad = [d.get("model") for d in data if d.get("model") != MODEL]
            if bad:
                raise RuntimeError(f"{name}: ответила модель {bad}, а не {MODEL}")
            return task, data
    raise RuntimeError(f"{name}: нет ответа за 15 минут (task {tid})")


def download(url, dst):
    for i in range(5):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                dst.write_bytes(r.read())
            return
        except Exception:
            if i == 4:
                raise
            time.sleep(5 * (i + 1))


def one(out, name, style, sec, neg=""):
    out.mkdir(parents=True, exist_ok=True)
    task, data = generate(name, style, sec, neg)
    files = []
    for tag, d in zip("ab", data):
        dst = out / f"{name}_{tag}.mp3"
        download(d["audio_url"], dst)
        files.append({"file": dst.name, "id": d["id"], "duration": d.get("duration")})
    rec = {"name": name, "model": MODEL, "style": style, "neg": neg, "sec": sec,
           "task_id": task.get("id"), "cost": (task.get("response") or {}).get("cost"),
           "files": files, "dir": str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out),
           "date": datetime.date.today().isoformat()}
    with _log_lock:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("one")
    p1.add_argument("out"); p1.add_argument("name"); p1.add_argument("style")
    p1.add_argument("--sec", type=float, default=30); p1.add_argument("--neg", default="")
    p2 = sub.add_parser("batch")
    p2.add_argument("manifest"); p2.add_argument("out")
    p2.add_argument("--jobs", type=int, default=6); p2.add_argument("--only", default="")
    a = ap.parse_args()

    if a.cmd == "one":
        print(json.dumps(one(Path(a.out).resolve(), a.name, a.style, a.sec, a.neg), ensure_ascii=False))
        return
    out = Path(a.out).resolve()
    items = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    only = set(filter(None, a.only.split(",")))
    todo = [it for it in items if (not only or it["name"] in only)
            and not ((out / f"{it['name']}_a.mp3").exists() and (out / f"{it['name']}_b.mp3").exists())]
    print(f"к генерации: {len(todo)} из {len(items)}", flush=True)
    fails = []
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = {ex.submit(one, out, it["name"], it["style"], it["sec"], it.get("neg", "")): it["name"] for it in todo}
        for f in cf.as_completed(futs):
            n = futs[f]
            try:
                r = f.result()
                print(f"готово {n}: {[x['duration'] for x in r['files']]} с, {r['cost']}", flush=True)
            except Exception as e:
                fails.append(n)
                print(f"СБОЙ {n}: {e}", flush=True)
    if fails:
        sys.exit(f"не получилось: {', '.join(fails)}")


if __name__ == "__main__":
    main()
