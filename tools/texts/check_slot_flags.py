#!/usr/bin/env python3
"""Сверка docs/BJ3_SLOT_FLAGS.md с ТЗ актов и графами.

Проверяет: каждый слот ТЗ (§9) есть в таблице своего акта ровно один раз и
лишних нет; каждый флаг в колонках «Когда» и «Ставит» существует в глоссарии
графа акта или в §0 документа; каждое действие в колонке «Действие графа»
есть в графе. Выход 0 — всё сходится.

Запуск: python tools/texts/check_slot_flags.py [docs/BJ3_SLOT_FLAGS.md]
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_texts as ct  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "BJ3_SLOT_FLAGS.md"
ACTS = {"I": 1, "II": 2, "III": 3, "IV": 4}
# имена из §0 документа (движок и тексты), не из графов
EXTRA = {"room", "zoom", "n", "shown", "hint", "probe", "call", "trolley", "combo", "relics",
         "menu", "hint.lock", "hint.n", "probe.n", "call.n", "trolley.pos"}
POSITIONS = {"room", "door", "lift", "lobby", "crowd", "service", "exhibit", "stairs", "hall",
             "cabin", "receiving", "office"}
TOPIC = re.compile(r"^[a-z]+$")


def tables(text):
    """Акт → список строк таблицы (список ячеек)."""
    out, act = {}, None
    for line in text.splitlines():
        m = re.match(r"^## Акт (I|II|III|IV)\b", line)
        if m:
            act = ACTS[m.group(1)]
            out[act] = []
            continue
        if act and line.startswith("| `"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4:
                out[act].append(cells)
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0]) if argv else DOC
    text = path.read_text(encoding="utf-8")
    errors = 0
    for act, rows in sorted(tables(text).items()):
        brief = ct.parse_brief(ROOT / "texts" / f"act{act}" / f"BRIEF_ACT{act}_TEXTS.md")
        graph = json.loads((ROOT / "acts" / f"act{act}" / f"ACT{act}_graph.json").read_text(encoding="utf-8"))
        flags = set(graph["flags_glossary"]) | set(graph["start_flags"])
        actions = {a["id"] for a in graph["actions"]}
        topics = {s.split(".")[1] for s in brief if s.startswith("HINT.") and s.count(".") == 2}
        seen = {}
        for sid, when, action, sets in rows:
            sid = sid.strip("`")
            seen[sid] = seen.get(sid, 0) + 1
            if sid not in brief:
                print(f"Акт {act}: слот `{sid}` — нет в ТЗ"); errors += 1
            for cell in (when, sets):
                for tok in re.findall(r"`([^`]+)`", cell):
                    base = tok.split("(")[0].split(":")[0].split("[")[0]
                    if tok.startswith(("DOC.", "room:", "zoom:", "shown(", "combo(", "hint.level(")):
                        continue
                    if re.match(r"^[A-Z][A-Z0-9]*\.", tok):   # ссылка на слот
                        if tok not in brief:
                            print(f"Акт {act}: `{sid}` ссылается на слот `{tok}`, которого нет в ТЗ"); errors += 1
                        continue
                    if tok in EXTRA or base in EXTRA or tok in POSITIONS:
                        continue
                    if TOPIC.match(tok) and tok in topics and "тема" in cell:
                        continue
                    if re.match(r"^[a-z][a-z0-9_]*$", tok):
                        if tok not in flags:
                            print(f"Акт {act}: `{sid}` — флаг `{tok}` не в графе"); errors += 1
                    else:
                        print(f"Акт {act}: `{sid}` — непонятный токен `{tok}`"); errors += 1
            for tok in re.findall(r"\b([A-Z]\d{2}[a-z]?_[A-Za-z0-9_]+|R\d_[a-z]+)\b", action):
                if tok not in actions:
                    print(f"Акт {act}: `{sid}` — действия `{tok}` нет в графе"); errors += 1
        for sid in brief:
            if sid not in seen:
                print(f"Акт {act}: слот ТЗ `{sid}` не описан"); errors += 1
        for sid, k in seen.items():
            if k > 1:
                print(f"Акт {act}: слот `{sid}` описан {k} раза"); errors += 1
        used = {a for a in actions if any(a in r[2] for r in rows)}
        missing = actions - used
        print(f"Акт {act}: слотов в ТЗ {len(brief)}, строк {len(rows)}, действий графа {len(actions)}, "
              f"не упомянуто действий: {', '.join(sorted(missing)) or 'нет'}")
    print("Итог: ошибок %d" % errors)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
