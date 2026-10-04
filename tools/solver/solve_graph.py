#!/usr/bin/env python3
"""Абстрактный солвер графов A (формат сдачи акта, промпт V2, раздел A).

Что проверяет (handoff §8 п. 6, промпт V2 раздел G):
  1. Схема: обязательные поля, уникальность id, типы действий, комнаты,
     все флаги — из flags_glossary.
  2. Достижимость цели акта из start_flags.
  3. Отсутствие софтлоков при ЛЮБОМ допустимом порядке: из каждого
     достижимого состояния цель ещё достижима.
  4. Безопасность removes: ни один переход с removes не ведёт в тупик.
  5. Цель достижима без optional-действий.
  6. Обязательные (bottleneck) действия, кратчайший путь, свободные пары.
  7. (--prev) Стыковка актов: start_flags акта N+1 гарантированно
     истинны в финальном состоянии акта N.

Модель: состояние — множество истинных флагов. Действие применимо, если
все requires истинны и применение меняет состояние:
  новое = (состояние − removes) ∪ adds.
Состояние, где все act_goal_flags истинны, — финальное (дальше не идём).

Запуск:
  python tools/solver/solve_graph.py act1.json
  python tools/solver/solve_graph.py act2.json --prev act1.json
  python tools/solver/solve_graph.py act1.json --json report.json

Код выхода: 0 — граф принят; 1 — найдены ошибки; 2 — файл не читается.
Только стандартная библиотека Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

ALLOWED_TYPES = {"inspect", "take", "use", "combine", "talk", "install", "read"}
REQUIRED_KEYS = ("act", "start_flags", "flags_glossary", "actions", "rooms", "act_goal_flags")
DEFAULT_MAX_STATES = 2_000_000


class GraphError(Exception):
    """Файл не читается или не является графом A."""


@dataclass(frozen=True)
class Action:
    id: str
    name: str
    room: str
    type: str
    requires: frozenset
    adds: frozenset
    removes: frozenset
    optional: bool


@dataclass
class Graph:
    act: str
    start: frozenset
    goal: frozenset
    glossary: dict
    rooms: list
    actions: list
    assumptions: list


@dataclass
class Report:
    act: str
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    info: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


# ---------------------------------------------------------------- загрузка


def room_code(entry: str) -> str:
    """«W1 — Номер 317» → «W1». Разделитель — тире или дефис с пробелами."""
    for sep in (" — ", " – ", " - "):
        if sep in entry:
            return entry.split(sep, 1)[0].strip()
    return entry.strip()


def load_graph(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise GraphError(f"не удалось прочитать {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise GraphError(f"{path}: файл не в UTF-8 (пересохранён редактором?): {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GraphError(f"{path}: неверный JSON, строка {exc.lineno}, столбец {exc.colno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise GraphError(f"{path}: корень JSON должен быть объектом")
    return data


def _flag_list(value, where: str, report: Report) -> frozenset:
    if value is None:
        return frozenset()
    if not isinstance(value, list) or not all(isinstance(f, str) for f in value):
        report.errors.append(f"{where}: ожидается список строк-флагов")
        return frozenset()
    if len(set(value)) != len(value):
        report.warnings.append(f"{where}: флаги повторяются")
    return frozenset(value)


def parse_graph(data: dict, report: Report) -> Graph | None:
    """Проверка схемы. Возвращает None, если дальше анализировать нельзя."""
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        report.errors.append("нет обязательных полей: " + ", ".join(missing))
        return None

    glossary = data["flags_glossary"]
    if not isinstance(glossary, dict):
        report.errors.append("flags_glossary: ожидается объект {флаг: описание}")
        return None
    for flag, desc in glossary.items():
        if not isinstance(desc, str) or not desc.strip():
            report.warnings.append(f"flags_glossary.{flag}: пустое описание")

    rooms = data["rooms"]
    if not isinstance(rooms, list) or not all(isinstance(r, str) for r in rooms):
        report.errors.append("rooms: ожидается список строк")
        return None
    room_codes = [room_code(r) for r in rooms]
    if len(set(room_codes)) != len(room_codes):
        report.errors.append("rooms: коды комнат повторяются")

    start = _flag_list(data["start_flags"], "start_flags", report)
    goal = _flag_list(data["act_goal_flags"], "act_goal_flags", report)
    if not goal:
        report.errors.append("act_goal_flags пуст: у акта нет цели")

    raw_actions = data["actions"]
    if not isinstance(raw_actions, list) or not raw_actions:
        report.errors.append("actions: ожидается непустой список")
        return None

    actions: list[Action] = []
    seen: set[str] = set()
    for i, raw in enumerate(raw_actions):
        where = f"actions[{i}]"
        if not isinstance(raw, dict):
            report.errors.append(f"{where}: ожидается объект")
            continue
        aid = raw.get("id")
        if not isinstance(aid, str) or not aid:
            report.errors.append(f"{where}: нет id")
            continue
        where = f"действие {aid}"
        if aid in seen:
            report.errors.append(f"{where}: id повторяется")
            continue
        seen.add(aid)
        for key in ("name", "room", "type"):
            if not isinstance(raw.get(key), str) or not raw.get(key).strip():
                report.errors.append(f"{where}: нет поля {key}")
        atype = raw.get("type", "")
        if atype and atype not in ALLOWED_TYPES:
            report.errors.append(
                f"{where}: тип «{atype}» не из списка ({', '.join(sorted(ALLOWED_TYPES))})"
            )
        room = raw.get("room", "")
        if room and room_code(room) not in room_codes:
            report.errors.append(f"{where}: комнаты «{room}» нет в rooms")
        optional = raw.get("optional", False)
        if not isinstance(optional, bool):
            report.errors.append(f"{where}: optional должен быть true/false")
            optional = bool(optional)
        act = Action(
            id=aid,
            name=raw.get("name", ""),
            room=room_code(room) if isinstance(room, str) else "",
            type=atype,
            requires=_flag_list(raw.get("requires"), f"{where}.requires", report),
            adds=_flag_list(raw.get("adds"), f"{where}.adds", report),
            removes=_flag_list(raw.get("removes"), f"{where}.removes", report),
            optional=optional,
        )
        if not act.adds and not act.removes:
            report.errors.append(f"{where}: не меняет ни одного флага (нет adds и removes)")
        if act.adds & act.removes:
            report.errors.append(
                f"{where}: один флаг и в adds, и в removes: {', '.join(sorted(act.adds & act.removes))}"
            )
        stray = act.removes - act.requires
        if stray:
            report.warnings.append(
                f"{where}: removes без requires ({', '.join(sorted(stray))}) — "
                "расходование должно быть видимым, т. е. расходуемое должно быть на руках"
            )
        actions.append(act)

    # Все флаги — из глоссария.
    known = set(glossary)
    used: set[str] = set(start) | set(goal)
    for flag in sorted(start - known):
        report.errors.append(f"start_flags: флага {flag} нет в глоссарии")
    for flag in sorted(goal - known):
        report.errors.append(f"act_goal_flags: флага {flag} нет в глоссарии")
    for act in actions:
        for key in ("requires", "adds", "removes"):
            flags = getattr(act, key)
            used |= flags
            for flag in sorted(flags - known):
                report.errors.append(f"действие {act.id}.{key}: флага {flag} нет в глоссарии")
    for flag in sorted(known - used):
        report.warnings.append(f"флаг {flag} есть в глоссарии, но нигде не используется")

    if goal and goal <= start:
        report.errors.append("цель акта истинна уже на старте")

    assumptions = data.get("assumptions", [])
    if not isinstance(assumptions, list):
        report.warnings.append("assumptions: ожидается список строк")
        assumptions = []

    act_name = data["act"] if isinstance(data["act"], str) else str(data["act"])
    return Graph(act_name, start, goal, glossary, rooms, actions, assumptions)


# ---------------------------------------------------------------- пространство состояний


def apply(state: frozenset, act: Action) -> frozenset | None:
    if not act.requires <= state:
        return None
    new = (state - act.removes) | act.adds
    return None if new == state else new


@dataclass
class Space:
    states: list                      # индекс → frozenset
    index: dict                       # frozenset → индекс
    edges: list                       # индекс → [(action_idx, target_idx)]
    goal_states: set
    truncated: bool


def explore(graph: Graph, actions: list[Action], max_states: int) -> Space:
    states = [graph.start]
    index = {graph.start: 0}
    edges: list[list] = [[]]
    goal_states: set[int] = set()
    queue = deque([0])
    truncated = False
    while queue:
        si = queue.popleft()
        state = states[si]
        if graph.goal <= state:
            goal_states.add(si)
            continue
        for ai, act in enumerate(actions):
            new = apply(state, act)
            if new is None:
                continue
            ti = index.get(new)
            if ti is None:
                if len(states) >= max_states:
                    truncated = True
                    continue
                ti = len(states)
                states.append(new)
                index[new] = ti
                edges.append([])
                queue.append(ti)
            edges[si].append((ai, ti))
    return Space(states, index, edges, goal_states, truncated)


def can_reach_goal(space: Space) -> list[bool]:
    """Для каждого состояния: достижима ли из него цель."""
    reverse: list[list[int]] = [[] for _ in space.states]
    for si, out in enumerate(space.edges):
        for _, ti in out:
            reverse[ti].append(si)
    good = [False] * len(space.states)
    queue = deque(space.goal_states)
    for gi in space.goal_states:
        good[gi] = True
    while queue:
        ti = queue.popleft()
        for si in reverse[ti]:
            if not good[si]:
                good[si] = True
                queue.append(si)
    return good


def path_to(space: Space, target: int, actions: list[Action]) -> list[str]:
    """Кратчайший путь (BFS) от старта до состояния target — список id действий."""
    parent: dict[int, tuple[int, int]] = {0: (-1, -1)}
    queue = deque([0])
    while queue:
        si = queue.popleft()
        if si == target:
            break
        for ai, ti in space.edges[si]:
            if ti not in parent:
                parent[ti] = (si, ai)
                queue.append(ti)
    if target not in parent:
        return []
    path = []
    node = target
    while node != 0:
        prev, ai = parent[node]
        path.append(actions[ai].id)
        node = prev
    return list(reversed(path))


def shortest_goal_path(space: Space, actions: list[Action]) -> list[str] | None:
    """Кратчайший путь до ближайшего финального состояния."""
    if not space.goal_states:
        return None
    dist = {0: 0}
    queue = deque([0])
    while queue:
        si = queue.popleft()
        if si in space.goal_states:
            return path_to(space, si, actions)
        for _, ti in space.edges[si]:
            if ti not in dist:
                dist[ti] = dist[si] + 1
                queue.append(ti)
    return None


def describe_state(state: frozenset) -> str:
    return "{" + ", ".join(sorted(state)) + "}" if state else "{}"


# ---------------------------------------------------------------- анализ


def analyse(graph: Graph, report: Report, max_states: int = DEFAULT_MAX_STATES) -> Space:
    actions = graph.actions
    space = explore(graph, actions, max_states)
    report.info["states"] = len(space.states)
    report.info["goal_states"] = len(space.goal_states)
    if space.truncated:
        report.errors.append(
            f"пространство состояний больше {max_states}: анализ неполон "
            "(слишком много независимых флагов — укрупнить граф или поднять --max-states)"
        )

    # 2. Достижимость цели.
    if not space.goal_states:
        report.errors.append("цель акта недостижима из start_flags")
        missing = graph.goal - set().union(*space.states)
        if missing:
            report.errors.append("ни в одном достижимом состоянии нет: " + ", ".join(sorted(missing)))
        never = [a.id for a in actions if not any(apply(s, a) for s in space.states)]
        if never:
            report.info["never_enabled"] = never
        return space

    path = shortest_goal_path(space, actions)
    report.info["shortest_path"] = path

    # 3. Софтлоки.
    good = can_reach_goal(space)
    dead = [si for si in range(len(space.states)) if not good[si]]
    report.info["dead_end_states"] = len(dead)
    for si in dead[:5]:
        report.errors.append(
            "СОФТЛОК: из состояния " + describe_state(space.states[si])
            + " цель недостижима; путь туда: " + (" → ".join(path_to(space, si, actions)) or "(старт)")
        )
    if len(dead) > 5:
        report.errors.append(f"…и ещё {len(dead) - 5} тупиковых состояний")

    # 4. Безопасность removes. Виновато то действие, которое переводит из
    # состояния, где цель достижима, в тупик (а не любое движение внутри тупика).
    unsafe = set()
    for si, out in enumerate(space.edges):
        for ai, ti in out:
            act = actions[ai]
            if act.removes and good[si] and not good[ti] and act.id not in unsafe:
                unsafe.add(act.id)
                report.errors.append(
                    f"removes действия {act.id} ({', '.join(sorted(act.removes))}) отрезает путь к цели: "
                    "после него из " + describe_state(space.states[si]) + " цель недостижима"
                )
    report.info["removes_actions"] = sorted(a.id for a in actions if a.removes)
    report.info["removes_unsafe"] = sorted(unsafe)

    # Действия, которые ни разу не становятся доступны.
    enabled = {ai for out in space.edges for ai, _ in out}
    never = [a.id for ai, a in enumerate(actions) if ai not in enabled]
    if never:
        report.info["never_enabled"] = never
        for aid in never:
            report.warnings.append(f"действие {aid} ни в одном достижимом состоянии не применимо (мёртвое)")

    # 5. Цель без optional.
    required_only = [a for a in actions if not a.optional]
    if len(required_only) != len(actions):
        sub = explore(graph, required_only, max_states)
        if not sub.goal_states:
            report.errors.append("без optional-действий цель недостижима: какое-то из них на деле обязательно")

    # 6. Bottleneck-действия: без них цель недостижима.
    bottlenecks = []
    for ai, act in enumerate(actions):
        rest = [a for j, a in enumerate(actions) if j != ai]
        if not explore(graph, rest, max_states).goal_states:
            bottlenecks.append(act.id)
            if act.optional:
                report.errors.append(f"действие {act.id} помечено optional, но без него цель недостижима")
    report.info["bottlenecks"] = bottlenecks

    # Свободные пары: в некотором достижимом нефинальном состоянии оба действия
    # применимы, ни одно не завершает акт, и они коммутируют (оба порядка дают
    # одно состояние). Поскольку софтлоков нет (проверено выше), оба порядка
    # ведут к цели.
    pairs = []
    on_path_ids = {a.id for a in required_only}
    for ai, bi in combinations(range(len(actions)), 2):
        a, b = actions[ai], actions[bi]
        if a.id not in on_path_ids or b.id not in on_path_ids:
            continue
        for si, state in enumerate(space.states):
            if si in space.goal_states:
                continue
            sa, sb = apply(state, a), apply(state, b)
            if sa is None or sb is None:
                continue
            if graph.goal <= sa or graph.goal <= sb:
                # Один из порядков уже завершает акт — второе действие после
                # финала не играется, это не свободная пара.
                continue
            sab, sba = apply(sa, b), apply(sb, a)
            if sab is not None and sab == sba:
                pairs.append((a.id, b.id))
                break
    report.info["free_pairs"] = pairs

    # Гарантированные флаги в финале — для стыковки со следующим актом.
    finals = [space.states[gi] for gi in space.goal_states]
    report.info["guaranteed_final_flags"] = sorted(frozenset.intersection(*finals))
    report.info["possible_final_flags"] = sorted(frozenset().union(*finals))

    # Статистика для лимитов промпта V2 (раздел G п. 4, п. 7).
    report.info["actions_total"] = len(actions)
    report.info["actions_required"] = len(required_only)
    report.info["rooms_used"] = sorted({a.room for a in actions})
    by_type: dict[str, int] = {}
    for a in required_only:
        by_type[a.type] = by_type.get(a.type, 0) + 1
    report.info["required_by_type"] = by_type
    return space


def check_chain(prev_report: Report, graph: Graph, report: Report) -> None:
    """start_flags акта N+1 обязаны быть гарантированно истинны в финале акта N."""
    guaranteed = set(prev_report.info.get("guaranteed_final_flags", []))
    possible = set(prev_report.info.get("possible_final_flags", []))
    for flag in sorted(graph.start - guaranteed):
        if flag in possible:
            report.errors.append(
                f"стыковка: {flag} истинен лишь в части финалов {prev_report.act} — не гарантирован"
            )
        else:
            report.errors.append(f"стыковка: {flag} не бывает истинен в финале {prev_report.act}")
    lost = guaranteed - graph.start
    if lost:
        report.warnings.append(
            f"стыковка: гарантированные флаги финала {prev_report.act} не перенесены в start_flags: "
            + ", ".join(sorted(lost))
        )


# ---------------------------------------------------------------- вывод


def solve_file(path: Path, max_states: int = DEFAULT_MAX_STATES) -> tuple[Report, Graph | None]:
    report = Report(act=path.name)
    data = load_graph(path)
    graph = parse_graph(data, report)
    if graph is None:
        return report, None
    report.act = graph.act
    if report.errors:
        # Схема битая — пространство состояний может врать. Не анализируем.
        return report, graph
    analyse(graph, report, max_states)
    return report, graph


def format_report(report: Report) -> str:
    lines = [f"=== Солвер графа A: {report.act} ==="]
    info = report.info
    if "states" in info:
        lines.append(f"Состояний: {info['states']}, финальных: {info['goal_states']}")
    if info.get("shortest_path"):
        sp = info["shortest_path"]
        lines.append(f"Кратчайший путь ({len(sp)} действий): " + " → ".join(sp))
    if "actions_total" in info:
        lines.append(
            f"Действий: {info['actions_total']} (обязательных {info['actions_required']}); "
            f"комнаты: {', '.join(info['rooms_used'])}"
        )
        lines.append("Обязательные по типам: " + ", ".join(
            f"{t} {n}" for t, n in sorted(info["required_by_type"].items())))
    if "bottlenecks" in info:
        lines.append("Bottleneck (без них цели нет): " + (", ".join(info["bottlenecks"]) or "—"))
    if "free_pairs" in info:
        fp = info["free_pairs"]
        lines.append(f"Свободные пары ({len(fp)}): " + (", ".join(f"{a}⇄{b}" for a, b in fp) or "—"))
    if "removes_actions" in info:
        lines.append("Действия с removes: " + (", ".join(info["removes_actions"]) or "—")
                     + ("; все безопасны" if not info.get("removes_unsafe") else ""))
    if "guaranteed_final_flags" in info:
        lines.append("Гарантированно в финале: " + (", ".join(info["guaranteed_final_flags"]) or "—"))
    for w in report.warnings:
        lines.append(f"ПРЕДУПРЕЖДЕНИЕ: {w}")
    for e in report.errors:
        lines.append(f"ОШИБКА: {e}")
    lines.append("ИТОГ: граф принят" if report.ok else f"ИТОГ: граф НЕ принят, ошибок {len(report.errors)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        # Консоль Windows по умолчанию не UTF-8 — без этого кириллица падает.
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="Абстрактный солвер графов A (BJ3).")
    parser.add_argument("graph", type=Path, help="JSON графа A акта")
    parser.add_argument("--prev", type=Path, help="граф A предыдущего акта — проверить стыковку")
    parser.add_argument("--json", type=Path, help="записать отчёт в JSON")
    parser.add_argument("--max-states", type=int, default=DEFAULT_MAX_STATES)
    args = parser.parse_args(argv)

    try:
        prev_report = None
        if args.prev:
            prev_report, _ = solve_file(args.prev, args.max_states)
            print(format_report(prev_report))
            print()
        report, graph = solve_file(args.graph, args.max_states)
        if prev_report is not None and graph is not None:
            if prev_report.ok:
                check_chain(prev_report, graph, report)
            else:
                report.errors.append(f"стыковка не проверена: предыдущий акт {prev_report.act} не принят")
    except GraphError as exc:
        print(f"ОШИБКА ВВОДА: {exc}", file=sys.stderr)
        return 2

    print(format_report(report))
    if args.json:
        payload = {"act": report.act, "ok": report.ok, "errors": report.errors,
                   "warnings": report.warnings, "info": report.info}
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = report.ok and (prev_report is None or prev_report.ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
