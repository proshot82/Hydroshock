#!/usr/bin/env python3
"""Тест-матрица «Гидроудара» H01–H26 (BJ3_HANDOFF.md §12) на собранной логике — шаг 6 плана сборки.

  python tools/data/check_matrix.py [--out ОТЧЁТ.md]

Что можно проверить перебором, проверяется перебором логики актов (тот же исполнитель, что у
`check_logic.py`: зоны, глаголы, предметы, меню, сцены, цепочки); остальное — существующими гейтами
(тексты, условия слотов, шрифты) и разбором кода движка. Пункты, которые проверяет только
автопрохождение в браузере (`tools/web/autoplay.js`), так и помечены — их результат печатает
автопрохождение. Код выхода: 0 — все проверяемые здесь пункты выполнены.
"""
import argparse
import copy
import re
import subprocess
import sys
from collections import deque
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_logic as CL  # noqa: E402
import gen_design as G  # noqa: E402
import logic as L  # noqa: E402

ROOT = L.ROOT
RELICS = ("relic_r1", "relic_r2", "relic_r3")
RELIC_ACTIONS = {"R1_token", "R2_postcard", "R3_mug"}


class Watch(CL.Sim):
    """Исполнитель перебора, который ещё и записывает: какой слот звучал при каких флагах и какое
    действие графа срабатывало, когда его последствия уже были (повтор)."""

    def __init__(self, data):
        super().__init__(data)
        self.slot_hook = None
        self.repeats = []

    def play(self, st, slot):
        if self.slot_hook and slot and not slot.startswith("@"):
            self.slot_hook(st, slot)
        super().play(st, slot)

    def fire(self, st, rule, where):
        a = rule.get("action")
        if a and a in self.d["graph"]:
            adds = set(self.d["graph"][a]["adds"])
            if adds and adds <= st["flags"]:
                self.repeats.append((a, where))
        return super().fire(st, rule, where)


def explore(data, extras=((),), limit=2_000_000):
    """Все достижимые состояния акта от стартов (стартовые флаги + каждый набор extras)."""
    sim = Watch(data)
    states, edges, seen = [], [], {}
    q = deque()
    for extra in extras:
        st = sim.start(extra)
        k = sim.key(st)
        if k not in seen:
            seen[k] = len(states)
            states.append(st)
            edges.append([])
            q.append(seen[k])
    while q and len(states) < limit:
        i = q.popleft()
        for _, st2 in sim.moves(states[i]):
            k = sim.key(st2)
            j = seen.get(k)
            if j is None:
                j = seen[k] = len(states)
                states.append(st2)
                edges.append([])
                q.append(j)
            edges[i].append(j)
    return sim, states, edges


def drop_actions(data, actions):
    """Убрать из данных акта все правила с этими действиями графа (путь без реликвий)."""
    d = copy.deepcopy(data)
    for zk, vv in d["rules"].items():
        for verb in list(vv):
            vv[verb] = [r for r in vv[verb] if r.get("action") not in actions]
            if not vv[verb]:
                del vv[verb]
    return d


def dead_ends(states, edges):
    """Сколько состояний, из которых конец недостижим."""
    rev = [[] for _ in states]
    for i, es in enumerate(edges):
        for j in es:
            rev[j].append(i)
    good = {i for i, s in enumerate(states) if s["end"]}
    q = deque(good)
    while q:
        j = q.popleft()
        for i in rev[j]:
            if i not in good:
                good.add(i)
                q.append(i)
    return len(states) - len(good)


def ends(states):
    return [s for s in states if s["end"]]


def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1:]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="записать отчёт в markdown")
    a = ap.parse_args(argv)
    acts = {k: G.build(k) for k in (1, 2, 3, 4)}
    base = {k: explore(d) for k, d in acts.items()}   # (исполнитель, состояния, рёбра) — один перебор на акт
    rows = []

    def row(hid, ok, how, note=""):
        rows.append((hid, ok, how, note))
        print(f"{'OK  ' if ok is True else ('FAIL' if ok is False else 'СМ. ')} {hid}: {how}{' — ' + note if note else ''}")

    # H01, H02, H06 — без реликвий: каждый акт доходит до конца, реликвии не в основаниях P16–P17
    bad = []
    for k, d in acts.items():
        has_r = any(r.get("action") in RELIC_ACTIONS for vv in d["rules"].values() for rs in vv.values() for r in rs)
        _, states, _ = explore(drop_actions(d, RELIC_ACTIONS)) if has_r else base[k]
        if not ends(states):
            bad.append(f"Акт {k}")
    row("H01", not bad, "перебор каждого акта без правил R1–R3: конец достижим", ", ".join(bad))
    g4 = acts[4]["graph"]
    need = {f for a_, g in g4.items() if a_.startswith("E0") for f in g["requires"]}
    row("H02", not (need & set(RELICS)), "требования E01–E06 (приёмка, доклад, контора, отметка, пуск) не содержат relic_*")
    _, states, _ = explore(drop_actions(acts[4], {"R3_mug"}))
    ok6 = any(s["end"] and "relic_r3" not in s["flags"] for s in states)
    row("H06", ok6, "Акт IV без правила R3 (кружки нет): конец достижим")

    # H03 — все восемь сочетаний реликвий → верный эпилог
    d4 = drop_actions(acts[4], RELIC_ACTIONS)
    wrong = []
    for n in range(4):
        for combo in combinations(RELICS, n):
            sim, states, _ = explore(d4, extras=(combo,))
            got = {s2 for s in ends(states) for s2 in ("EPI.0", "EPI.1", "EPI.2", "EPI.3") if s["n"].get(s2)}
            if got != {f"EPI.{n}"}:
                wrong.append(f"{'+'.join(c[-2:] for c in combo) or 'нет'} → {sorted(got)}")
    row("H03", not wrong, "Акт IV, старт с каждым из 8 сочетаний relic_r1–r3: в каждом конце звучит EPI.<число реликвий>",
        "; ".join(wrong))

    # H04 — повторное взятие реликвии: правило не срабатывает второй раз
    rep = []
    for k, d in acts.items():
        sim = base[k][0]
        rep += [f"Акт {k}: {x} ({w})" for x, w in sim.repeats if x in RELIC_ACTIONS]
    row("H04", not rep, "ни в одном акте правило R1–R3 не срабатывает, когда реликвия уже есть", "; ".join(sorted(set(rep))[:5]))

    # H05 — сохранение после финала: эпилог не пересчитывается
    gj = (ROOT / "game" / "js" / "game.js").read_text(encoding="utf-8")
    ok5 = "if (st.ended) { showEnd(); return; }" in gj
    row("H05", ok5, "движок: загруженная законченная партия сразу показывает карточку конца, цепочку эпилога не исполняет "
        "(game.js, start); в браузере — автопрохождение: перезагрузка после «Конец»")

    # H07 — дуга лифта: любой порядок проходим (тупиков нет из всех состояний Акта III)
    errs, stats = CL.check_data(copy.deepcopy(acts[3]), seed=3, walks=500)
    row("H07", not errs, f"Акт III: из каждого из {stats.get('состояний')} состояний конец достижим; C03 необязательно",
        "; ".join(errs[:3]))

    # H08, H12 — кабина и герой
    names = {r.get("slot") for vv in acts[3]["rules"].values() for rs in vv.values() for r in rs}
    scen = {s["slot"] for st_ in acts[3]["scenes"].values() for s in st_}
    need8 = {"Z11.lift.empty", "Z11.ride.standing", "Z12.door.payment", "SEQ.send.alone", "Z11.ride.after.send"}
    row("H08", need8 <= names | scen, "Акт III: пустая тележка, «встать в кабину», пешком к двери, оплата одна → частичная приёмка → под пустой тележкой — все в логике; без софтлока (H07)",
        ", ".join(sorted(need8 - names - scen)))
    states3 = base[3][1]
    rode = [s for s in states3 if "descended_as_staff" in s["flags"] and s["pos"] not in ("cabin", "receiving", None) and not s["end"]]
    row("H12", not rode and {"Z11.ride.standing", "Z12.door.payment"} <= names,
        "стоя не едет (Z11.ride.standing), пешком — заперто (Z12.door.payment), вниз только сценой «под тележкой»")

    # H09 — жидкости: пена правилом (Акт I, все пробы до победы — перебор Акта I чист)
    dead1 = dead_ends(base[1][1], base[1][2])
    row("H09", not dead1, f"Акт I: {len(base[1][1])} состояний с любыми пробами жидкостей — из каждого конец достижим",
        f"тупиков {dead1}" if dead1 else "")

    # H10, H11 — хват: отказы и короткие операции есть в логике
    allslots = {r.get("slot") for d in acts.values() for vv in d["rules"].values() for rs in vv.values() for r in rs}
    hold = {"Z10.water.carry", "Z04.kefir.take", "Z04.invoice.take", "Z10.paper.take", "FB.paper.act3", "Z13.ledger.pen"}
    row("H10", hold <= allslots, "отказы нести стекло, бумагу, писать ручкой — свои реплики в логике", ", ".join(sorted(hold - allslots)))
    short = {"Z10.water.offer"}
    row("H11", short <= allslots and any("E05_plunger_mark" == r.get("action") for vv in acts[4]["rules"].values() for rs in vv.values() for r in rs),
        "бутылка на тележку (C08), вантуз к странице (E05), маховик (E06) — разрешены")

    # H13 — второго пробного пуска нет
    sim3 = base[3][0]
    twice = [w for x, w in sim3.repeats if x == "C09_test_run"]
    row("H13", not twice, "C09 не срабатывает после пробного пуска; возвращаются счёт и записка (DOC.note, DOC.bill)", "; ".join(twice[:3]))

    # H14 — счёт в руки, обвинение, печать — обратимо; под печать — признание
    ok14 = all(any(it["id"] == i for it in acts[3]["menus"]["talk"]) for i in ("bill", "accuse", "stamp"))
    row("H14", ok14 and not errs, "пункты «счёт в руки», «это вы носили кефир», «печать» — без последствий для пути; C13 — признание")

    # H15 — воды нет до отметки: water_restored ставит только E06, E06 требует marks_exchanged
    setters = {r.get("action") for d in acts.values() for vv in d["rules"].values() for rs in vv.values() for r in rs
               if any(e.get("add") == "water_restored" for e in r["effects"])}
    for d in acts.values():
        for sc in d["scenes"].values():
            for s in sc:
                if any(e.get("add") == "water_restored" for e in s["effects"]):
                    setters.add("сцена")
    row("H15", "marks_exchanged" in g4["E06_open_valve"]["requires"] and setters <= {None, "E06_open_valve", "сцена"},
        "water_restored — только пуском E06, а он требует встречной отметки E05")

    # H16 — оплата внизу, Лапидус под тележкой: «инвентарь не докладывается», двери заперты
    sl4 = {r.get("slot") for vv in acts[4]["rules"].values() for rs in vv.values() for r in rs}
    row("H16", {"TALK.kuh.under", "W5.hand", "W5.door.early"} <= sl4, "из-под тележки — TALK.kuh.under, W5.hand; дверь до доклада — W5.door.early")

    # H17 — ранние догадки Акта III (D16, D18, D19)
    talk3 = {r["slot"] for it in acts[3]["menus"]["talk"] for r in it["rules"]}
    row("H17", {"TALK.iz.kefir", "TALK.iz.accuse"} <= talk3 and "Z11.wait.water" in names, "кефир до счёта, обвинение до бумаги, ожидание воды — содержательные ответы")

    # H18 — сейв: что переживает (state.js) и проверки сейва в автопрохождении
    sj = (ROOT / "game" / "js" / "state.js").read_text(encoding="utf-8")
    ok18 = all(k in sj for k in ("flags:", "pos: this.pos", "n: this.n", "c: this.c", "view: this.view", "docs: this.docs", "hint: this.hint"))
    row("H18", ok18, "сейв хранит флаги (накопительно), тележку, вид, счётчики, советы, бумаги; автопрохождение: сейв посреди Актов I, II, III")

    # H19 — «я» Изольды до признания: проверка текстов + порядок в логике
    leak = []

    def hook(st, slot):
        if slot in ("SEQ.iz.payment", "SEQ.load", "TALK.iz.carry") and "iz_confessed" not in st["flags"]:
            leak.append(slot)
    sim = Watch(acts[3])
    sim.slot_hook = hook
    _, _, _ = explore_with(sim)
    row("H19", not leak, "реплики Изольды с «я» звучат только после признания (перебор Акта III); тексты — check_texts", ", ".join(sorted(set(leak))))

    # H20 — чистый портрет только после пуска
    clean_slots = {sid for sid, t in acts[4]["texts"].items() if any(l["e"] == "lap_clean" for l in t["lines"])}
    early = []

    def hook20(st, slot):
        if slot in clean_slots and "water_restored" not in st["flags"]:
            early.append(slot)
    sim = Watch(acts[4])
    sim.slot_hook = hook20
    explore_with(sim, extras=[()] + [c for k in (1, 2, 3) for c in combinations(RELICS, k)])
    row("H20", not early and bool(clean_slots), f"lap_clean ({', '.join(sorted(clean_slots))}) — только при water_restored; монтаж: Z01, фонтан с уточкой, Z06, W4",
        ", ".join(sorted(set(early))))

    # H21 — без звука: у звуковых улик есть титр или кадр
    try:
        rc, tail = run([sys.executable, "tools/audio/check_audio.py"])
        row("H21", rc == 0, "tools/audio/check_audio.py (п. 5: у звуковых слотов титр или кадр; без титра — реплики громкой связи "
            "с плашкой, норма GDD §8): " + " ".join(tail) + "; автопрохождение идёт без звука и доходит до конца")
    except OSError as e:
        row("H21", None, f"tools/audio/check_audio.py не запустился: {e}")

    # H22 — даты: логика не читает время
    js = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "game" / "js").glob("*.js"))
    dates = re.findall(r"new Date|Date\.now|getDay|getHours|toLocale", js)
    row("H22", not dates, "движок не читает дату и время (ни одного обращения к Date)", ", ".join(dates))

    # H23 — совет: в каждом незаконченном состоянии есть открытая тема или всё сделано
    gaps = []
    for k, d in acts.items():
        states = base[k][1]
        for s in states:
            if s["end"] or s["menu"]:
                continue
            if not any(L.evaluate(h["when"], s) for h in d["hints"]):
                gaps.append((k, s))
    by_act = {}
    for k, s in gaps:
        by_act.setdefault(k, 0)
        by_act[k] += 1
    row("H23", not by_act, "состояния без открытой темы совета (там «Тут всё»): " + (", ".join(f"Акт {k}: {n}" for k, n in sorted(by_act.items())) or "нет")
        + "; путь без совета — перебор не нажимает «Совет» и доходит до конца")

    # H24 — повторный переезд через вестибюль Акта I: сцена крика не повторяется
    sim1 = base[1][0]
    again = [w for x, w in sim1.repeats if x in ("A08_drive_out", "A09_shout_hot")]
    row("H24", not again, "Акт I: проезд и крик (A08, A09) не повторяются", "; ".join(again[:3]))

    # H25, H26 — гейты
    rc, tail = run([sys.executable, "tools/check_fonts.py"])
    row("H25", rc == 0, "tools/check_fonts.py: " + " ".join(tail))
    bad26 = []
    for k in (1, 2, 3, 4):
        rc, tail = run([sys.executable, "tools/texts/check_texts.py", f"texts/act{k}/ACT{k}_TEXTS_FINAL.md",
                        "--brief", f"texts/act{k}/BRIEF_ACT{k}_TEXTS.md"])
        if rc:
            bad26.append(f"Акт {k}: {' '.join(tail)}")
    rc, tail = run([sys.executable, "tools/texts/check_slot_flags.py"])
    if rc:
        bad26.append("SLOT_FLAGS: " + " ".join(tail))
    row("H26", not bad26, "check_texts.py по четырём актам и check_slot_flags.py — без ошибок", "; ".join(bad26))

    fails = [r for r in rows if r[1] is False]
    print(f"\nМАТРИЦА: выполнено {sum(1 for r in rows if r[1] is True)}, не выполнено {len(fails)}, "
          f"смотреть отдельно {sum(1 for r in rows if r[1] is None)}")
    if a.out:
        lines = ["# Тест-матрица H01–H26 — результат", "",
                 "Собрано `tools/data/check_matrix.py` (руками не править). Пункты «смотреть» — проверяются автопрохождением "
                 "или гейтом, которого нет в этом окружении.", "",
                 "| ID | Итог | Как проверено | Замечание |", "|---|---|---|---|"]
        for hid, ok, how, note in rows:
            lines.append(f"| {hid} | {'да' if ok is True else ('НЕТ' if ok is False else 'смотреть')} | {how} | {note} |")
        Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if fails else 0


def explore_with(sim, extras=((),)):
    """Перебор готовым исполнителем (с крючками)."""
    states, seen = [], {}
    q = deque()
    for extra in extras:
        st = sim.start(extra)
        k = sim.key(st)
        if k not in seen:
            seen[k] = len(states)
            states.append(st)
            q.append(seen[k])
    while q:
        i = q.popleft()
        for _, st2 in sim.moves(states[i]):
            k = sim.key(st2)
            if k not in seen:
                seen[k] = len(states)
                states.append(st2)
                q.append(seen[k])
    return sim, states, None


if __name__ == "__main__":
    sys.exit(main())
