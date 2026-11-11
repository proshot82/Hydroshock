#!/usr/bin/env python3
"""Достижимость советов Предка и реплик: полный перебор состояний акта.

  python tools/data/check_reach.py [1 2 3 4] [--slot СЛОТ ...]

Перебор — модель check_logic.py (класс Sim), но в ключ состояния добавлены флаги и показы, которые
читают условия советов и предметов: check_logic их не различает (необязательные находки склеиваются),
и без них перебор ошибочно объявляет недостижимым, например, «жетон на краску» (Z09.paint.token).
Для каждого акта печатает:
  * темы советов: сколько состояний (без открытого меню), где тема — первая подходящая; тема с нулём
    не прозвучит никогда; «done» — состояния, где не подходит ни одна (тогда звучит HINT.done).
    HINT.done — страховка (решение автора 02.11.2026): при нынешней логике последняя тема каждого акта
    держится до хода, который кончает акт, и ноль у «done» ожидаем — в «не прозвучат никогда» он не идёт;
    не ноль значит, что в акте есть состояния без открытой темы;
  * слоты текстов акта, которые не звучат ни в одном ходе (советы и интерфейс — не в счёт). Слот,
    не прозвучавший в основном переборе, проверяется ещё двумя способами, и только после них
    считается немым:
      – необязательная находка: в ключ состояния добавляются флаги, показы и счётчики из условий, которые
        стоят на пути к слоту (правило, его соседи по списку, зона, предмет, подпись бумаги и всё,
        что зовёт его цепочку или сцену), и перебор повторяется — так находится пункт разговора,
        открытый необязательным осмотром (TALK.kuh.photo после семейной фотографии), и повторы
        («.again», «.repeat», «.2»), до которых основной перебор не доходит;
      – наследство прошлых актов: флаг из тех же условий, который в этом акте никто не ставит и
        которого нет на старте, но ставит один из прошлых актов, добавляется к стартовым, и перебор
        повторяется — так находится вариант начала Акта IV, если оплату в Акте III отправили одну
        (SEQ.rollout.empty, SEQ.goods.prior). Что такой флаг совместим со всем остальным
        наследством, перебор не доказывает: он показывает, что условие слота выполнимо.
    Такие слоты печатаются отдельно, с тем, что их открыло;
  * --slot: достижим ли каждый названный слот и, если только в варианте, — в каком.
Поиск в варианте идёт по одному слоту и кончается на находке; если он упирается в потолок
состояний, слот печатается как «не проверено до конца» — это не «немой».
Пишет отчёт; код выхода 0 — это справка. С --strict код выхода 1, если есть тема совета, которая
не прозвучит никогда, слот, немой после всех трёх проверок, или слот, не проверенный до конца.
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
VARIANT_LIMIT = 3_000_000   # потолок поиска одного слота в варианте


class Sim(CL.Sim):
    """Исполнитель check_logic, который умеет различать в ключе состояния ещё и счётчики
    (probe.n и подобные): условие «вторая повторная проба» читает счётчик, а не флаг."""

    def __init__(self, data):
        super().__init__(data)
        self.key_counters = set()

    def key(self, st):
        base = super().key(st)
        if not self.key_counters:
            return base
        return base + (tuple(sorted((k, v) for k, v in st["c"].items() if k in self.key_counters)),)


def _walk(x, key, acc):
    """Все строковые значения ключа key в дереве данных (эффекты лежат на разной глубине)."""
    if isinstance(x, dict):
        if isinstance(x.get(key), str):
            acc.add(x[key])
        for v in x.values():
            _walk(v, key, acc)
    elif isinstance(x, list):
        for v in x:
            _walk(v, key, acc)
    return acc


def settable(d):
    """Флаги, которые акт умеет поставить сам: эффекты правил, цепочек, меню, сцен, предметов и граф."""
    acc = _walk({k: d[k] for k in ("rules", "chains", "menus", "scenes", "items")}, "add", set())
    for g in d["graph"].values():
        acc |= set(g["adds"])
    return acc


def guards(d, slot):
    """Условия на пути к слоту: (флаги, показы, счётчики). Собираются вверх по зовущим: правило со слотом и
    его соседи по списку (первое подходящее перекрывает следующие), условие зоны и предмета, подпись
    бумаги, а для слота из цепочки, сцены или меню — ещё и всё, что их зовёт или открывает."""
    groups = []   # (общие условия, [правила], имя цепочки или None, имя меню или None)
    for vid, v in d["views"].items():
        for z in v["zones"]:
            for verb, rs in d["rules"].get(f"{vid}.{z['id']}", {}).items():
                common = [z["when"]]
                if verb.startswith("предмет:") and verb[8:] in d["items"]:
                    common.append(d["items"][verb[8:]]["when"])
                groups.append((common, rs, None, None))
    for name, rs in d["chains"].items():
        groups.append(([], rs, name, None))
    for name, m in d["menus"].items():
        for it in m:
            groups.append(([], it["rules"], None, name))
    for it in d["items"].values():
        groups.append(([it["when"]], [{"when": None, "slot": it["look"], "effects": it["look_effects"]}], None, None))
        for miss in {it["miss"], it["miss_flat"]}:
            groups.append(([it["when"]], [{"when": None, "slot": miss, "effects": []}], None, None))

    flags, shows, counters = set(), set(), set()
    want = {"slots": {slot}, "chains": set(), "scenes": set(), "docs": set(), "menus": set()}
    for name, doc in d["docs"].items():
        cap = doc.get("caption")
        if cap and cap["slot"] == slot:
            want["docs"].add(name)
            flags.update(L.cond_flags(cap["when"]))
            shows.update(L.cond_slots(cap["when"]))
    changed = True
    while changed:
        changed = False
        for name, steps in d["scenes"].items():
            if name not in want["scenes"] and any(_hits(st, want) for st in steps):
                want["scenes"].add(name)
                changed = True
        for common, rs, chain, menu in groups:
            if not any(_hits(r, want) for r in rs):
                continue
            for t in common + [r["when"] for r in rs]:
                cnt = set()
                CL.Sim._counters(t, cnt)
                nf, ns, nc = L.cond_flags(t) - flags, L.cond_slots(t) - shows, cnt - counters
                if nf or ns or nc:
                    flags |= nf
                    shows |= ns
                    counters |= nc
                    changed = True
            for kind, name in (("chains", chain), ("menus", menu)):
                if name and name not in want[kind]:
                    want[kind].add(name)
                    changed = True
    return flags, shows, counters


def _hits(rule, want):
    """Ведёт ли правило (или шаг сцены) к искомому: само играет слот или зовёт то, что к нему ведёт."""
    s = rule.get("slot")
    if s in want["slots"] or (s and s.startswith("@") and s[1:] in want["chains"]):
        return True
    return any(e.get("chain") in want["chains"] or e.get("scene") in want["scenes"]
               or e.get("doc") in want["docs"] or e.get("menu") in want["menus"]
               for e in rule.get("effects", []))


def explore(d, key_flags=(), key_slots=(), start=(), topics=None, stop=None, limit=LIMIT, key_counters=()):
    """Перебор акта. key_flags/key_slots — что ещё различать в ключе состояния, start — добавка к
    стартовым флагам, key_counters — счётчики в ключе, stop — слот, на котором перебор можно кончать (он найден), limit — потолок
    состояний. Возвращает (исполнитель, число состояний, состояний без открытой темы, полон ли)."""
    sim = Sim(d)
    sim.key_counters = set(key_counters)
    for h in d["hints"]:
        sim.key_flags |= L.cond_flags(h["when"])
        sim.key_slots |= L.cond_slots(h["when"])
    for it in d["items"].values():
        sim.key_flags |= L.cond_flags(it["when"])
    sim.key_flags |= set(key_flags)
    sim.key_slots |= set(key_slots)
    st = sim.start(start)
    seen = {sim.key(st)}
    q = deque([st])
    done, full = 0, True
    while q:
        s = q.popleft()
        if topics is not None and not s["menu"]:
            t = next((h["topic"] for h in d["hints"] if L.evaluate(h["when"], s)), None)
            if t is None:
                done += 1
            else:
                topics[t] += 1
        for _, s2 in sim.moves(s):
            if s2["end"]:
                continue
            k = sim.key(s2)
            if k not in seen:
                seen.add(k)
                q.append(s2)
                if len(seen) > limit:
                    full = False
                    q.clear()
                    break
        if stop is not None and stop in sim.played:
            break
    return sim, len(seen), done, full


def analyze(act, data=None):
    """Итог по акту словарём: темы советов, немые слоты и слоты, найденные только в варианте.
    data — готовые данные акта вместо собранных (для тестов на испорченном входе)."""
    d = data if data is not None else G.build(act)
    t0 = time.time()
    topics = {h["topic"]: 0 for h in d["hints"]}
    sim, states, done, full = explore(d, topics=topics)
    skip = {f"HINT.{h['topic']}.{k}" for h in d["hints"] for k in (1, 2, 3)} | set(d["other"]) | set(d.get("borrowed", ()))
    silent = sorted(s for s in d["texts"] if s not in sim.played and s not in skip)
    found = {}    # слот -> чем открыт
    unsure = []   # слоты, чей поиск упёрся в потолок состояний: ни «звучит», ни «немой»
    partial = not full
    own = settable(d) | set(d["start_flags"])
    earlier = {}
    for k in range(1, act):
        for f in settable(G.build(k)):
            earlier.setdefault(f, k)
    # По одному слоту: общий ключ со всеми условиями сразу раздувает перебор (Акт I — миллионы
    # состояний), а условия одного слота добавляют к ключу немного, и поиск кончается на находке.
    for s in silent:
        gf, gs, kc = guards(d, s)
        kf, ks = gf - sim.key_flags, gs - sim.key_slots
        capped = False
        # 1) необязательная находка: различить флаги, показы и счётчики на пути к слоту
        if kf or ks or kc:
            sim2, _, _, full2 = explore(d, kf, ks, stop=s, limit=VARIANT_LIMIT, key_counters=kc)
            if s in sim2.played:
                found[s] = "необязательная находка: " + ", ".join(sorted(kf | ks | kc))
                continue
            capped |= not full2
        # 2) наследство: флаг, который ставит только прошлый акт
        for f in sorted(f for f in gf - own if f in earlier):
            sim3, _, _, full3 = explore(d, kf, ks, start=[f], stop=s, limit=VARIANT_LIMIT, key_counters=kc)
            if s in sim3.played:
                found[s] = f"наследство Акта {G.ROMAN[earlier[f]]}: {f}"
                break
            capped |= not full3
        if s not in found and capped:
            unsure.append(s)
    return {"act": act, "data": d, "played": sim.played, "states": states, "seconds": time.time() - t0,
            "topics": topics, "dead": [k for k, v in topics.items() if v == 0], "done": done,
            "silent": [s for s in silent if s not in found and s not in unsure], "found": found,
            "unsure": unsure, "partial": partial}


def reach(act, slots=()):
    """Печатает отчёт по акту; возвращает True, если нет ни мёртвых тем, ни немых слотов."""
    r = analyze(act)
    d = r["data"]
    print(f"акт {act}: состояний {r['states']}, {r['seconds']:.0f} с")
    if r["partial"]:
        print(f"  больше {LIMIT} состояний — перебор остановлен, итог неполный")
    print("  темы советов (первая подходящая, состояний): " + ", ".join(f"{k} {v}" for k, v in r["topics"].items()))
    if r["dead"]:
        print(f"  не прозвучат никогда: {', '.join(r['dead'])}")
    print("  HINT.done (страховка): " + ("ни одного состояния без открытой темы" if r["done"] == 0
                                        else f"состояний без открытой темы {r['done']} — там звучит «Тут всё»"))
    if r["found"]:
        print("  слоты, которые звучат только в варианте (основной перебор их не видит):")
        for s, why in sorted(r["found"].items()):
            print(f"    {s} — {why}")
    if r["unsure"]:
        print(f"  не проверено до конца (поиск упёрся в {VARIANT_LIMIT} состояний): {', '.join(r['unsure'])}")
    if r["silent"]:
        print(f"  слоты, которые не звучат ни в одном ходе: {', '.join(r['silent'])}")
    for s in slots:
        if s in d["texts"]:
            how = "достижим" if s in r["played"] else f"достижим — {r['found'][s]}" if s in r["found"] else "НЕ достижим"
            print(f"  {s}: {how}")
    return not r["dead"] and not r["silent"] and not r["unsure"] and not r["partial"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("acts", nargs="*", type=int, default=[1, 2, 3, 4])
    ap.add_argument("--slot", nargs="*", default=[])
    ap.add_argument("--strict", action="store_true", help="код выхода 1 при мёртвой теме или немом слоте")
    a = ap.parse_args(argv)
    ok = [reach(act, a.slot) for act in a.acts]
    return 0 if all(ok) or not a.strict else 1


if __name__ == "__main__":
    sys.exit(main())
