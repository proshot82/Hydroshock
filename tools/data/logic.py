#!/usr/bin/env python3
"""Разбор файлов логики актов `design/logic/ACT*_LOGIC.md` (шаг 2 плана сборки).

Общий модуль для генератора данных движка (`gen_design.py`) и проверки (`check_logic.py`).
Файл логики — markdown: разделы `## Имя` с таблицами. Здесь: чтение таблиц, разбор условий
(флаги графа, ¬ ∧ ∨, скобки, shown(), n(), pos=, счётчики) в дерево и разбор эффектов.
Дерево условия — JSON-совместимое: так же его вычисляет движок в браузере.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------- таблицы


def read_sections(path):
    """{раздел: [таблица, …]}, таблица — список словарей по заголовку."""
    sections, cur, table, header = {}, None, None, None
    for n, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if line.startswith("## "):
            cur = line[3:].strip()
            sections.setdefault(cur, [])
            table = header = None
            continue
        if not line.startswith("|"):
            table = header = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            header = cells
            table = []
            sections.setdefault(cur, []).append(table)
            continue
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        if len(cells) != len(header):
            raise ValueError(f"{path}:{n}: в строке {len(cells)} ячеек, в заголовке {len(header)}")
        row = dict(zip(header, cells))
        row["_line"] = n
        table.append(row)
    return sections


def table(sections, name, idx=0):
    t = sections.get(name) or []
    return t[idx] if len(t) > idx else []


# ---------------------------------------------------------------- условия

TOKEN = re.compile(r"\s*(¬|!|∧|&|∨|\||\(|\)|shown\([^)]*\)|n\([^)]*\)\s*(?:>=|<=|=|>|<)\s*\d+|"
                   r"pos\s*=\s*[a-z_]+|[a-z_]+\.n\s*(?:>=|<=|=|>|<)\s*\d+|act\s*(?:>=|<=|=)\s*\d+|[A-Za-z_][A-Za-z0-9_]*)")


def parse_cond(text):
    """Строка условия → дерево. Пустая строка → None (всегда истинно)."""
    text = (text or "").strip()
    if not text or text in ("—", "-"):
        return None
    toks, pos = [], 0
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            raise ValueError(f"условие «{text}»: не разобрать с «{text[pos:]}»")
        toks.append(m.group(1).strip())
        pos = m.end()
    toks.append(None)
    i = 0

    def peek():
        return toks[i]

    def take():
        nonlocal i
        t = toks[i]
        i += 1
        return t

    def atom():
        t = take()
        if t in ("¬", "!"):
            return {"not": atom()}
        if t == "(":
            e = orr()
            if take() != ")":
                raise ValueError(f"условие «{text}»: нет закрывающей скобки")
            return e
        if t is None:
            raise ValueError(f"условие «{text}»: оборвано")
        m = re.fullmatch(r"shown\(\s*([^)]+?)\s*\)", t)
        if m:
            return {"shown": m.group(1)}
        m = re.fullmatch(r"n\(\s*([^)]+?)\s*\)\s*(>=|<=|=|>|<)\s*(\d+)", t)
        if m:
            return {"cmp": "n:" + m.group(1), "op": m.group(2), "v": int(m.group(3))}
        m = re.fullmatch(r"pos\s*=\s*([a-z_]+)", t)
        if m:
            return {"pos": m.group(1)}
        m = re.fullmatch(r"([a-z_]+)\.n\s*(>=|<=|=|>|<)\s*(\d+)", t)
        if m:
            return {"cmp": m.group(1), "op": m.group(2), "v": int(m.group(3))}
        m = re.fullmatch(r"act\s*(>=|<=|=)\s*(\d+)", t)
        if m:
            return {"cmp": "act", "op": m.group(1), "v": int(m.group(2))}
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", t):
            return {"f": t}
        raise ValueError(f"условие «{text}»: лишнее «{t}»")

    def andd():
        e = [atom()]
        while peek() in ("∧", "&"):
            take()
            e.append(atom())
        return e[0] if len(e) == 1 else {"and": e}

    def orr():
        e = [andd()]
        while peek() in ("∨", "|"):
            take()
            e.append(andd())
        return e[0] if len(e) == 1 else {"or": e}

    tree = orr()
    if peek() is not None:
        raise ValueError(f"условие «{text}»: лишнее «{peek()}»")
    return tree


def cond_flags(tree, acc=None):
    """Все флаги графа, упомянутые в условии."""
    acc = set() if acc is None else acc
    if tree is None:
        return acc
    if "f" in tree:
        acc.add(tree["f"])
    for k in ("and", "or"):
        for e in tree.get(k, []):
            cond_flags(e, acc)
    if "not" in tree:
        cond_flags(tree["not"], acc)
    return acc


def cond_slots(tree, acc=None):
    acc = set() if acc is None else acc
    if tree is None:
        return acc
    if "shown" in tree:
        acc.add(tree["shown"])
    if "cmp" in tree and tree["cmp"].startswith("n:"):
        acc.add(tree["cmp"][2:])
    for k in ("and", "or"):
        for e in tree.get(k, []):
            cond_slots(e, acc)
    if "not" in tree:
        cond_slots(tree["not"], acc)
    return acc


def evaluate(tree, st):
    """st: {"flags": set, "pos": str, "n": {слот: k}, "c": {счётчик: k}, "act": int}."""
    if tree is None:
        return True
    if "f" in tree:
        return tree["f"] in st["flags"]
    if "not" in tree:
        return not evaluate(tree["not"], st)
    if "and" in tree:
        return all(evaluate(e, st) for e in tree["and"])
    if "or" in tree:
        return any(evaluate(e, st) for e in tree["or"])
    if "shown" in tree:
        return st["n"].get(tree["shown"], 0) > 0
    if "pos" in tree:
        return st["pos"] == tree["pos"]
    if "cmp" in tree:
        k = tree["cmp"]
        if k.startswith("n:"):
            v = st["n"].get(k[2:], 0)
        elif k == "act":
            v = st.get("act", 1)
        else:
            v = st["c"].get(k, 0)
        op, x = tree["op"], tree["v"]
        return {">=": v >= x, "<=": v <= x, "=": v == x, ">": v > x, "<": v < x}[op]
    raise ValueError(f"неизвестный узел условия {tree}")


# ---------------------------------------------------------------- эффекты

EFFECT_KEYS = {"вид": "view", "док": "doc", "сцена": "scene", "меню": "menu", "цепочка": "chain",
               "звук": "sfx", "музыка": "music", "кадр": "frame", "акт": "act", "портрет": "portrait",
               "петля": "loop", "стоп": "stop", "амбиент": "amb"}


def parse_effects(text):
    """«+a, -b, pos=room, вид:W1, …» → список словарей."""
    out = []
    for part in [p.strip() for p in (text or "").split(",") if p.strip()]:
        if part.startswith("+") and re.fullmatch(r"\+[a-z_0-9]+", part):
            out.append({"add": part[1:]})
        elif part.startswith("-") and re.fullmatch(r"-[a-z_0-9]+", part):
            out.append({"remove": part[1:]})
        elif re.fullmatch(r"pos=[a-z_]+", part):
            out.append({"pos": part[4:]})
        elif re.fullmatch(r"[a-z]+\+", part):
            out.append({"inc": part[:-1]})
        elif ":" in part:
            k, v = part.split(":", 1)
            if k not in EFFECT_KEYS:
                raise ValueError(f"эффект «{part}»: неизвестный вид «{k}»")
            out.append({EFFECT_KEYS[k]: v.strip()})
        elif re.fullmatch(r"(sfx|ui|sting)_[a-z_0-9]+", part):
            out.append({"sfx": part})   # в колонке «Звук» сцен можно без «звук:»
        else:
            raise ValueError(f"эффект «{part}» не разобран")
    return out


def dash(v):
    v = (v or "").strip()
    return None if v in ("", "—", "-") else v
