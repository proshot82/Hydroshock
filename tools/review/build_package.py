#!/usr/bin/env python3
"""Пакет материалов для полного ревью игры (review/BRIEF_FULL_REVIEW.md §2).

Собирает в один ZIP все действующие документы в порядке чтения: ТЗ ревью,
библии, канон с поправками, промпт, скелет с поправками, сдачи актов с графами
и отчётами солвера, текстовый слой, стиль автора, ТЗ текстов актов, статус
проекта и handoff. Рядом в ZIP кладёт REVIEW_PACKAGE.md — те же файлы подряд
одним текстом (для нейросетей, которые принимают один файл); JSON графов и
отчётов в общий текст не входят — они есть в ZIP отдельно.

История (acts/*/rev1, acts/*/alt, docs/history) в пакет не входит.

По умолчанию пакет облегчённый: без ТЗ текстов четырёх актов (их требования
к слотам уже стоят в текстовом слое строками «Обязано быть» и «Обязательно»)
и без журнала проекта (решения автора перечислены в §3 ТЗ ревью). Это около
четверти объёма — меньше расход токенов в чате. Флаг --full кладёт всё.

Запуск:
    python tools/review/build_package.py                 # review/REVIEW_PACKAGE.zip, облегчённый
    python tools/review/build_package.py --full          # весь комплект §2
    python tools/review/build_package.py ПУТЬ/К/ФАЙЛУ.zip [--full]

Код выхода: 0 — собрано; 1 — не хватает файлов из списка.
Только стандартная библиотека Python 3.8+.
"""

import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "review" / "REVIEW_PACKAGE.zip"

# (номер по §2 ТЗ, путь в репозитории)
FILES = [
    ("00", "review/BRIEF_FULL_REVIEW.md"),
    ("01", "docs/DESIGN_BIBLE.md"),
    ("02", "docs/02_WRITING_BIBLE.md"),
    ("03a", "docs/BJ3_WORLD_CANON_V2.md"),
    ("03b", "docs/BJ3_CANON_V2_1.md"),
    ("03c", "docs/BJ3_CANON_V2_2.md"),
    ("04", "docs/BJ3_PUZZLE_CHAIN_PROMPT_V2.md"),
    ("05a", "docs/BJ3_SKELETON_S3.md"),
    ("05b", "docs/BJ3_SKELETON_S3_1.md"),
    ("06a", "acts/act1/ACT1_SUBMISSION.md"),
    ("06b", "acts/act2/ACT2_SUBMISSION.md"),
    ("06c", "acts/act3/ACT3_SUBMISSION.md"),
    ("06d", "acts/act4/ACT4_SUBMISSION.md"),
    ("07a", "acts/act1/ACT1_graph.json"),
    ("07b", "acts/act1/ACT1_solver_report.json"),
    ("07c", "acts/act2/ACT2_graph.json"),
    ("07d", "acts/act2/ACT2_solver_report.json"),
    ("07e", "acts/act3/ACT3_graph.json"),
    ("07f", "acts/act3/ACT3_solver_report.json"),
    ("07g", "acts/act4/ACT4_graph.json"),
    ("07h", "acts/act4/ACT4_solver_report.json"),
    ("08", "texts/TEXT_LAYER.md"),
    ("09a", "texts/STYLE_AUTHOR.md"),
    ("09b", "texts/AUTHOR_LINES.json"),
    ("10a", "texts/act1/BRIEF_ACT1_TEXTS.md"),
    ("10b", "texts/act2/BRIEF_ACT2_TEXTS.md"),
    ("10c", "texts/act3/BRIEF_ACT3_TEXTS.md"),
    ("10d", "texts/act4/BRIEF_ACT4_TEXTS.md"),
    ("11", "PROJECT_STATUS_HYDROUDAR.md"),
    ("12", "BJ3_HANDOFF.md"),
]
TEXT_SUFFIXES = {".md"}
# Только в полном пакете (--full): дублируют то, что уже есть в слое и в §3 ТЗ.
FULL_ONLY = {
    "texts/act1/BRIEF_ACT1_TEXTS.md",
    "texts/act2/BRIEF_ACT2_TEXTS.md",
    "texts/act3/BRIEF_ACT3_TEXTS.md",
    "texts/act4/BRIEF_ACT4_TEXTS.md",
    "PROJECT_STATUS_HYDROUDAR.md",
}


def selected(full=False):
    return [(num, rel) for num, rel in FILES if full or rel not in FULL_ONLY]


def arcname(num, rel):
    return "%s_%s" % (num, Path(rel).name)


def combined(present, full=False):
    kind = "полный" if full else "облегчённый (без ТЗ текстов актов и журнала проекта — см. §2 ТЗ)"
    out = ["# «Латунный янычар: Гидроудар» — пакет материалов для полного ревью",
           "",
           "Собрано %s скриптом `tools/review/build_package.py`, пакет %s. Файлы идут в порядке чтения из ТЗ ревью (§2); "
           "перед каждым — строка `===== ФАЙЛ: имя =====`. Графы и отчёты солвера (JSON) — только в ZIP."
           % (date.today().strftime("%d.%m.%Y"), kind),
           ""]
    for num, rel in present:
        if Path(rel).suffix not in TEXT_SUFFIXES:
            continue
        out += ["", "", "===== ФАЙЛ: %s (%s) =====" % (arcname(num, rel), rel), ""]
        out.append((ROOT / rel).read_text(encoding="utf-8").rstrip("\n"))
    return "\n".join(out) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    full = "--full" in argv
    rest = [a for a in argv if a != "--full"]
    out = Path(rest[0]) if rest else DEFAULT_OUT
    missing = [rel for _, rel in FILES if not (ROOT / rel).is_file()]
    if missing:
        print("Не хватает файлов:\n  " + "\n  ".join(missing))
        return 1
    files = selected(full)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = combined(files, full)
    md = out.with_suffix(".md")
    md.write_text(text, encoding="utf-8")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for num, rel in files:
            z.write(ROOT / rel, arcname(num, rel))
        z.writestr("REVIEW_PACKAGE.md", text)
    print("Пакет %s: файлов %d; общий текст — %d знаков" % ("полный" if full else "облегчённый", len(files), len(text)))
    print("ZIP: %s (%d байт)" % (out, out.stat().st_size))
    print("Один файл для чата: %s" % md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
