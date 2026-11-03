#!/usr/bin/env python3
"""План классического видеопрохождения («как на ютубе»): игра от начала до лучшей концовки без
перебора всех реплик — для записи тем же роботом, что и полное (tools/web/record_full.js).

  python tools/web/plan_walk.py [--out work/walkthrough/plan.json] [--acts 1,2,3,4]

Что делает игрок в таком видео: решает загадки в разумном порядке, смотрит улики, которые к ним
ведут, читает основные бумаги, собирает три реликвии (лучшая концовка) — и не делает ложных
попыток, не перебирает альтернативы, не жмёт «Совет», не возвращается к сохранениям.

Ходы — по действиям графа акта (acts/act*/ACT*_graph.json): все обязательные плюс отобранные
необязательные (WANT ниже). Путь — жадно: ближайший ход, на котором срабатывает ещё не сделанное
нужное действие; ходы, двигающие прохождение, дороже осмотров (та же цена, что в plan_full.py), —
сначала всё нужное на месте, потом шаг вперёд. Нужного больше нет — кратчайший путь к концу акта.
Пишет план в формате plan_full.py ({plan:[{act, moves:[{move, slots, action?}]}]}) — без ответвлений.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "web"))
import plan_full as PF  # noqa: E402

G, L = PF.G, PF.L

# Необязательные действия, которые делает игрок в классическом прохождении: улики и осмотры,
# которые ведут к решению, бумаги с историей места, реликвии. Не берутся: ложные попытки (O…,
# N01a–c), альтернативы пробы (A02b–f), обходные пути (C19, C16b, O12), повторы бумаг.
WANT = {
    1: {"A04_try_skirt", "A12_inspect_room", "A13_inspect_breakfast"},
    2: {"B01_pump_cascade", "B07_read_old_journal", "B08_open_vitrine", "B09_compare_plunger",
        "B11_inspect_board", "B12_scrape_plate", "B20_accuse_signature", "B21_read_soviet_memo",
        "B22_read_regulation", "B23_inspect_mirror", "B24_inspect_cladding",
        "R1_token", "R2_postcard", "R3_mug"},
    3: {"C03_photo_floor", "C12_watch_stamp"},
    4: {"O03_look_photo"},
}

# Порядок, как у думающего игрока: (сначала, потом) — второе не цель, пока не сделано первое.
# Акт III: сначала инструкция у двери конторы, от неё — фото «Четвергъ» (лифт стоял в зале),
# и уже потом порожек под зеркалом (иначе фото теряет смысл и выпадает).
ORDER = {
    3: [("C01_read_order", "*"), ("C03_photo_floor", "C04_threshold")],
}

# Главы для YouTube (тайм-коды в описании видео): с хода, на котором впервые срабатывает действие.
CHAPTERS = {
    1: [("A12_inspect_room", "Номер 317"), ("A02_probe_mineral", "Пена не смывается"),
        ("N01_free_plunger", "Вантуз на стекле душа"), ("A13_inspect_breakfast", "Тележка с завтраком"),
        ("A03_call_reception", "Звонок на стойку"), ("A07_peek_lobby", "Вестибюль"),
        ("A08_drive_out", "Под тележкой"), ("A09_shout_hot", "«Осторожно, горячее!»")],
    2: [("B01_pump_cascade", "«Влажное наваждение»"), ("B08_open_vitrine", "Экспонат: счётчик с пломбой"),
        ("B05_lay_films", "Три эпохи одной шахты"), ("B11_inspect_board", "Свежая краска на доске почёта"),
        ("B20_accuse_signature", "Подпись Изольды"), ("B02_inspect_drums", "Прачечная"),
        ("B03_merge_requests", "Разговор с Изольдой"), ("B15_descend", "Служебная лестница")],
    3: [("C01_read_order", "Инструкция 1908 года"), ("C02_trolley_stairs", "Тележка не проходит"),
        ("C03_photo_floor", "Лифт за зеркалом"), ("C06_inspect_cabin", "«Не трогать — элемент дизайна»"),
        ("C09_test_run", "Пробный пуск"), ("C12_watch_stamp", "Счёт под печать"),
        ("C14_load_payment", "Оплата"), ("C16_ride_as_staff", "Спуск грузом")],
    4: [("E03_report", "Доложиться"), ("E05_plunger_mark", "Две отметки в журнале"),
        ("E06_open_valve", "Пуск воды и эпилог")],
}


def walk(sim, st, want, order):
    """Жадный путь по нужным действиям с учётом ORDER; затем — к концу акта."""
    steps, done = [], set()
    while not st["end"]:
        rest = want - done
        blocked = {b for a, b in order if a not in done and a in want} if rest else set()
        if "*" in blocked:
            blocked = rest - {a for a, b in order if b == "*"}
        tgt = {"ACT:" + a for a in rest - blocked}
        path = PF.search(sim, st, lambda s2: not s2["end"] and any(x in tgt for x in s2["log"])) if tgt else None
        last = path is None
        if last:
            path = PF.search(sim, st, lambda s2: s2["end"])
            if path is None:
                raise SystemExit(f"акт {sim.d['act']}: конец недостижим")
        for label, st2 in path:
            steps.append((label, st2))
            done |= {x[4:] for x in st2["log"] if x.startswith("ACT:")}
            st = st2
        if last:
            break
    return steps, done


class Walk(PF.Plan):
    """Plan, который отмечает в журнале хода сработавшие действия графа («ACT:id»)."""

    def fire(self, st, rule, where):
        st2 = super().fire(st, rule, where)
        if rule.get("action"):
            st2["log"].append("ACT:" + rule["action"])
        return st2

    def run_chain(self, st, name):
        r = next((r for r in self.d["chains"].get(name, []) if L.evaluate(r["when"], st)), None)
        super().run_chain(st, name)
        if r and r.get("action") and "log" in st:
            st["log"].append("ACT:" + r["action"])


def plan_act(act, carry):
    data = G.build(act)
    sim = Walk(data)
    st = {"flags": set(data["start_flags"]), "pos": "room" if act == 1 else None, "n": {}, "c": {},
          "view": None, "menu": None, "end": False, "act": act, "log": [],
          "h": {"n": 0, "lock": False, "level": {}}}
    if carry:
        st["flags"] |= carry[0]
        st["n"] = dict(carry[1])
        st["c"] = dict(carry[2])
    if "open" in data["scenes"]:
        sim.run_scene(st, "open")
    if st["view"] is None:
        st["view"] = next(iter(data["views"]))
    start_slots = [x for x in st["log"] if not x.startswith("ACT:")]
    st0 = dict(st, log=[])
    graph = data["graph"]
    want = {a for a, g in graph.items() if not g.get("optional")} | (WANT.get(act, set()) & set(graph))
    steps, done = walk(sim, st0, want, ORDER.get(act, []))
    moves = [{"move": "начало акта", "slots": start_slots}]
    for label, st2 in steps:
        acts = [x[4:] for x in st2["log"] if x.startswith("ACT:")]
        m = {"move": label, "slots": [x for x in st2["log"] if not x.startswith("ACT:")]}
        if acts:
            m["action"] = acts
        moves.append(m)
    chap = dict(CHAPTERS.get(act, []))
    for m in moves:
        for a in m.get("action", []):
            if a in chap:
                m["chapter"] = chap.pop(a)
                break
    if chap:
        print(f"  главы без хода: {', '.join(chap.values())}")
    miss = sorted(want - done)
    print(f"акт {act}: ходов {len(steps)}, действий графа {len(done)} (нужных {len(want & done)} из {len(want)})"
          + (f"; не сделано: {', '.join(miss)}" if miss else ""), flush=True)
    end = steps[-1][1]
    return {"act": act, "moves": moves}, (set(end["flags"]), dict(end["n"]), dict(end["c"])), miss


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "work" / "walkthrough" / "plan.json"))
    ap.add_argument("--acts", default="1,2,3,4")
    a = ap.parse_args(argv)
    plan, carry, bad = [], None, False
    for act in map(int, a.acts.split(",")):
        p, carry, miss = plan_act(act, carry)
        plan.append(p)
        bad |= bool(miss)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"plan": plan}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"план → {out}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
