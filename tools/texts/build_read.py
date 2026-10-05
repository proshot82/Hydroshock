#!/usr/bin/env python3
"""Страница для чтения сценария: итоговые тексты актов карточками, как на
странице слепого сравнения, но одна версия на слот и поле правки под каждым.

Берёт пары «итоговый файл акта + его ТЗ» и ничего в текстах не меняет:
типографика и «ё» — как в файле. Над слотом — «Когда» и «Обязано быть» из
таблицы §9 ТЗ, разделы — подразделы §9. Итоговый файл, не прошедший проверку
по ТЗ (check_texts.py), на страницу не попадает.

Правки автор пишет прямо на странице; они хранятся в базе страницы
(`notes/<акт>:<слот>`, например `notes/III:OPEN.door`), их читает Claude.

Запуск:
    python tools/texts/build_read.py ВЫХОД.html ИТОГ.md ТЗ.md [ИТОГ.md ТЗ.md ...]
"""

import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_texts as ct  # noqa: E402
from build_compare import ROMAN, act_title, sections, strip_md  # noqa: E402

TEMPLATE = Path(__file__).with_name("read_template.html")


def status(final_path):
    """Состояние текстов по шапке итогового файла (до первого слота)."""
    head = Path(final_path).read_text(encoding="utf-8").split("\n### ", 1)[0]
    if "ждёт чтения" in head:
        return "ждёт чтения автора"
    if "заморож" in head:
        return "заморожен автором"
    if "риняты автором" in head:
        return "принят автором"
    return ""


def slot_view(slot):
    if slot is None:
        return {"silence": False, "doc": None, "lines": []}
    doc = None
    if slot["doc"] is not None:
        doc = list(slot["doc"])
        while doc and not doc[-1].strip():
            doc.pop()
    return {
        "silence": slot["silence"],
        "doc": doc,
        "lines": [{"sp": l["speaker"], "em": l["emotion"], "t": l["text"]}
                  for l in slot["lines"]],
    }


def build_act(final_path, brief_path):
    """Данные одного акта; ValueError, если итоговый файл не проходит ТЗ."""
    brief = ct.parse_brief(brief_path)
    act = ct.detect_act(brief_path)
    texts, fmt = ct.parse_texts(final_path)
    errs, _, _ = ct.check(brief, texts, fmt, act)
    if errs:
        raise ValueError("%s не проходит проверку по ТЗ:\n  %s" % (
            final_path, "\n  ".join("%s: %s" % (s or "файл", m) for s, m in errs)))
    secs = sections(brief_path)
    slots = []
    for sid, spec in brief.items():
        v = slot_view(texts.get(sid))
        v.update({"id": sid, "sec": secs.get(sid, ""), "star": spec["star"],
                  "when": strip_md(spec["when"]), "must": strip_md(spec["must"])})
        slots.append(v)
    return {
        "act": ROMAN[act], "title": act_title(brief_path), "status": status(final_path),
        "lines": sum(len(s["lines"]) for s in slots), "slots": slots,
    }


def build(pairs, today=None):
    today = today or datetime.date.today()
    return {"built": today.strftime("%d.%m.%Y"),
            "acts": [build_act(f, b) for f, b in pairs]}


def render(data):
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", payload)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 3 or len(argv) % 2 == 0:
        print(__doc__)
        return 2
    pairs = list(zip(argv[1::2], argv[2::2]))
    try:
        data = build(pairs)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    Path(argv[0]).write_text(render(data), encoding="utf-8")
    for a in data["acts"]:
        print("Акт %s «%s»: слотов %d, реплик %d, ключевых %d — %s"
              % (a["act"], a["title"], len(a["slots"]), a["lines"],
                 sum(1 for s in a["slots"] if s["star"]), a["status"] or "состояние не указано"))
    print("Страница: %s" % argv[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
