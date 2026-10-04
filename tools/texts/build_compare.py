#!/usr/bin/env python3
"""Страница слепого сравнения двух версий текстов акта.

Берёт ТЗ (слоты, контекст, разделы §9) и две версии в формате §8, приводит
типографику к одному виду (кавычки, тире, многоточия; «ё» → «е» в обеих
версиях, чтобы авторство не угадывалось по орфографии) и собирает одну
HTML-страницу. Порядок вариантов A/B в каждом слоте — псевдослучайный, с
постоянным зерном: пересборка страницы не путает уже отданные голоса.

Слоты, где версия нарушила жёсткое правило ТЗ (§7, по check_texts.py),
в слепом голосовании не участвуют: по ТЗ они проиграны автоматически и
показываются только после раскрытия счёта.

Запуск:
    python tools/texts/build_compare.py ВЕРСИЯ_CLAUDE.md ДРУГАЯ.md ВЫХОД.html
"""

import base64
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_texts as ct  # noqa: E402

SEED = 20261004
KEY = 0x5A


def sections(brief_path):
    """Слот → название подраздела §9 ТЗ («Вступление», «Тележка»…)."""
    text = Path(brief_path).read_text(encoding="utf-8")
    start = text.find("\n## 9. Слоты")
    end = text.find("\n## 10.", start)
    cur, out = "", {}
    row = re.compile(r"^\|\s*`(" + ct.SLOT_ID + r")`\s*\|")
    for line in text[start:end].splitlines():
        m = re.match(r"^###\s+9\.\d+\.\s+(.+?)\s*$", line)
        if m:
            cur = re.sub(r"\s*\(.*\)$", "", m.group(1))
            continue
        m = row.match(line)
        if m:
            out[m.group(1)] = cur
    return out


def blind(text):
    return ct.norm_typo(text).replace("ё", "е").replace("Ё", "Е")


def variant(slot):
    if slot is None:
        return {"silence": False, "doc": None, "lines": []}
    doc = None
    if slot["doc"] is not None:
        doc = [blind(l) for l in slot["doc"]]
        while doc and not doc[-1].strip():
            doc.pop()
    return {
        "silence": slot["silence"],
        "doc": doc,
        "lines": [{"sp": l["speaker"], "em": l["emotion"], "t": blind(l["text"])}
                  for l in slot["lines"]],
    }


def strip_md(s):
    return s.replace("`", "")


def build(brief_path, claude_path, other_path):
    brief = ct.parse_brief(brief_path)
    secs = sections(brief_path)
    versions = []
    for p in (claude_path, other_path):
        texts, fmt = ct.parse_texts(p)
        errs, _, _ = ct.check(brief, texts, fmt)
        versions.append((texts, errs))
    rnd = random.Random(SEED)
    slots, key = [], bytearray()
    for sid, spec in brief.items():
        claude_first = rnd.random() < 0.5
        vc = variant(versions[0][0].get(sid))
        vo = variant(versions[1][0].get(sid))
        pair = [vc, vo] if claude_first else [vo, vc]
        key.append((0 if claude_first else 1) ^ KEY)
        auto = []
        for who, (_, errs) in zip(("claude", "other"), versions):
            reasons = [m for s, m in errs if s == sid]
            if reasons:
                auto.append({"who": who, "why": "; ".join(reasons)})
        slots.append({
            "id": sid, "sec": secs.get(sid, ""), "star": spec["star"],
            "when": strip_md(spec["when"]), "must": strip_md(spec["must"]),
            "auto": auto, "v": pair,
        })
    common = [m for s, m in versions[1][1] if s is None] + \
             [m for s, m in versions[0][1] if s is None]
    return {
        "act": "I", "title": "Комплимент от заведения",
        "slots": slots, "k": base64.b64encode(bytes(key)).decode(),
        "globalErrors": common,
    }


TEMPLATE = Path(__file__).with_name("compare_template.html")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 3:
        print(__doc__)
        return 2
    data = build(ct.DEFAULT_BRIEF, argv[0], argv[1])
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", payload)
    Path(argv[2]).write_text(html, encoding="utf-8")
    n_auto = sum(1 for s in data["slots"] if s["auto"])
    print("Страница: %s; слотов %d, в голосовании %d, по правилам ТЗ решено %d"
          % (argv[2], len(data["slots"]), len(data["slots"]) - n_auto, n_auto))
    return 0


if __name__ == "__main__":
    sys.exit(main())
