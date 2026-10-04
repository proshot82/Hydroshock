#!/usr/bin/env python3
"""Импорт текстов акта, скопированных из чата другой нейросети, в формат §8 ТЗ.

Чат или Google Docs при копировании портит разметку, а не текст:
  • экранирует символы: «\\_», «\\!», «\\-», «\\.»;
  • делает заголовки слотов жирными: «### **OPEN.1\\_voucher**»;
  • ставит в конце строк по два пробела (переносы Markdown);
  • вместо блока ```text … ``` оставляет слово «Plaintext» и голые строки.

Скрипт меняет только это. Сам текст реплик не трогается, и это проверяется:
скелет входа (без экранирования, разметки и пробелов) обязан совпасть со
скелетом выхода, иначе файл не записывается.

Запуск:
    python tools/texts/import_texts.py СЫРОЙ.md ВЫХОД.md [ТЗ.md]
    (ТЗ по умолчанию — Акта I; для Акта II: texts/act2/BRIEF_ACT2_TEXTS.md)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_texts as ct  # noqa: E402

ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|>~=])")
HEAD = re.compile(r"^#{2,4}\s*\**`?\s*(" + ct.SLOT_ID + r")\s*`?\**\s*$")
DOC_LABELS = {"plaintext", "text", "txt", "markdown"}


def unescape(line):
    return ESCAPE.sub(r"\1", line)


def convert(raw, brief):
    out = []
    lines = [unescape(l.rstrip()) for l in raw.splitlines()]
    i = 0
    while i < len(lines):
        m = HEAD.match(lines[i].strip())
        if not m:
            out.append(lines[i])
            i += 1
            continue
        sid = m.group(1)
        out.append("### " + sid)
        i += 1
        body = []
        while i < len(lines) and not HEAD.match(lines[i].strip()):
            body.append(lines[i])
            i += 1
        spec = brief.get(sid)
        has_fence = any(l.strip().startswith("```") for l in body)
        if spec and spec["kind"] == "doc" and not has_fence:
            tail = []
            while body and (not body[-1].strip()
                            or body[-1].strip() == "ПРОДОЛЖЕНИЕ СЛЕДУЕТ"
                            or re.match(r"^КОНЕЦ АКТА [IV]+$", body[-1].strip())):
                tail.insert(0, body.pop())
            while body and not body[0].strip():
                body.pop(0)
            if body and body[0].strip().lower() in DOC_LABELS:
                body.pop(0)
            while body and not body[0].strip():
                body.pop(0)
            out.append("```text")
            out.extend(body)
            out.append("```")
            out.extend(tail)
        else:
            for l in body:
                s = l.strip()
                # строка «ui | … | В РУКАХ» и сразу «КОНЕЦ АКТА …» — разные строки
                out.append(s if s else "")
    return "\n".join(out).rstrip("\n") + "\n"


def skeleton(text):
    """Только смысловые символы: без разметки, экранирования и пробелов."""
    t = unescape(text)
    t = re.sub(r"```\w*", "", t)
    t = re.sub(r"(?im)^\s*(plaintext|text|txt|markdown)\s*$", "", t)
    t = t.replace("*", "")
    return re.sub(r"\s+", "", t)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) not in (2, 3):
        print(__doc__)
        return 2
    src, dst = Path(argv[0]), Path(argv[1])
    raw = src.read_text(encoding="utf-8-sig")
    # третий аргумент — ТЗ акта (по умолчанию — ТЗ Акта I)
    brief = ct.parse_brief(argv[2] if len(argv) == 3 else ct.DEFAULT_BRIEF)
    res = convert(raw, brief)
    if skeleton(raw) != skeleton(res):
        print("Отказ: после импорта изменился сам текст, файл не записан.")
        return 1
    dst.write_text(res, encoding="utf-8")
    print("Импортировано: %s → %s (текст не изменён, правлена только разметка)"
          % (src, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
