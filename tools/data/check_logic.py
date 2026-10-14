#!/usr/bin/env python3
"""Проверка логики актов (GATE1 для движка BJ3): играет файл логики перебором всех состояний.

  python tools/data/check_logic.py 1 [2 3 4] [--verbose]

Для каждого акта:
  1. ссылки: виды, слои, зоны, слоты, флаги, звуки, подписи — через сборку данных (gen_design);
  2. перебор состояний от стартовых флагов графа (как будет играть движок: зоны, глаголы, предметы,
     меню, сцены, цепочки; «назад» из зума);
  3. каждое действие графа срабатывает только при своих requires; объединение «+флагов» правил
     действия покрывает его adds, «−флаги» — ровно его removes;
  4. конец акта достижим, цели акта выполнены, тупиков нет (из каждого состояния конец достижим);
  5. каждый слот текстов акта где-то звучит (кроме советов и подписей — их проверяет движок).
Код выхода: 0 — всё чисто, 1 — ошибки (печатаются).
"""
import argparse
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_design as G  # noqa: E402
import logic as L  # noqa: E402

MAX_STATES = 2_000_000


class Sim:
    def __init__(self, data):
        self.d = data
        self.errors = []
        self.fired = {}          # действие графа → сколько раз
        self.played = set()      # прозвучавшие слоты
        self.req_fail = set()
        # пороги счётчиков показов, нужные условиям: n(SLOT) храним только для них
        self.watch = {}
        self.cnt_cap = {"probe": 3, "call": 2}

        def scan(tree):
            if tree is None:
                return
            if "shown" in tree:
                self.watch[tree["shown"]] = max(self.watch.get(tree["shown"], 0), 1)
            if "cmp" in tree and tree["cmp"].startswith("n:"):
                s = tree["cmp"][2:]
                self.watch[s] = max(self.watch.get(s, 0), tree["v"] + 1)
            for k in ("and", "or"):
                for e in tree.get(k, []):
                    scan(e)
            if "not" in tree:
                scan(tree["not"])

        def progress(r):
            """Правило влияет на прохождение: действие графа или флаги, тележка, вид, сцена, меню, акт."""
            return bool(r.get("action")) or any(k in e for e in r["effects"] for k in
                                               ("add", "remove", "pos", "view", "scene", "menu", "act", "chain"))

        for v in data["views"].values():
            for x in v["zones"]:
                scan(x["when"])
        for z in data["rules"].values():
            for rs in z.values():
                for r in rs:
                    if progress(r):
                        scan(r["when"])
        for g in data["chains"].values():
            for r in g:
                if progress(r):
                    scan(r["when"])
        for m in data["menus"].values():
            for it in m:
                for r in it["rules"]:
                    if progress(r):
                        scan(r["when"])
        self.key_flags, self.key_slots = self.significant(data)

    @staticmethod
    def significant(data):
        """Что различает состояния перебора: флаги и показы слотов, от которых зависит, куда игрок
        может прийти. Значимое правило меняет значимый флаг, тележку, вид, меню (не своё же), сцену,
        акт, значимый счётчик показов или зовёт значимую цепочку; значимы флаги и показы, которые
        читают условия значимых правил (вместе с условием зоны и предмета), требования действий
        графа, цели акта и экранные флаги. Неподвижная точка. Остальное — необязательные находки,
        которые ничего дальше не открывают (реликвии, витрина, журнал, памятка): состояния,
        различные лишь ими, ведут себя одинаково, и перебор их не множит (иначе Акт II — десятки
        миллионов состояний). Их реплики и действия проверяют те же ходы и случайные прохождения."""
        flags = set(data["goal_flags"]) | set(data.get("screen_scopes", {}))
        for g in data["graph"].values():
            flags |= set(g["requires"])
        entries = []   # (условия, слот, эффекты, меню-источник)
        for vid, v in data["views"].items():
            for z in v["zones"]:
                for verb, rs in data["rules"].get(f"{vid}.{z['id']}", {}).items():
                    extra = []
                    if verb.startswith("предмет:") and verb[8:] in data["items"]:
                        extra = [data["items"][verb[8:]]["when"]]
                    for r in rs:
                        entries.append(([z["when"], r["when"]] + extra, r["slot"], r["effects"], None))
        for g in data["chains"].values():
            for r in g:
                entries.append(([r["when"]], r["slot"], r["effects"], None))
        for name, m in data["menus"].items():
            for it in m:
                for r in it["rules"]:
                    entries.append(([r["when"]], r["slot"], r["effects"], name))
        counters = set()
        for conds, _, _, _ in entries:
            for t in conds:
                Sim._counters(t, counters)
        slots = set()

        def sig_chain(name, seen=()):
            return any(sig(r["slot"], r["effects"], None, seen + (name,)) for r in data["chains"].get(name, []))

        def sig(slot, effects, ctx, seen=()):
            if slot and slot.startswith("@") and slot[1:] not in seen and sig_chain(slot[1:], seen):
                return True
            if slot in slots:
                return True
            for e in effects:
                if ("add" in e and e["add"] in flags) or ("remove" in e and e["remove"] in flags):
                    return True
                if any(k in e for k in ("pos", "view", "scene", "act")):
                    return True
                if "menu" in e and e["menu"] != ctx:
                    return True
                if "inc" in e and e["inc"] in counters:
                    return True
                if "chain" in e and e["chain"] not in seen and sig_chain(e["chain"], seen):
                    return True
            return False

        changed = True
        while changed:
            changed = False
            for conds, slot, effects, ctx in entries:
                if not sig(slot, effects, ctx):
                    continue
                for t in conds:
                    nf = L.cond_flags(t) - flags
                    ns = L.cond_slots(t) - slots
                    if nf or ns:
                        flags |= nf
                        slots |= ns
                        changed = True
        return flags, slots

    @staticmethod
    def _counters(tree, acc):
        if tree is None:
            return
        if "cmp" in tree and not tree["cmp"].startswith("n:") and tree["cmp"] != "act":
            acc.add(tree["cmp"])
        for k in ("and", "or"):
            for e in tree.get(k, []):
                Sim._counters(e, acc)
        if "not" in tree:
            Sim._counters(tree["not"], acc)

    # ------------------------------------------------------------ состояние
    def start(self):
        st = {"flags": set(self.d["start_flags"]), "pos": "room" if self.d["act"] == 1 else None,
              "n": {}, "c": {}, "view": None, "menu": None, "end": False, "act": self.d["act"]}
        if "open" in self.d["scenes"]:
            self.run_scene(st, "open")
        if st["view"] is None:
            st["view"] = next(iter(self.d["views"]))
        return st

    def key(self, st):
        return (frozenset(st["flags"] & self.key_flags), st["pos"], st["view"], st["menu"], st["end"],
                tuple(sorted((k, v) for k, v in st["n"].items() if k in self.key_slots)))

    @staticmethod
    def copy(st):
        return {**st, "flags": set(st["flags"]), "n": dict(st["n"]), "c": dict(st["c"])}

    # ------------------------------------------------------------ исполнение
    def play(self, st, slot):
        if slot is None:
            return
        if slot.startswith("@"):
            self.run_chain(st, slot[1:])
            return
        self.played.add(slot)
        st["n"][slot] = min(st["n"].get(slot, 0) + 1, max(self.watch.get(slot, 0), 3))

    def run_chain(self, st, name):
        for r in self.d["chains"].get(name, []):
            if L.evaluate(r["when"], st):
                a = r.get("action")
                if a:
                    miss = set(self.d["graph"][a]["requires"]) - st["flags"]
                    if miss and (a, name) not in self.req_fail:
                        self.req_fail.add((a, name))
                        self.errors.append(f"цепочка {name}: действие {a} срабатывает без {sorted(miss)}")
                    self.fired[a] = self.fired.get(a, 0) + 1
                self.play(st, r["slot"])
                self.apply(st, r["effects"])
                return
        self.errors.append(f"цепочка {name}: ни одно условие не истинно в состоянии {sorted(st['flags'])}")

    def run_scene(self, st, name):
        steps = self.d["scenes"].get(name)
        if not steps:
            self.errors.append(f"сцены {name} нет")
            return
        for step in steps:
            self.play(st, step["slot"])
            self.apply(st, step["effects"])

    def apply(self, st, effects):
        later = []
        for e in effects:
            if "add" in e:
                st["flags"].add(e["add"])
            elif "remove" in e:
                st["flags"].discard(e["remove"])
            elif "pos" in e:
                st["pos"] = e["pos"]
            elif "inc" in e:
                k = e["inc"]
                st["c"][k] = min(st["c"].get(k, 0) + 1, self.cnt_cap.get(k, 3))
            elif "doc" in e:
                self.played.add(e["doc"])
                cap = self.d["docs"].get(e["doc"], {}).get("caption")
                if cap and L.evaluate(cap["when"], st):
                    self.played.add(cap["slot"])
            else:
                later.append(e)
        for e in later:
            if "view" in e:
                if e["view"] != st["view"]:
                    L.drop_screen(st["flags"], e["view"], self.d.get("screen_scopes"))
                st["view"] = e["view"]
                st["menu"] = None
            elif "scene" in e:
                self.run_scene(st, e["scene"])
            elif "menu" in e:
                st["menu"] = e["menu"]
            elif "chain" in e:
                self.run_chain(st, e["chain"])
            elif "act" in e:
                st["end"] = True

    def fire(self, st, rule, where):
        a = rule.get("action")
        if a:
            req = set(self.d["graph"][a]["requires"])
            miss = req - st["flags"]
            if miss and (a, where) not in self.req_fail:
                self.req_fail.add((a, where))
                self.errors.append(f"{where}: действие {a} срабатывает без {sorted(miss)}")
            self.fired[a] = self.fired.get(a, 0) + 1
        st2 = self.copy(st)
        if st2["menu"] and not any(("menu" in e) for e in rule["effects"]):
            st2["menu"] = None   # пункт меню выполнен — меню закрывается, если правило не открыло его снова
        self.play(st2, rule["slot"])
        self.apply(st2, rule["effects"])
        return st2

    @staticmethod
    def first(rules, st):
        for r in rules:
            if L.evaluate(r["when"], st):
                return r
        return None

    def moves(self, st):
        """Все ходы игрока из состояния: [(подпись, новое состояние)]."""
        out = []
        if st["end"]:
            return out
        if st["menu"]:
            for it in self.d["menus"][st["menu"]]:
                r = self.first(it["rules"], st)
                if r:
                    out.append((f"меню {st['menu']}.{it['id']}", self.fire(st, r, f"меню {st['menu']}.{it['id']}")))
            if st["menu"] != "talk":   # разговор не закрыть, пока не закончен; меню у толпы — можно
                st2 = self.copy(st)
                st2["menu"] = None
                out.append(("закрыть меню", st2))
            return out
        view = self.d["views"][st["view"]]
        held = [i for i, it in self.d["items"].items() if L.evaluate(it["when"], st)]
        for z in view["zones"]:
            if not L.evaluate(z["when"], st):
                continue
            zk = f"{st['view']}.{z['id']}"
            for verb, rules in self.d["rules"].get(zk, {}).items():
                if verb.startswith("предмет:"):
                    continue
                r = self.first(rules, st)
                if r:
                    out.append((f"{zk} {verb}", self.fire(st, r, f"{zk} {verb}")))
            for item in held:
                rules = self.d["rules"].get(zk, {}).get(f"предмет:{item}")
                r = self.first(rules, st) if rules else None
                if r:
                    out.append((f"{zk} ← {item}", self.fire(st, r, f"{zk} ← {item}")))
                else:
                    it = self.d["items"][item]
                    miss = it["miss_flat"] if "плоское" in z["props"] else it["miss"]
                    st2 = self.copy(st)
                    self.play(st2, miss)
                    out.append((f"{zk} ← {item} (мимо)", st2))
        for item in held:
            it = self.d["items"][item]
            st2 = self.copy(st)
            self.play(st2, it["look"])
            self.apply(st2, it["look_effects"])
            out.append((f"осмотр {item}", st2))
            for other in held:
                if other != item and "fb_generic" in self.d["chains"]:
                    st3 = self.copy(st)
                    self.run_chain(st3, "fb_generic")
                    out.append((f"{item} + {other}", st3))
        if view["parent"]:
            st2 = self.copy(st)
            st2["view"] = view["parent"]
            L.drop_screen(st2["flags"], view["parent"], self.d.get("screen_scopes"))
            out.append(("назад", st2))
        return out


def check(act, verbose=False):
    try:
        data = G.build(act)
    except G.DesignError as e:
        return e.errors, {}
    return check_data(data, verbose, seed=act)


def check_data(data, verbose=False, seed=0, walks=3000):
    """Проверка собранных данных акта (её же зовут негативные тесты на испорченных данных)."""
    act = seed
    sim = Sim(data)
    st0 = sim.start()
    seen = {sim.key(st0): 0}
    states = [st0]
    edges = [[]]
    q = deque([0])
    while q:
        i = q.popleft()
        for label, st2 in sim.moves(states[i]):
            k = sim.key(st2)
            j = seen.get(k)
            if j is None:
                j = len(states)
                seen[k] = j
                states.append(st2)
                edges.append([])
                q.append(j)
                if len(states) > MAX_STATES:
                    sim.errors.append(f"состояний больше {MAX_STATES} — перебор остановлен")
                    q.clear()
                    break
            edges[i].append(j)
    # случайные прохождения: все счётчики показов живые — ловят варианты «повтор» и «ещё раз»
    import random
    rnd = random.Random(act)
    for _ in range(walks):
        st = sim.start()
        for _ in range(300):
            mv = sim.moves(st)
            if not mv:
                break
            st = rnd.choice(mv)[1]
    ends = [i for i, s in enumerate(states) if s["end"]]
    errors = list(sim.errors)
    if not ends:
        errors.append("конец акта недостижим")
    goal = set(data["goal_flags"])
    for i in ends:
        miss = goal - states[i]["flags"]
        if miss:
            errors.append(f"конец акта без целей {sorted(miss)}")
            break
    # тупики: обратная достижимость от концов
    rev = [[] for _ in states]
    for i, es in enumerate(edges):
        for j in es:
            rev[j].append(i)
    good = set(ends)
    q = deque(ends)
    while q:
        j = q.popleft()
        for i in rev[j]:
            if i not in good:
                good.add(i)
                q.append(i)
    dead = [i for i in range(len(states)) if i not in good]
    if dead:
        s = states[dead[0]]
        errors.append(f"тупиков {len(dead)}; пример: вид {s['view']}, меню {s['menu']}, pos {s['pos']}, "
                      f"флаги {sorted(s['flags'])}")
    # соответствие графу
    for a, g in data["graph"].items():
        adds, rems = set(), set()
        for zk in data["rules"].values():
            for rs in zk.values():
                for r in rs:
                    if r.get("action") == a:
                        adds |= {e["add"] for e in r["effects"] if "add" in e}
                        rems |= {e["remove"] for e in r["effects"] if "remove" in e}
                        for e in r["effects"]:
                            if "scene" in e:
                                for stp in data["scenes"].get(e["scene"], []):
                                    adds |= {x["add"] for x in stp["effects"] if "add" in x}
                            if "chain" in e:
                                for c in data["chains"].get(e["chain"], []):
                                    adds |= {x["add"] for x in c["effects"] if "add" in x}
        for m in data["menus"].values():
            for it in m:
                for r in it["rules"]:
                    if r.get("action") == a:
                        adds |= {e["add"] for e in r["effects"] if "add" in e}
                        for e in r["effects"]:
                            if "scene" in e:
                                for stp in data["scenes"].get(e["scene"], []):
                                    adds |= {x["add"] for x in stp["effects"] if "add" in x}
                            if "chain" in e:
                                for c in data["chains"].get(e["chain"], []):
                                    adds |= {x["add"] for x in c["effects"] if "add" in x}
        for c in data["chains"].values():
            for r in c:
                if r.get("action") == a:
                    adds |= {e["add"] for e in r["effects"] if "add" in e}
        if a not in sim.fired:
            errors.append(f"действие графа {a} ни разу не срабатывает")
            continue
        miss = set(g["adds"]) - adds
        if miss:
            errors.append(f"действие {a}: правила не ставят {sorted(miss)} из adds графа")
        if rems != set(g["removes"]):
            errors.append(f"действие {a}: правила снимают {sorted(rems)}, граф — {sorted(g['removes'])}")
    # покрытие слотов
    hint_slots = {f"HINT.{h['topic']}.{k}" for h in data["hints"] for k in (1, 2, 3)} | {"HINT.intro", "HINT.cooldown", "HINT.done"}
    skip = hint_slots | set(data["other"]) | set(data.get("borrowed", ()))
    silent = sorted(s for s in data["texts"] if s not in sim.played and s not in skip)
    if silent:
        errors.append(f"слоты, которые нигде не звучат ({len(silent)}): {', '.join(silent)}")
    stats = {"состояний": len(states), "концов": len(ends), "слотов прозвучало": len(sim.played),
             "действий графа сработало": len(sim.fired)}
    if verbose:
        never = sorted(set(data["graph"]) - set(sim.fired))
        stats["не сработали"] = never
    return errors, stats


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("acts", nargs="+", type=int)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    bad = 0
    for act in a.acts:
        errors, stats = check(act, a.verbose)
        print(f"Акт {act}: " + ", ".join(f"{k} {v}" for k, v in stats.items()))
        for e in errors:
            print("  ОШИБКА " + e)
        bad += len(errors)
    print("ЛОГИКА ЧИСТА" if not bad else f"ИТОГ: ошибок {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
