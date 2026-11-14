#!/usr/bin/env python3
"""Все проверки «Гидроудара» одной командой.

  python tools/check_all.py                  быстрый набор (минут семь): документы, тексты, логика, звук, код
  python tools/check_all.py --full           всё (около часа): ещё тесты, достижимость, сборка, браузер,
                                             полное автопрохождение
  python tools/check_all.py --only browser   одна или несколько групп (через пробел)
  python tools/check_all.py --list           что входит в какую группу

Группы:
  static   документы, спека ассетов, шрифты, тексты и условия слотов, генерируемые документы, звук,
           синтаксис и линтер кода, логика актов, тест-матрица H01–H26 — без браузера;
  tests    тесты самих проверок (pytest tests);
  reach    достижимость советов и реплик, строго (check_reach.py --strict);
  browser  сборка, дымовой тест, автопрохождение мышью на компьютере и пальцем на iPhone;
  touch    автопрохождение пальцем на Android и на телефоне вертикально;
  fullrun  полное автопрохождение: все реплики и бумаги через настоящий интерфейс, сверка с моделью.

Каждая проверка — отдельная строка: OK или FAIL, время. У провала печатается хвост вывода; полный
вывод каждой — в work/verify/check_all/ИМЯ.log. Чего не хватает для запуска (библиотека Python,
Node, Playwright) — сообщается отдельной строкой «НЕТ ЗАВИСИМОСТИ» с командой установки, а не
провалом проверки: урок 10.11.2026 — без pyloudnorm матрица показывала ложный провал H21.

Код выхода: 0 — всё, что запускалось, прошло; 1 — есть провал или не хватило зависимости.
Зависимости: pip install -r requirements-dev.txt, Node 22+ с ESLint (`npm install -g eslint`) и
ffmpeg (проверка звука, матрица, сборка); для групп с браузером — ещё
`npm install -g playwright` (один раз — `npx playwright install chromium`).
"""
import argparse
import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "work" / "verify" / "check_all"     # work/verify/ — в .gitignore
DIST = ROOT / "dist" / "web"                      # dist/ — в .gitignore
PY = sys.executable
GROUPS = ("static", "tests", "reach", "browser", "touch", "fullrun")
DEFAULT = ("static",)
ACTS = (1, 2, 3, 4)
# Звук читают и перекодируют программы ffmpeg и ffprobe (одна установка): проверка звука, матрица
# (пункт H21 зовёт проверку звука) и сборка. Урок 11.11.2026: на GitHub без них проверка звука и
# матрица упали с «No such file or directory: 'ffprobe'» — провалом это не было.
FFMPEG = ("ffmpeg", "ffprobe")
HOW = {"ffmpeg": "поставить ffmpeg (ffprobe идёт с ним) и добавить в PATH",
       "ffprobe": "поставить ffmpeg (ffprobe идёт с ним) и добавить в PATH",
       "node": "поставить Node 22 или новее и добавить в PATH",
       "eslint": "npm install -g eslint"}


class Step:
    def __init__(self, name, group, title, cmd=None, run=None, py=(), node=False, tools=(), web=False,
                 timeout=1800, env=None):
        self.name, self.group, self.title = name, group, title
        self.cmd, self.run = cmd, run            # команда (URL подставляется вместо "{url}") или функция
        self.py, self.node, self.tools = py, node, tools   # что нужно для запуска
        self.web = web                           # нужна собранная игра и сервер
        self.timeout, self.env = timeout, env or {}


def js_files():
    return sorted((ROOT / "game" / "js").glob("*.js")) + sorted((ROOT / "tools" / "web").glob("*.js")) \
        + sorted((ROOT / "tools" / "web").glob("*.mjs"))


def run_js_syntax(log):
    """node --check по каждому файлу движка и тестов: файл с синтаксической ошибкой не загрузится вовсе."""
    bad = 0
    for f in js_files():
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, cwd=ROOT)
        if r.returncode:
            bad += 1
            log.write(f"{f.relative_to(ROOT)}:\n{r.stderr.decode('utf-8', 'replace')}\n")
    log.write(f"файлов {len(js_files())}, с ошибками {bad}\n")
    return 1 if bad else 0


def run_generated(log):
    """Генерируемые документы совпадают с тем, что даёт генератор: их не правили руками и не забыли
    пересобрать после правки текстов или условий слотов."""
    tmp = LOGS / "generated"
    tmp.mkdir(parents=True, exist_ok=True)
    pairs = [x for k in ACTS for x in (f"texts/act{k}/ACT{k}_TEXTS_FINAL.md", f"texts/act{k}/BRIEF_ACT{k}_TEXTS.md")]
    jobs = [
        ("docs/WALKTHROUGH_SPOILERS.md", [PY, "tools/texts/gen_walkthrough.py", str(tmp / "WALKTHROUGH_SPOILERS.md")]),
        ("texts/TEXT_LAYER.md", [PY, "tools/texts/build_layer.py", str(tmp / "TEXT_LAYER.md")] + pairs),
    ]
    bad = 0
    for target, cmd in jobs:
        r = subprocess.run(cmd, capture_output=True, cwd=ROOT, env=child_env())
        out = tmp / Path(target).name
        if r.returncode or not out.is_file():
            bad += 1
            log.write(f"{target}: генератор не отработал\n{r.stdout.decode('utf-8', 'replace')}{r.stderr.decode('utf-8', 'replace')}\n")
        elif out.read_bytes() != (ROOT / target).read_bytes():
            bad += 1
            log.write(f"{target}: в репозитории не то, что даёт генератор, — пересобрать: {' '.join(cmd[1:2])}\n")
        else:
            log.write(f"{target}: совпадает с генератором\n")
    return 1 if bad else 0


def steps():
    s = [
        Step("docs", "static", "Суммы документов (MANIFEST_MD5.txt)", [PY, "tools/check_docs.py"]),
        Step("asset_spec", "static", "Спека ассетов: все файлы на месте", [PY, "tools/check_asset_spec.py"]),
        Step("fonts", "static", "Шрифты: каждый символ текстов есть в каждом шрифте", [PY, "tools/check_fonts.py"], py=("PIL",)),
        Step("slot_flags", "static", "Условия слотов против графов актов", [PY, "tools/texts/check_slot_flags.py"]),
    ]
    for k in ACTS:
        s.append(Step(f"texts{k}", "static", f"Тексты Акта {k} по ТЗ",
                      [PY, "tools/texts/check_texts.py", f"texts/act{k}/ACT{k}_TEXTS_FINAL.md",
                       "--brief", f"texts/act{k}/BRIEF_ACT{k}_TEXTS.md"]))
    s += [
        Step("generated", "static", "Генерируемые документы совпадают с генераторами", run=run_generated, py=("PIL",)),
        Step("audio", "static", "Звук: файлы спеки, громкость, швы", [PY, "tools/audio/check_audio.py"],
             py=("numpy", "soundfile", "pyloudnorm"), tools=FFMPEG),
        Step("js_syntax", "static", "Синтаксис кода движка и тестов", run=run_js_syntax, tools=("node",)),
        Step("lint", "static", "Линтер кода: неизвестные имена, неиспользуемое, недостижимое",
             ["eslint", "game/js", "tools/web", "eslint.config.mjs"], tools=("node", "eslint")),
        Step("touch_unit", "static", "Распознаватель касаний (23 проверки)", ["node", "tools/web/test_touch.mjs"], tools=("node",)),
        Step("logic", "static", "Логика четырёх актов: полный перебор", [PY, "tools/data/check_logic.py", "1", "2", "3", "4"]),
        Step("matrix", "static", "Тест-матрица H01–H26", [PY, "tools/data/check_matrix.py"],
             py=("PIL", "numpy", "soundfile", "pyloudnorm"), tools=FFMPEG),
        Step("pytest", "tests", "Тесты проверок (pytest)", [PY, "-m", "pytest", "-q", "tests"], py=("pytest", "PIL")),
        Step("reach", "reach", "Достижимость советов и реплик, строго", [PY, "tools/data/check_reach.py", "--strict"], timeout=3600),
        Step("smoke", "browser", "Дымовой тест в браузере",
             ["node", "tools/web/web_smoke.js", "{url}", str(LOGS / "shots_smoke")], node=True, web=True),
    ]
    for group, device, title in (("browser", "desktop", "компьютер, мышь"), ("browser", "phone", "iPhone, палец"),
                                 ("touch", "android", "Android, палец"), ("touch", "phone-portrait", "телефон вертикально, палец")):
        s.append(Step(f"autoplay_{device}", group, f"Автопрохождение: {title}",
                      ["node", "tools/web/autoplay.js", "{url}", str(LOGS / f"shots_{device}")],
                      node=True, web=True, env={"DEVICE": device}))
    s += [
        Step("plan_full", "fullrun", "План полного прохождения",
             [PY, "tools/web/plan_full.py", "--out", str(LOGS / "fullrun" / "plan.json")]),
        Step("autoplay_full", "fullrun", "Полное автопрохождение: все реплики и бумаги",
             ["node", "tools/web/autoplay_full.js", "{url}", str(LOGS / "fullrun" / "plan.json"), str(LOGS / "fullrun")],
             node=True, web=True, timeout=5400),
    ]
    return s


# ---------------------------------------------------------------- окружение

def child_env(extra=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    npm = shutil.which("npm")
    if npm and "BJ3_NPM_ROOT" not in env:
        try:
            r = subprocess.run([npm, "root", "-g"], capture_output=True, text=True, timeout=60)
            os.environ["BJ3_NPM_ROOT"] = env["BJ3_NPM_ROOT"] = r.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            os.environ["BJ3_NPM_ROOT"] = env["BJ3_NPM_ROOT"] = ""
    if env.get("BJ3_NPM_ROOT"):
        env["NODE_PATH"] = os.pathsep.join(x for x in (env.get("NODE_PATH"), env["BJ3_NPM_ROOT"]) if x)
    env.update(extra or {})
    return env


def missing(step):
    """Чего не хватает для запуска проверки: [(что, как поставить)]."""
    out = []
    for m in step.py:
        if importlib.util.find_spec(m) is None:
            out.append((f"библиотека Python «{m}»", "pip install -r requirements-dev.txt"))
    need_tools = set(step.tools) | ({"node"} if step.node else set()) | (set(FFMPEG) if step.web else set())
    for t in sorted(need_tools):
        if shutil.which(t) is None:
            out.append((f"программа «{t}»", HOW.get(t, "поставить и добавить в PATH")))
    if step.web and importlib.util.find_spec("PIL") is None:
        out.append(("библиотека Python «PIL»", "pip install -r requirements-dev.txt"))
    if step.node and shutil.which("node"):
        r = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True, cwd=ROOT, env=child_env())
        if r.returncode:
            out.append(("Playwright для Node", "npm install -g playwright && npx playwright install chromium"))
    return out


class Web:
    """Собранная игра и сервер с ней — поднимаются один раз, когда понадобятся."""

    def __init__(self):
        self.proc, self.url, self.failed = None, None, None

    def ensure(self):
        if self.url or self.failed:
            return self.url
        t0 = time.time()
        with open(LOGS / "build.log", "wb") as log:
            r = subprocess.run([PY, "tools/web/build_web.py", "--out", str(DIST)], stdout=log, stderr=subprocess.STDOUT,
                               cwd=ROOT, env=child_env())
        line("OK" if r.returncode == 0 else "FAIL", time.time() - t0, "Сборка игры (tools/web/build_web.py)")
        if r.returncode:
            tail(LOGS / "build.log")
            self.failed = "сборка не прошла"
            return None
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        self.proc = subprocess.Popen([PY, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(DIST)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        else:
            self.failed = "сервер не поднялся"
            return None
        self.url = f"http://127.0.0.1:{port}/"
        return self.url

    def close(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()


# ---------------------------------------------------------------- вывод

def line(status, seconds, title):
    print(f"{status:<5} {seconds:7.1f} с  {title}", flush=True)


def tail(path, n=15):
    try:
        rows = path.read_text(encoding="utf-8", errors="replace").rstrip().splitlines()
    except OSError:
        return
    for row in rows[-n:]:
        print("        " + row[:300])
    print(f"        (полный вывод: {path.relative_to(ROOT)})", flush=True)


def run_step(step, web):
    need = missing(step)
    if need:
        line("НЕТ", 0, f"{step.title} — НЕТ ЗАВИСИМОСТИ")
        for what, how in need:
            print(f"        нет: {what}; поставить: {how}")
        return False
    url = None
    if step.web:
        url = web.ensure()
        if not url:
            line("FAIL", 0, f"{step.title} — не запускалась: {web.failed}")
            return False
    path = LOGS / f"{step.name}.log"
    t0 = time.time()
    try:
        if step.run:
            with open(path, "w", encoding="utf-8") as log:
                rc = step.run(log)
        else:
            cmd = [url if c == "{url}" else c for c in step.cmd]
            # программа по имени — полным путём: в Windows eslint и npm — файлы .cmd, по имени не запускаются
            cmd[0] = shutil.which(cmd[0]) or cmd[0]
            with open(path, "wb") as log:
                rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, env=child_env(step.env),
                                    timeout=step.timeout).returncode
    except subprocess.TimeoutExpired:
        line("FAIL", time.time() - t0, f"{step.title} — не уложилась в {step.timeout // 60} мин")
        tail(path)
        return False
    line("OK" if rc == 0 else "FAIL", time.time() - t0, step.title)
    if rc:
        tail(path)
    return rc == 0


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Все проверки «Гидроудара» одной командой.")
    ap.add_argument("--full", action="store_true", help="все группы (около часа)")
    ap.add_argument("--only", nargs="+", choices=GROUPS, metavar="ГРУППА", help="только эти группы: " + ", ".join(GROUPS))
    ap.add_argument("--list", action="store_true", help="показать проверки по группам и выйти")
    a = ap.parse_args(argv)
    all_steps = steps()
    if a.list:
        for g in GROUPS:
            print(f"{g}{' (входит в быстрый набор)' if g in DEFAULT else ''}:")
            for s in all_steps:
                if s.group == g:
                    print(f"    {s.name:<24} {s.title}")
        return 0
    groups = GROUPS if a.full else tuple(a.only) if a.only else DEFAULT
    todo = [s for s in all_steps if s.group in groups]
    LOGS.mkdir(parents=True, exist_ok=True)
    print(f"Группы: {', '.join(g for g in GROUPS if g in groups)}; проверок {len(todo)}"
          + (" (и сборка игры)" if any(s.web for s in todo) else ""), flush=True)
    web = Web()
    t0 = time.time()
    failed = []
    try:
        for s in todo:
            if not run_step(s, web):
                failed.append(s.title)
    finally:
        web.close()
    mins = (time.time() - t0) / 60
    if failed:
        print(f"\nИТОГ: провалов {len(failed)} из {len(todo)} ({mins:.0f} мин):")
        for t in failed:
            print(f"  — {t}")
        return 1
    print(f"\nИТОГ: все {len(todo)} проверок прошли ({mins:.0f} мин)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
