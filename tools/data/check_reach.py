#!/usr/bin/env python3
"""Достижимость советов Предка и реплик: полный перебор состояний акта.

  python tools/data/check_reach.py [1 2 3 4] [--slot СЛОТ ...]

Перебор — модель check_logic.py (класс Sim), но в ключ состояния добавлены флаги и показы, которые
читают условия советов и предметов: check_logic их не различает (необязательные находки склеиваются),
и без них перебор ошибочно объявляет недостижимым, например, «жетон на краску» (Z09.paint.token).
Для каждого акта печатает:
  * темы советов: сколько состояний (без открытого меню), где тема — первая подходящая; тема с нулём
    не прозвучит никогда; «done» — состояния, где не подходит ни одна (тогда звучит HINT.done);
  * слоты текстов акта, которые не звучат ни в одном ходе (советы и интерфейс — не в счёт). Список
    грубый: повторы («.again», «.repeat», «.2») перебор с усечёнными счётчиками может не дойти, а
    варианты от наследства прошлого акта со стартовых флагов не видны — такие слоты проверены
    видеопрохождением (work/fullrun/…/record_log.json: что реально прозвучало);
  * --slot: достижим ли каждый названный слот.
Старт акта — его стартовые флаги (наследство прошлых актов не учитывается: варианты, зависящие от
прошлого акта, проверяются правкой стартовых флагов или в видеопрохождении tools/web/plan_full.py).
Пишет отчёт; код выхода 0 всегда — это справка, не гейт.
"""
import argparse
import sys
import time
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_logic as CL  # noqa: E402
import gen_design as G  # noqa: E402
import logic as L  # noqa: E402

LIMIT = 5_000_000


def reach(act, slots=()):
    d = G.build(act)
    sim = CL.Sim(d)
    for h in d["hints"]:
        sim.key_flags |= L.cond_flags(h["when"])
        sim.key_slots |= L.cond_slots(h["when"])
    for it in d["items"].values():
        sim.key_flags |= L.cond_flags(it["when"])
    st = sim.start()
    seen = {sim.key(st)}
    q = deque([st])
    topics = {h["topic"]: 0 for h in d["hints"]}
    topics["done"] = 0
    t0 = time.time()
    while q:
        s = q.popleft()
        if not s["menu"]:
            t = next((h["topic"] for h in d["hints"] if L.evaluate(h["when"], s)), "done")
            topics[t] += 1
        for _, s2 in sim.moves(s):
            if s2["end"]:
                continue
            k = sim.key(s2)
            if k not in seen:
                seen.add(k)
                q.append(s2)
                if len(seen) > LIMIT:
                    print(f"акт {act}: больше {LIMIT} состояний — перебор остановлен, итог неполный")
                    q.clear()
                    break
    skip = {f"HINT.{h['topic']}.{k}" for h in d["hints"] for k in (1, 2, 3)} | set(d["other"]) | set(d.get("borrowed", ()))
    silent = sorted(s for s in d["texts"] if s not in sim.played and s not in skip)
    print(f"акт {act}: состояний {len(seen)}, {time.time() - t0:.0f} с")
    print("  темы советов (первая подходящая, состояний): " + ", ".join(f"{k} {v}" for k, v in topics.items()))
    dead = [k for k, v in topics.items() if v == 0]
    if dead:
        print(f"  не прозвучат никогда: {', '.join(dead)}")
    if silent:
        print(f"  слоты, которые не звучат ни в одном ходе: {', '.join(silent)}")
    for s in slots:
        if s in d["texts"]:
            print(f"  {s}: {'достижим' if s in sim.played else 'НЕ достижим'}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("acts", nargs="*", type=int, default=[1, 2, 3, 4])
    ap.add_argument("--slot", nargs="*", default=[])
    a = ap.parse_args(argv)
    for act in a.acts:
        reach(act, a.slot)


if __name__ == "__main__":
    main()
