#!/usr/bin/env python3
"""Полное эталонное прохождение игры со всеми фразами (DoD DESIGN_BIBLE §17: WALKTHROUGH_SPOILERS.md).

  python tools/texts/gen_walkthrough.py [ВЫХОД.md]      (по умолчанию docs/WALKTHROUGH_SPOILERS.md)

Источники: условия слотов `docs/BJ3_SLOT_FLAGS.md`, графы и отчёты солвера `acts/act*/`,
итоговые тексты `texts/act*/ACT*_TEXTS_FINAL.md` (реплики и документы — дословно),
плашки говорящих — таблицы §5 ТЗ актов, носители документов — `tools/assets/doc_preview.py`.

Устройство: по каждому акту — маршрут (обязательные действия графа по порядку прохождения),
затем шаги; в шаге — реплики обязательного действия, за ними всё, что можно сделать на том же
месте (осмотры, ошибки, повторы, по желанию); советы Предка — по темам в порядке приоритета;
предметы, отказы, интерфейс — отдельно. Документы печатаются там, где их открывают.
В конце — сверка: каждый слот текстов каждого акта в файле есть; иначе — ошибка.
Собранный файл руками не править: правятся тексты или таблица условий, затем сборка заново.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "texts"))
sys.path.insert(0, str(ROOT / "tools" / "assets"))
sys.path.insert(0, str(ROOT / "tools" / "data"))
import check_texts as CT  # noqa: E402
import doc_preview as DP  # noqa: E402
import gen_design as GD  # noqa: E402

ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}
# Порядок прохождения обязательных действий. Акты II–IV — порядок графа (он же кратчайший путь
# солвера); Акт I — естественный: меню нужно раньше вантуза (кромкой меню снимают присоску).
ORDER = {1: ["A11_take_menu_card", "N01_free_plunger", "A02_probe_mineral", "A03_call_reception",
             "A05_inspect_stars", "A06_fold_stars", "A07_peek_lobby", "A08_drive_out", "A09_shout_hot",
             "A10_talk_isolde"]}
# Где игрок управляет после шага, если это не видно по условиям реплик (сцены с переездом)
END_LOC = {1: {"A07_peek_lobby": "W1", "A08_drive_out": "W2", "A09_shout_hot": "W2", "A10_talk_isolde": "W2"}}
ZOOM_ROOM = {"Z01": "W1", "Z02": "W1", "Z03": "W1", "Z04": "W2", "Z05": "W2", "Z06": "W3", "Z07": "W3",
             "Z08": "W3", "Z09": "W4", "Z10": "W4", "Z11": "W4", "Z12": "W4", "Z13": "W6"}
PLACE = {"W1": "номер 317", "W2": "вестибюль, стойка Изольды", "W3": "прачечная", "W4": "зал прекраснодушия",
         "W5": "приёмный пункт", "W6": "контора старшего по воде",
         "Z01": "душевой узел", "Z02": "стол и мини-бар", "Z03": "тележка", "Z04": "стойка со служебной стороны",
         "Z05": "витрина экспоната", "Z06": "барабаны", "Z07": "«декоративная стена»", "Z08": "служебный шкаф",
         "Z09": "доска почёта", "Z10": "архивный стол и люк", "Z11": "зеркало и лифт",
         "Z12": "площадка внизу лестницы", "Z13": "стол конторы"}
GRAPH_ID = re.compile(r"\b([A-Z]\d{2}[a-z]?_[a-z0-9_]+|R\d_[a-z0-9_]+|[A-Z]\d{2}[a-z]?)\b")


def slot_rows():
    """{акт: [строка таблицы условий по порядку]}."""
    text = (ROOT / "docs" / "BJ3_SLOT_FLAGS.md").read_text(encoding="utf-8")
    acts, cur, intro = {}, None, {}
    for line in text.splitlines():
        m = re.match(r"## Акт (I{1,3}|IV) ", line)
        if m:
            cur = {"I": 1, "II": 2, "III": 3, "IV": 4}[m.group(1)]
            acts[cur] = []
            continue
        if cur and line.startswith("Приоритет тем Предка"):
            intro[cur] = re.findall(r"`([a-z_]+)`", line)
        if cur and line.startswith("| `"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4:
                continue
            slot = cells[0].strip("`")
            acts[cur].append({"slot": slot, "when": cells[1], "action": cells[2], "sets": cells[3]})
    return acts, intro


def esc(s):
    return s.replace("|", "\\|")


def main(argv=None):
    out_path = Path(argv[0]) if argv else ROOT / "docs" / "WALKTHROUGH_SPOILERS.md"
    rows_by_act, topic_order = slot_rows()
    speakers = GD.speaker_names()
    out = []
    w = out.append
    total_slots = total_lines = total_docs = 0
    problems = []

    w("# «Латунный янычар: Гидроудар» — полное прохождение со всеми фразами")
    w("")
    w("Эталон для автора: что делать, где и что при этом звучит — каждая реплика, титр, пункт меню и документ игры, дословно из итоговых текстов. "
      "Собрано генератором `tools/texts/gen_walkthrough.py` из `docs/BJ3_SLOT_FLAGS.md` (условия), графов актов (порядок) и `texts/act*/ACT*_TEXTS_FINAL.md` (тексты); руками не править — правятся тексты или условия, затем сборка заново.")
    w("")
    w("**Как читать.** У каждого акта сначала маршрут — обязательные действия по порядку. Дальше шаги: в шаге сначала реплики самого действия, затем «Здесь же» — всё, что можно сделать на том же месте (осмотры, неверные попытки, повторы, по желанию). "
      "Над каждым слотом — его имя, когда он звучит (флагами графа, как в таблице условий) и что меняет. Реплика: **ПЛАШКА** _(эмоция портрета)_ — текст; _[титр]_ — титр без портрета; ▸ — пункт меню выбора. Документы — цитатой там, где их открывают. "
      "Советы Предка — в конце акта по темам: тема открыта, пока верно её условие; ступени 1 → 2 → 3.")
    w("")

    for act in (1, 2, 3, 4):
        texts, _ = CT.parse_texts(ROOT / "texts" / f"act{act}" / f"ACT{act}_TEXTS_FINAL.md")
        graph = json.loads((ROOT / "acts" / f"act{act}" / f"ACT{act}_graph.json").read_text(encoding="utf-8"))
        actions = {a["id"]: a for a in graph["actions"]}
        report = json.loads((ROOT / "acts" / f"act{act}" / f"ACT{act}_solver_report.json").read_text(encoding="utf-8"))
        mand = report["info"]["shortest_path"]
        order = ORDER.get(act) or [a["id"] for a in graph["actions"] if a["id"] in mand]
        # порядок проверяется графом: каждое действие — когда его условия уже выполнены
        flags = set(graph["start_flags"])
        for a in order:
            miss = set(actions[a]["requires"]) - flags
            if miss:
                problems.append(f"Акт {act}: порядок прохождения нарушен у {a}: нет {sorted(miss)}")
            flags |= set(actions[a]["adds"])
        rows = rows_by_act[act]
        printed = set()

        def ids(cell):
            return [x for x in GRAPH_ID.findall(cell) if x in actions]

        def loc(row):
            m = re.search(r"(zoom|room):(W\d|Z\d\d)", row["when"])
            return m.group(2) if m else None

        def docs_in(row):
            return re.findall(r"`(DOC\.[a-z_0-9.]+)`", row["action"] + " " + row["when"])

        # шаг каждого обязательного действия и его место
        step_of = {a: i for i, a in enumerate(order)}
        step_rows = {i: [] for i in range(len(order))}
        step_loc = {}
        extra = {i: [] for i in range(len(order))}
        head, tail, hints, misc, docs_left = [], [], [], [], []
        last_step = None
        for r in rows:
            s = r["slot"]
            if s.startswith("HINT."):
                hints.append(r)
                continue
            if s.startswith(("INV.", "FB.", "UI.")):
                misc.append(r)
                continue
            if s.startswith("DOC."):
                docs_left.append(r)
                continue
            if s.startswith("OPEN."):
                head.append(r)
                continue
            if s.startswith("END."):
                tail.append(r)
                continue
            ms = [a for a in ids(r["action"]) if a in step_of]
            if ms:
                k = step_of[ms[0]]
                step_rows[k].append(r)
                if k not in step_loc and loc(r):
                    step_loc[k] = loc(r)
                last_step = k
                continue
            r["_after"] = last_step
        for k, a in enumerate(order):
            step_loc.setdefault(k, actions[a].get("room"))
        # что доступно после шага k: старт + обязательные до k + всё необязательное, что к тому времени можно
        gl = set(graph["flags_glossary"])
        # необязательное действие-альтернатива обязательному (те же последствия и больше) —
        # в «доступное» попадает не раньше своего обязательного шага
        alt_of = {}
        for x in actions.values():
            if x["optional"]:
                for i, a in enumerate(order):
                    if actions[a]["adds"] and set(actions[a]["adds"]) <= set(x["adds"]):
                        alt_of[x["id"]] = i
                        break
        avail = []
        have = set(graph["start_flags"])
        for k, a in enumerate(order):
            have |= set(actions[a]["adds"])
            changed = True
            while changed:
                changed = False
                for x in actions.values():
                    if (x["optional"] and alt_of.get(x["id"], -1) <= k and set(x["requires"]) <= have
                            and not set(x["adds"]) <= have):
                        have |= set(x["adds"])
                        changed = True
            avail.append(set(have))
        avail_before = [set(graph["start_flags"])] + avail[:-1]

        def positive(row):
            """Флаги графа, которые условие слота требует истинными (без ¬)."""
            out = set()
            for m in re.finditer(r"(¬?)`([a-z_0-9]+)`", row["when"]):
                if not m.group(1) and m.group(2) in gl:
                    out.add(m.group(2))
            return out

        def same_room(a, b):
            return a and b and ZOOM_ROOM.get(a, a) == ZOOM_ROOM.get(b, b)

        # попутные: на первом шаге, где у игрока уже есть флаги условия и он на том же месте;
        # пробы-альтернативы (необязательное действие с теми же последствиями) — рядом с обязательным
        for r in rows:
            if "_after" not in r:
                continue
            opt = [x for x in ids(r["action"]) if actions[x]["optional"]]
            alt = None
            for x in opt:
                for i, a in enumerate(order):
                    if set(actions[a]["adds"]) and set(actions[a]["adds"]) <= set(actions[x]["adds"]) and actions[x]["requires"] != actions[a]["requires"] or (
                            set(actions[a]["adds"]) == set(actions[x]["adds"])):
                        alt = (i, a)
                        break
                if alt:
                    break
            if alt:
                r["_alt"] = alt[1]
                extra[alt[0]].append(r)
                continue
            need = positive(r)
            L = loc(r)
            here = {i: END_LOC.get(act, {}).get(order[i], step_loc.get(i)) for i in range(len(order))}
            ok = [i for i in range(len(order)) if need <= avail[i]]
            k = None
            # условию нужен флаг, который даёт шаг, — реплика доступна с этого шага
            # нужный флаг даёт само обязательное действие шага — реплика доступна с этого шага
            prod = [i for i in ok if need & set(actions[order[i]]["adds"]) and not need <= avail_before[i]]
            if need and prod:
                k = prod[0]
            if k is None and L and L.startswith("Z"):
                k = next((i for i in ok if step_loc.get(i) == L), None)
            if k is None and L:
                k = next((i for i in ok if same_room(L, here[i])), None)
            if k is None:
                k = next((i for i in ok if r["_after"] is None or i >= r["_after"]), None)
            if k is None:
                k = len(order) - 1
            extra[k].append(r)

        def print_doc(d, indent=""):
            nonlocal total_docs
            if d in printed or d not in texts:
                return
            printed.add(d)
            body = texts[d].get("doc") or []
            carrier = DP.DOC.get(d, ("—",))[0]
            w(f"{indent}> **Документ `{d}`** — носитель `{carrier}`:")
            w(f"{indent}>")
            for ln in body:
                w(f"{indent}> {esc(ln) if ln.strip() else '&nbsp;'}  ")
            w("")
            total_docs += 1
            # подпись к документу (титр при открытии)
            for r2 in docs_left:
                if r2["slot"].startswith(d + ".") and r2["slot"] not in printed:
                    print_row(r2)

        def print_row(r, note=""):
            nonlocal total_slots, total_lines
            s = r["slot"]
            if s in printed:
                return
            printed.add(s)
            t = texts.get(s)
            act_cell = r["action"].replace("`", "")
            sets = r["sets"].replace("`", "")
            w(f"##### `{s}`{note}")
            w(f"<sub>когда: {esc(r['when'].replace('`', ''))} · граф: {esc(act_cell)} · ставит: {esc(sets)}</sub>")
            w("")
            if t is None:
                problems.append(f"Акт {act}: слот {s} есть в таблице условий, но нет в текстах")
                w("_(текста нет)_")
                w("")
                return
            total_slots += 1
            if t.get("silence") and not t["lines"]:
                w("_(без реплик)_")
            for l in t["lines"]:
                total_lines += 1
                sp, em, tx = l["speaker"], l["emotion"], esc(l["text"])
                if sp == "cap":
                    w(f"- _[титр]_ {tx}")
                elif sp == "choice":
                    w(f"- ▸ **пункт меню:** {tx}")
                elif sp == "ui":
                    w(f"- _[надпись интерфейса]_ {tx}")
                else:
                    name = speakers.get(sp, sp)
                    emo = f" _({em})_" if em and em != "none" else ""
                    w(f"- **{name}**{emo}: {tx}")
            if t.get("doc") and s.startswith("DOC."):
                w("")
                print_doc(s)
            w("")
            for d in docs_in(r):
                print_doc(d)

        w(f"## Акт {ROMAN[act]} {graph.get('title', '')}".rstrip())
        title_line = next((l for l in (ROOT / "docs" / "BJ3_SLOT_FLAGS.md").read_text(encoding="utf-8").splitlines()
                           if l.startswith(f"## Акт {ROMAN[act]} ")), "")
        if title_line:
            out[-1] = "## " + title_line[3:]
        w("")
        w(f"Обязательных действий — {len(order)}; всего действий в графе — {len(actions)}. Цель акта (флаги): {', '.join(graph['act_goal_flags'])}.")
        w("")
        w("**Маршрут:**")
        w("")
        for k, a in enumerate(order, 1):
            L = step_loc.get(k - 1)
            place = f" — {PLACE.get(L, L)}" if L else ""
            w(f"{k}. {actions[a]['name']} (`{a}`{place})")
        w("")
        if head:
            w(f"### Начало акта")
            w("")
            for r in head:
                print_row(r)
        for k, a in enumerate(order):
            L = step_loc.get(k)
            w(f"### Шаг {k + 1}. {actions[a]['name']}")
            w(f"<sub>`{a}` · место: {PLACE.get(L, L or '—')}{' (' + L + ')' if L else ''} · нужно: {', '.join(actions[a]['requires']) or '—'} · даёт: {', '.join(actions[a]['adds'])}</sub>")
            w("")
            for r in step_rows[k]:
                print_row(r)
            rest = [r for r in extra[k] if r["slot"] not in printed]
            alts = [r for r in rest if r.get("_alt")]
            if alts:
                w(f"#### Вместо этого можно")
                w("")
                for r in alts:
                    opt = [x for x in ids(r["action"]) if x in actions and actions[x]["optional"]]
                    print_row(r, f" — то же действие другим способом ({', '.join(opt)})")
            rest = [r for r in rest if not r.get("_alt")]
            groups = {}
            for r in rest:
                groups.setdefault(loc(r), []).append(r)
            for L, rs in groups.items():
                where = f"{PLACE.get(L, L)} ({L})" if L else "в разговоре, меню и сценах"
                w(f"#### Здесь же — {where}")
                w("")
                for r in rs:
                    opt = [x for x in ids(r["action"]) if x in actions and actions[x]["optional"]]
                    print_row(r, f" — по желанию ({', '.join(opt)})" if opt else "")
        if tail:
            w("### Конец акта")
            w("")
            for r in tail:
                print_row(r)
        if hints:
            w(f"### Советы Предка (Акт {ROMAN[act]})")
            w("")
            if topic_order.get(act):
                w(f"Приоритет тем: {' → '.join(topic_order[act])}.")
                w("")
            for r in hints:
                print_row(r)
        if misc:
            w(f"### Предметы в руках, отказы, интерфейс (Акт {ROMAN[act]})")
            w("")
            for r in misc:
                print_row(r)
        left = [r for r in docs_left if r["slot"] not in printed]
        if left:
            w(f"### Документы, не открытые по ходу (Акт {ROMAN[act]})")
            w("")
            for r in left:
                print_row(r)
        missing = [s for s in texts if s not in printed]
        if missing:
            w(f"### Слоты без строки в таблице условий (Акт {ROMAN[act]})")
            w("")
            for s in missing:
                print_row({"slot": s, "when": "—", "action": "—", "sets": "—"})
            problems.append(f"Акт {act}: слоты есть в текстах, но нет в таблице условий: {', '.join(missing)}")

    w("---")
    w("")
    w(f"Сверка: слотов {total_slots}, реплик и титров {total_lines}, документов {total_docs}. "
      + ("Каждый слот текстов каждого акта — в файле." if not problems else "Есть замечания — см. вывод генератора."))
    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    for p in problems:
        print("ЗАМЕЧАНИЕ", p)
    print(f"{out_path}: слотов {total_slots}, реплик {total_lines}, документов {total_docs}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
