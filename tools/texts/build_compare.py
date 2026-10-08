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

Слоты, где обе версии совпадают буква в букву (после приведения
типографики), в сравнение не попадают: сравнивать нечего. Их список
печатается в конце страницы.

Запуск:
    python tools/texts/build_compare.py [--names БЫЛО,СТАЛО] [--lede "…"] \
        ВЕРСИЯ_1.md ВЕРСИЯ_2.md ВЫХОД.html [ТЗ.md]
    (ТЗ по умолчанию — Акта I; акт и название берутся из заголовка ТЗ)

--names — подписи версий, которые откроются вместе со счётом (по умолчанию
«Claude» и «другая нейросеть»: первая версия — Claude, вторая — другая).
--lede — фраза для шапки страницы вместо стандартной «Две версии написаны
по одному ТЗ…». В голосах первая версия всегда записывается как «claude»,
вторая — как «other», в этом же порядке их принимает merge_texts.py.
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
DEFAULT_LEDE = ("Две версии написаны по одному ТЗ: одна — Claude, другая — "
                "другой нейросетью.")


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


ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}


def act_title(brief_path):
    head = Path(brief_path).read_text(encoding="utf-8").splitlines()[0]
    m = re.search(r"«([^»]+)»", head)
    return m.group(1) if m else ""


def build(brief_path, claude_path, other_path, names=None, lede=None):
    brief = ct.parse_brief(brief_path)
    act = ct.detect_act(brief_path)
    secs = sections(brief_path)
    versions = []
    for p in (claude_path, other_path):
        texts, fmt = ct.parse_texts(p)
        errs, _, _ = ct.check(brief, texts, fmt, act)
        versions.append((texts, errs))
    rnd = random.Random(SEED)
    slots, same, key = [], [], bytearray()
    for sid, spec in brief.items():
        # Жребий тянется для каждого слота ТЗ, даже пропущенного: так порядок
        # A/B в остальных слотах не зависит от того, сколько слотов совпало.
        claude_first = rnd.random() < 0.5
        vc = variant(versions[0][0].get(sid))
        vo = variant(versions[1][0].get(sid))
        if vc == vo:
            same.append({"id": sid, "sec": secs.get(sid, "")})
            continue
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
        "act": ROMAN[act], "title": act_title(brief_path),
        "names": list(names) if names else None, "lede": lede or DEFAULT_LEDE,
        "slots": slots, "same": same, "k": base64.b64encode(bytes(key)).decode(),
        "globalErrors": common,
    }


TEMPLATE = Path(__file__).with_name("compare_template.html")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    names, lede = None, None
    while argv and argv[0].startswith("--"):
        flag = argv.pop(0)
        if flag == "--names" and argv:
            names = [s.strip() for s in argv.pop(0).split(",")]
            if len(names) != 2 or not all(names):
                print("--names: нужны две подписи через запятую")
                return 2
        elif flag == "--lede" and argv:
            lede = argv.pop(0).strip()
        else:
            print(__doc__)
            return 2
    if len(argv) not in (3, 4):
        print(__doc__)
        return 2
    data = build(argv[3] if len(argv) == 4 else ct.DEFAULT_BRIEF, argv[0], argv[1],
                 names, lede)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (TEMPLATE.read_text(encoding="utf-8")
            .replace("__ACT__", data["act"]).replace("__TITLE__", data["title"])
            .replace("__LEDE__", data["lede"]).replace("__DATA__", payload))
    Path(argv[2]).write_text(html, encoding="utf-8")
    n_auto = sum(1 for s in data["slots"] if s["auto"])
    print("Страница: %s; слотов в ТЗ %d, без изменений %d, в сравнении %d "
          "(в голосовании %d, по правилам ТЗ решено %d)"
          % (argv[2], len(data["slots"]) + len(data["same"]), len(data["same"]),
             len(data["slots"]), len(data["slots"]) - n_auto, n_auto))
    return 0


if __name__ == "__main__":
    sys.exit(main())
