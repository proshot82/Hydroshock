#!/usr/bin/env python3
"""План полного (100 %) прохождения для видеозаписи: все реплики, бумаги и советы Предка.

  python tools/web/plan_full.py [--out work/fullrun/plan.json] [--acts 1,2,3,4]

Играет логику актов той же моделью, что check_logic.py (класс Sim), плюс советы Предка так, как
их выдаёт движок (game.js: hint): знакомство, блок «подожди» до нового слота или смены флагов,
первая подходящая тема, по три уровня.

1. Основной путь — жадно: ближайший ход, где звучит ещё не показанный слот; ходы, двигающие
   прохождение (флаги графа), дороже простых, ходы, меняющие значимое состояние, — дороже
   осмотров: сначала исчерпать всё доступное на месте, потом шаг вперёд. Нового нет — к концу акта.
2. Советы — вставкой по пути: где тема ещё не выслушана до конца и блок снят, — нажать «Совет».
3. Ответвления: то, что основной путь потерял (исключающие порядки: «некуда звонить» до чтения
   путёвки; совет по теме, окно которой основной путь проскочил), — с точки основного пути, где
   оно ещё достижимо; в записи — снимок сохранения, ответвление, загрузка, дальше по основному.
Акты подряд, как в игре: флаги и показы копятся, советы — заново.

Пишет план: [{act, moves:[{move, slots} | {branch:[…]}]}] и отчёт о непокрытых слотах.
"""
import argparse
import heapq
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "data"))
import check_logic as CL  # noqa: E402
import gen_design as G  # noqa: E402
import logic as L  # noqa: E402

PROGRESS_COST = 1000
MAX_NODES = 300_000
BRANCH_NODES = 600_000


class Plan(CL.Sim):
    def __init__(self, data):
        super().__init__(data)
        self.prog_flags = set()
        for g in data["graph"].values():
            self.prog_flags |= set(g["adds"]) | set(g["removes"])

    @staticmethod
    def copy(st):
        st2 = CL.Sim.copy(st)
        st2["log"] = []
        st2["h"] = dict(st["h"], level=dict(st["h"]["level"]))
        return st2

    def play(self, st, slot):
        if slot and not slot.startswith("@"):
            first = not st["n"].get(slot)
            st["log"].append(slot)
            if first and not slot.startswith("HINT."):
                st["h"]["lock"] = False
        super().play(st, slot)

    def apply(self, st, effects):
        for e in effects:
            if "doc" in e:
                st["log"].append(e["doc"])
                cap = self.d["docs"].get(e["doc"], {}).get("caption")
                if cap and L.evaluate(cap["when"], st):
                    st["log"].append(cap["slot"])
        before = frozenset(st["flags"])
        super().apply(st, effects)
        if frozenset(st["flags"]) != before:
            st["h"]["lock"] = False

    def topic(self, st):
        t = next((t for t in self.d["hints"] if L.evaluate(t["when"], st)), None)
        return t["topic"] if t else None

    def hint_slot(self, st):
        """Какой слот даст «Совет» сейчас (не меняя состояния)."""
        h = st["h"]
        if not h["n"]:
            return "HINT.intro"
        if h["lock"]:
            return "HINT.cooldown"
        t = self.topic(st)
        if not t:
            return "HINT.done"
        return f"HINT.{t}.{min(3, h['level'].get(t, 0) + 1)}"

    def hint(self, st):
        st2 = self.copy(st)
        h = st2["h"]
        slot = self.hint_slot(st2)
        if slot == "HINT.intro":
            h["n"] = 1
        elif slot not in ("HINT.cooldown", "HINT.done"):
            t = slot.split(".")[1]
            h["level"][t] = int(slot.split(".")[2])
            h["n"] += 1
        self.play(st2, slot)
        if slot not in ("HINT.intro", "HINT.cooldown", "HINT.done"):
            h["lock"] = True
        return st2

    def moves2(self, st, hints=False):
        st = dict(st, log=[])
        out = list(self.moves(st))
        if hints and not st["menu"]:
            out.append(("совет", self.hint(st)))
        return out

    def key2(self, st):
        return (self.key(st), st["h"]["n"] > 0)

    def step(self, st, label):
        """Повторить ход по подписи (для пересчёта пути со вставленными советами)."""
        if label == "совет":
            return self.hint(dict(st, log=[]))
        for lab, st2 in self.moves(dict(st, log=[])):
            if lab == label:
                return st2
        raise KeyError(f"хода «{label}» нет в состоянии вид {st['view']}, меню {st['menu']}")


def cost_of(sim, a, b):
    """Цена хода: двигает прохождение (флаги графа) — 1000; меняет значимое состояние (флаги, показы,
    от которых зависят другие реплики) — 10: такие ходы откладываются, пока на месте есть что
    посмотреть, иначе пропадут ранние реплики («некуда звонить» до чтения путёвки); остальное — 1."""
    if (a["flags"] ^ b["flags"]) & sim.prog_flags:
        return PROGRESS_COST
    ka, kb = sim.key(a), sim.key(b)
    if (ka[0], ka[1], ka[4], ka[5]) != (kb[0], kb[1], kb[4], kb[5]) or a["c"] != b["c"]:
        return 10
    return 1


def search(sim, st0, goal, cap=MAX_NODES, flat=False, hints=False):
    """Дейкстра до первого хода, после которого goal(состояние после хода) истинно; конец акта —
    цель, только если её признаёт goal. Путь [(подпись, состояние)] или None."""
    pq = [(0, 0, False, st0, [])]
    seen = {sim.key2(st0): 0}
    cnt = 0
    nodes = 0   # предел — по числу разных состояний, а не сгенерированных ходов
    while pq:
        c, _, done, st, path = heapq.heappop(pq)
        if done:
            return path
        for label, st2 in sim.moves2(st, hints):
            p2 = path + [(label, st2)]
            c2 = c + (1 if flat else cost_of(sim, st, st2))
            cnt += 1
            if goal(st2):
                heapq.heappush(pq, (c2, cnt, True, st2, p2))
                continue
            if st2["end"]:
                continue
            k = sim.key2(st2)
            if seen.get(k, 1e18) <= c2:
                continue
            seen[k] = c2
            nodes += 1
            if nodes > cap:
                return None
            heapq.heappush(pq, (c2, cnt, False, st2, p2))
    return None


def greedy(sim, st, want, finish, cap=MAX_NODES, flat=False):
    """Ближайший новый слот, пока такие есть; finish — затем путь к концу акта. [(подпись, состояние)]."""
    steps, covered = [], set()
    while True:
        rest = want - covered
        path = search(sim, st, lambda s2: not s2["end"] and any(x in rest for x in s2["log"]), cap=cap, flat=flat) if rest else None
        last = False
        if path is None:
            if not finish:
                break
            path = search(sim, st, lambda s2: s2["end"])
            if path is None:
                raise SystemExit(f"акт {sim.d['act']}: конец недостижим из {sorted(st['flags'])}")
            last = True
        for label, st2 in path:
            steps.append((label, st2))
            covered |= set(st2["log"])
            st = st2
        if last:
            break
    return steps, covered


def with_hints(sim, st, steps, want, covered):
    """Пройти путь заново, нажимая «Совет», где он даст ещё не показанный слот."""
    out = []
    covered = set(covered)
    for label, _ in steps:
        while not st["menu"] and not st["end"]:
            slot = sim.hint_slot(st)
            if slot in want and slot not in covered:
                st = sim.hint(st)
                out.append(("совет", st))
                covered |= set(st["log"])
            else:
                break
        st = sim.step(st, label)
        out.append((label, st))
        covered |= set(st["log"])
    return out, covered


def hint_branch(sim, s0, miss, cap):
    """Ответвление за советами: дойти до состояния, где «Совет» даст непоказанный слот, нажать;
    повторять, пока выходит. [(подпись, состояние)], показанное."""
    steps, got, st = [], set(), s0
    while True:
        rest = miss - got
        hs = {x for x in rest if x.startswith("HINT.")}
        if not hs:
            break
        if sim.hint_slot(st) in hs and not st["menu"]:
            path = []
        else:
            path = search(sim, st, lambda s2: not s2["end"] and not s2["menu"] and sim.hint_slot(s2) in hs,
                          cap=cap, flat=True)
            if path is None:
                break
        for label, st2 in path:
            steps.append((label, st2))
            got |= set(st2["log"])
            st = st2
        st = sim.hint(st)
        steps.append(("совет", st))
        got |= set(st["log"])
    return steps, got


def wanted(data):
    s = set(data["texts"]) | set(data["docs"])
    s |= {d["caption"]["slot"] for d in data["docs"].values() if d.get("caption")}
    s |= {"HINT.intro", "HINT.cooldown", "HINT.done"}
    s -= {k for k in data["other"] if not k.startswith("HINT.")}
    return s


def as_moves(steps):
    return [{"move": label, "slots": list(st2["log"])} for label, st2 in steps]


def plan_act(act, carry, shown_all):
    data = G.build(act)
    sim = Plan(data)
    st = {"flags": set(data["start_flags"]), "pos": "room" if act == 1 else None, "n": {}, "c": {},
          "view": None, "menu": None, "end": False, "act": act, "log": [],
          "h": {"n": 0, "lock": False, "level": {}}}
    if carry:
        st["flags"] |= carry[0]
        st["n"] = dict(carry[1])
        st["c"] = dict(carry[2])
        st["h"]["n"] = carry[3]
    if "open" in data["scenes"]:
        sim.run_scene(st, "open")
    if st["view"] is None:
        st["view"] = next(iter(data["views"]))
    want = wanted(data) - shown_all
    start_slots = list(st["log"])
    st0 = dict(st, log=[])
    steps, covered = greedy(sim, st0, {x for x in want if not x.startswith("HINT.")}, finish=True)
    steps, covered = with_hints(sim, st0, steps, want, covered | set(start_slots))
    states = [st0] + [s2 for _, s2 in steps]
    branches = {}
    # точки ответвления — перед шагами, двигающими прохождение (и начало): после такого шага
    # что-то может стать недостижимым; пробуем с самой поздней (ответвление короче)
    points = [0] + [i for i in range(1, len(states) - 1) if (states[i]["flags"] ^ states[i + 1]["flags"]) & sim.prog_flags]
    points = [i for i in points if not states[i]["menu"] and not states[i]["end"]]
    while True:
        miss = want - covered
        if not miss:
            break
        best = None
        plain = {x for x in miss if not x.startswith("HINT.")}
        for i in reversed(points):
            s0 = states[i]
            cands = []
            if plain:
                cands.append(greedy(sim, s0, plain, finish=False, cap=BRANCH_NODES, flat=True))
            if len(plain) < len(miss):
                cands.append(hint_branch(sim, s0, miss, BRANCH_NODES))
            for bs, bc in cands:
                gain = len(bc & miss)
                if gain and (best is None or gain > best[0]):
                    best = (gain, i, bs, bc)
            if best:
                break
        if best is None:
            break
        gain, i, bs, bc = best
        branches.setdefault(i, []).append(as_moves(bs))
        covered |= bc
    moves = [{"move": "начало акта", "slots": start_slots}]
    for i, m in enumerate(as_moves(steps)):
        for b in branches.get(i, []):
            moves.append({"branch": b})
        moves.append(m)
    miss = sorted(want - covered)
    nb = sum(len(v) for v in branches.values())
    print(f"акт {act}: ходов {len(steps)}, ответвлений {nb} ({sum(len(b) for v in branches.values() for b in v)} ходов); "
          f"показано {len(covered & want)} из {len(want)}; не показано {len(miss)}: {', '.join(miss)}", flush=True)
    end = states[-1]
    return {"act": act, "moves": moves}, {"act": act, "missed": miss}, covered, \
        (set(end["flags"]), dict(end["n"]), dict(end["c"]), end["h"]["n"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "work" / "fullrun" / "plan.json"))
    ap.add_argument("--acts", default="1,2,3,4")
    a = ap.parse_args(argv)
    plan, report = [], []
    carry = None
    shown_all = set()
    for act in map(int, a.acts.split(",")):
        p, r, covered, carry = plan_act(act, carry, shown_all)
        shown_all |= covered
        plan.append(p)
        report.append(r)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"plan": plan, "report": report}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"план → {out}")


if __name__ == "__main__":
    main()
