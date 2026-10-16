#!/usr/bin/env python3
"""Данные движка из источников: логика акта + граф + тексты + координаты слоёв + документы.

  python tools/data/gen_design.py ACT [ACT …] --out ПАПКА     (ACT — 1..4)

Пишет ПАПКА/act<N>.json. Источники: `design/logic/ACT<N>_LOGIC.md`, `acts/act<N>/ACT<N>_graph.json`,
`texts/act<N>/ACT<N>_TEXTS_FINAL.md`, `assets/gfx/cutouts/cutouts.json`, `design/docs/fields.json`,
шрифты документов — таблица `DOC` в `tools/assets/doc_preview.py` (единый источник с пробой
приёмки носителей). Собранное руками не править: правится логика или тексты, затем сборка заново.
Ошибки источников — исключение `DesignError` со списком (их же печатает `check_logic.py`).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import logic as L  # noqa: E402

ROOT = L.ROOT
sys.path.insert(0, str(ROOT / "tools" / "texts"))
sys.path.insert(0, str(ROOT / "tools" / "assets"))
import check_texts as CT  # noqa: E402
import doc_preview as DP  # noqa: E402

GFX = ROOT / "assets" / "gfx"
AUDIO = ROOT / "assets" / "audio"
CURSORS = {"look", "act", "move", "zoom"}
SPEAKERS = {"lap", "iz", "kuh", "anc", "pa", "paiz", "ans", "guest", "guestf", "waiter", "cap", "choice", "ui"}
FONT_CSS = {DP.SANS: ("PT Sans", 400), DP.SANSB: ("PT Sans", 700), DP.OLD: ("Old Standard TT", 400),
            DP.OLDB: ("Old Standard TT", 700), DP.MONO: ("PT Mono", 400), DP.HAND: ("Caveat", 400)}
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}
PLANS = ROOT / "docs" / "assets" / "plans_markers.json"
# плёнки P05: шрифт и чернила подписей — как у пробы приёмки (tools/assets/plans_preview.py, спека §7.2)
PLAN_STYLE = {"plan_hotel": (("PT Sans", 400), "#1c3478"), "plan_1908": (("Old Standard TT", 400), "#6e401e"),
              "plan_soviet": (("PT Mono", 400), "#1e6e3c")}
HATCH = (700, 860)          # где на подсвеченном стекле люк (координаты плёнки 1400×980)
LIGHTBOX = (260, 50)        # стекло 1400×980 на экране 1920×1080 — по центру, как в читалке


class DesignError(Exception):
    def __init__(self, errors):
        super().__init__("\n".join(errors))
        self.errors = errors


def ui_keys():
    src = ROOT / "texts" / "ui" / "UI_TEXTS.md"
    out = {}
    for line in src.read_text(encoding="utf-8").splitlines():
        m = re.match(r"([a-zа-яё0-9_]+)\s*\|\s*(\S.*)$", line.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def speaker_names():
    """Плашки говорящих — таблицы §5 ТЗ актов: | `id` | ПЛАШКА | …"""
    out = {}
    for f in sorted(ROOT.glob("texts/act*/BRIEF_ACT*_TEXTS.md")):
        for line in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\|\s*`([a-z]+)`\s*\|\s*([^|]+?)\s*\|", line)
            name = m.group(2).split(" (")[0].strip() if m else ""   # «ГРОМКАЯ СВЯЗЬ (голос Изольды)» → плашка
            if m and name.isupper() and m.group(1) not in out:
                out[m.group(1)] = name
    return out


def gfx_exists(name):
    return (GFX / f"{name}.png").is_file()


def plan_films(mode):
    """Три плёнки P05 в одном из положений (спека §3, «Плёнки P05 на стекле Z10»): рамки — как легли,
    люк — нарисованный источник на настоящий люк и доворот по номеру 317 (одна вертикаль); купол,
    подписи, фасад — кривые стопки по ложной опоре. Сдвиг tx, ty и поворот rot (градусы, против
    часовой, как в plans_preview.py) — вокруг точки cx, cy плёнки."""
    data = json.loads(PLANS.read_text(encoding="utf-8"))
    anchor = {"подписи": ("hall", "hall"), "фасад": ("room317", "room317"), "купол": ("dome", "room317")}
    hotel = data["plan_hotel"]["markers"]
    films = []
    for name in ("plan_hotel", "plan_1908", "plan_soviet"):
        p = data[name]
        sx, sy = p["source"]
        tx = ty = rot = 0.0
        if mode == "люк":
            tx, ty, rot = HATCH[0] - sx, HATCH[1] - sy, p["angle_deg"]
        elif mode in anchor:
            own = anchor[mode][0] if anchor[mode][0] in p["markers"] else anchor[mode][1]
            ref = hotel[anchor[mode][0]]
            m = p["markers"][own]
            tx, ty = ref["x"] - m["x"], ref["y"] - m["y"]
        elif mode != "рамки":
            raise ValueError(f"положение плёнок «{mode}» не из рамки, люк, купол, подписи, фасад")
        font, ink = PLAN_STYLE[name]
        films.append({"img": f"docs/{name}", "cx": sx, "cy": sy, "tx": round(tx, 1), "ty": round(ty, 1),
                      "rot": rot, "font": font, "ink": ink,
                      "labels": [{"x": m["x"], "y": m["y"], "t": m["label"], "side": m.get("side", "r")}
                                 for m in p["markers"].values() if m["label"]]})
    return films


def build(act):
    errors = []

    def err(where, msg):
        errors.append(f"{where}: {msg}")

    lpath = ROOT / "design" / "logic" / f"ACT{act}_LOGIC.md"
    S = L.read_sections(lpath)
    graph = json.loads((ROOT / "acts" / f"act{act}" / f"ACT{act}_graph.json").read_text(encoding="utf-8"))
    texts, terrs = CT.parse_texts(ROOT / "texts" / f"act{act}" / f"ACT{act}_TEXTS_FINAL.md")
    for e in terrs:
        err("тексты", e)
    # реплики прошлых актов (осмотр вантуза и меню, отказы «не тот предмет»): слот можно назвать
    # в логике следующего акта — он войдёт в данные акта как заимствованный; свои слоты главнее
    earlier = {}
    for k in range(1, act):
        t, _ = CT.parse_texts(ROOT / "texts" / f"act{k}" / f"ACT{k}_TEXTS_FINAL.md")
        earlier.update(t)
    own = set(texts)
    borrowed = set()

    def known(slot):
        if slot in texts:
            return True
        if slot in earlier:
            texts[slot] = earlier[slot]
            borrowed.add(slot)
            return True
        return False
    cutouts = json.loads((GFX / "cutouts" / "cutouts.json").read_text(encoding="utf-8"))
    fields = json.loads((ROOT / "design" / "docs" / "fields.json").read_text(encoding="utf-8"))
    ui = ui_keys()
    gflags = set(graph["flags_glossary"])
    actions = {a["id"]: a for a in graph["actions"]}
    lname = lpath.name

    def cond(text, where):
        try:
            tree = L.parse_cond(text)
        except ValueError as e:
            err(where, str(e))
            return None
        for f in L.cond_flags(tree):
            if f not in gflags and not L.is_screen(f):
                err(where, f"флаг «{f}» не из графа")
        for s in L.cond_slots(tree):
            if not known(s):
                err(where, f"слот «{s}» в условии не найден в текстах")
        return tree

    def slot_ref(v, where, groups):
        v = L.dash(v)
        if v is None:
            return None
        if v.startswith("@"):
            if v[1:] not in groups:
                err(where, f"цепочки «{v[1:]}» нет")
            return v
        if not known(v):
            err(where, f"слота «{v}» нет в текстах акта")
        return v

    def layer_img(name, where):
        """«st_x» / «ov_x» → слой с координатами; «rooms/room_w1» → фон."""
        name = name.strip()
        if name.startswith("планы:"):
            mode, _, onto = name[6:].partition("@")
            try:
                films = plan_films(mode.strip())
            except ValueError as e:
                err(where, str(e))
                films = []
            lay = {"plans": films, "x": 0, "y": 0}
            if onto:
                try:
                    pts = [[int(v) for v in p.split(",")] for p in onto.split(";")]
                    assert len(pts) == 3 and all(len(p) == 2 for p in pts)
                except (ValueError, AssertionError):
                    err(where, f"«{name}»: после @ — три точки x,y;x,y;x,y (углы плёнки: верх-лево, верх-право, низ-лево)")
                    pts = None
                lay["onto"] = pts
            else:
                lay["box"] = "docs/paper_lightbox"
                lay["x"], lay["y"] = LIGHTBOX
            return lay
        if "/" in name:
            if not gfx_exists(name):
                err(where, f"картинки {name}.png нет")
            return {"img": name, "x": 0, "y": 0}
        if name.startswith("ov_"):
            if not gfx_exists(f"cutouts/{name}"):
                err(where, f"оверлея {name}.png нет")
            return {"img": f"cutouts/{name}", "x": 0, "y": 0}
        c = cutouts.get(name)
        if not c:
            err(where, f"слоя {name} нет в cutouts.json")
            return {"img": f"cutouts/{name}", "x": 0, "y": 0}
        return {"img": f"cutouts/{name}", "x": c["x"], "y": c["y"], "w": c["w"], "h": c["h"]}

    def frame(spec, where):
        """«фон+слой+слой;фон2+…» → [[слои кадра 1], …]; «вид:W1» → {"view": "W1"}."""
        out = []
        for part in [p.strip() for p in re.split(r";(?![\d])", spec) if p.strip()]:
            if part.startswith("вид:"):
                names = [n.strip() for n in part[4:].split("+")]
                fr = {"view": names[0]}
                if names[1:]:
                    fr["extra"] = [layer_img(n, where) for n in names[1:]]
                out.append(fr)
                continue
            names = [n.strip() for n in part.split("+")]
            out.append([layer_img(names[0], where)] + [layer_img(n, where) for n in names[1:]])
        return out

    def effects(text, where):
        try:
            effs = L.parse_effects(text)
        except ValueError as e:
            err(where, str(e))
            return []
        for e in effs:
            for k in ("add", "remove"):
                if k in e and e[k] not in gflags and not L.is_screen(e[k]):
                    err(where, f"флаг «{e[k]}» не из графа")
            if "sfx" in e or "loop" in e or "stop" in e or "music" in e or "amb" in e:
                nm = e.get("sfx") or e.get("loop") or e.get("stop") or e.get("music") or e.get("amb")
                if not (e.get("music") == "стоп" or (AUDIO / f"{nm}.ogg").is_file()):
                    err(where, f"звука {nm}.ogg нет")
            if "frame" in e:
                e["frame"] = frame(e["frame"], where)
            if "doc" in e and not known(e["doc"]):
                err(where, f"документа {e['doc']} нет в текстах")
            if "act" in e:
                e["act"] = int(e["act"])
        return effs

    def action(v, where):
        v = L.dash(v)
        if v and v not in actions:
            err(where, f"действия {v} нет в графе")
        return v

    # ---- виды и слои
    views = {}
    for r in L.table(S, "Виды"):
        w = f"{lname}:{r['_line']}"
        bg = r["Фон"]
        if not gfx_exists(bg):
            err(w, f"фона {bg}.png нет")
        views[r["Вид"]] = {"type": r["Тип"], "bg": bg, "parent": L.dash(r["Родитель"]),
                           "music": L.dash(r["Музыка"]), "amb": L.dash(r["Амбиент"]),
                           "layers": [], "zones": []}
    for v in views.values():
        if v["parent"] and v["parent"] not in views:
            err(lname, f"родителя {v['parent']} нет среди видов")
    for r in L.table(S, "Слои"):
        w = f"{lname}:{r['_line']}"
        if r["Вид"] not in views:
            err(w, f"вида {r['Вид']} нет")
            continue
        lay = layer_img(r["Слой"], w)
        lay["when"] = cond(r["Когда"], w)
        lay["name"] = r["Слой"]
        views[r["Вид"]]["layers"].append(lay)

    # ---- надписи движка на чистых полях арта (табличка экспоната, бирка, табло; спека §3)
    LABEL_FONT = {"sans": ("PT Sans", 400), "sansb": ("PT Sans", 700), "old": ("Old Standard TT", 400),
                  "oldb": ("Old Standard TT", 700), "mono": ("PT Mono", 400), "hand": ("Caveat", 400)}
    for vid in views:
        views[vid]["labels"] = []
    for r in L.table(S, "Надписи"):
        w = f"{lname}:{r['_line']}"
        if r["Вид"] not in views:
            err(w, f"вида {r['Вид']} нет")
            continue
        try:
            x, y, ww, hh = (int(v) for v in r["Где"].split(","))
        except ValueError:
            err(w, f"«{r['Где']}» не x,y,w,h")
            continue
        font = LABEL_FONT.get(r["Шрифт"].strip())
        if not font:
            err(w, f"шрифт «{r['Шрифт']}» не из {sorted(LABEL_FONT)}")
            continue
        color = r["Цвет"].strip()
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            err(w, f"цвет «{color}» не #rrggbb")
        views[r["Вид"]]["labels"].append({
            "box": [x, y, ww, hh], "lines": [t.strip() for t in r["Текст"].split(" / ")], "font": font,
            "color": color, "angle": float(L.dash(r.get("Угол", "")) or 0), "when": cond(r["Когда"], w)})

    # ---- зоны
    zone_ids = set()
    for r in L.table(S, "Зоны"):
        w = f"{lname}:{r['_line']}"
        vid = r["Вид"]
        if vid not in views:
            err(w, f"вида {vid} нет")
            continue
        z = {"id": r["Зона"], "name": r["Название"], "cursor": r["Курсор"], "when": cond(r["Когда"], w),
             "props": [p.strip() for p in r.get("Свойства", "").split(",") if p.strip()]}
        if z["cursor"] not in CURSORS:
            err(w, f"курсор «{z['cursor']}» не из {sorted(CURSORS)}")
        where_ = r["Где"].strip()
        if where_.startswith("слой "):
            z["layer"] = layer_img(where_[5:], w)
        else:
            rects = []
            for part in where_.split(";"):
                try:
                    x, y, ww, hh = (int(v) for v in part.split(","))
                except ValueError:
                    err(w, f"прямоугольник «{part}» не x,y,w,h")
                    continue
                if ww < 44 or hh < 44:
                    err(w, f"зона {z['id']}: сторона меньше 44 px ({ww}×{hh})")
                if x < 0 or y < 0 or x + ww > 1920 or y + hh > 1080:
                    err(w, f"зона {z['id']}: прямоугольник выходит за кадр")
                rects.append([x, y, ww, hh])
            z["rects"] = rects
        key = f"{vid}.{z['id']}"
        if key in zone_ids:
            err(w, f"зона {key} повторяется")
        zone_ids.add(key)
        views[vid]["zones"].append(z)

    # ---- цепочки (нужны раньше, для ссылок @)
    groups = {}
    chain_tables = S.get("Цепочки", []) + S.get("Предметы", [])[1:]
    for t in chain_tables:
        for r in t:
            if "Группа" not in r:
                continue
            groups.setdefault(r["Группа"], [])
    for t in chain_tables:
        for r in t:
            if "Группа" not in r:
                continue
            w = f"{lname}:{r['_line']}"
            groups[r["Группа"]].append({"when": cond(r["Условие"], w), "slot": slot_ref(r["Слот"], w, groups),
                                        "action": action(r.get("Граф", ""), w),
                                        "effects": effects(r.get("Эффекты", ""), w)})

    # ---- действия
    rules = {}
    verbs_used = set()
    for r in L.table(S, "Действия"):
        w = f"{lname}:{r['_line']}"
        zk, verb = r["Зона"], r["Глагол"]
        if zk not in zone_ids:
            err(w, f"зоны {zk} нет")
        if verb not in ("осмотр", "клик") and not verb.startswith("предмет:"):
            verbs_used.add(verb)
            if f"verb_{verb}" not in ui:
                err(w, f"нет подписи verb_{verb} в texts/ui/UI_TEXTS.md")
        rules.setdefault(zk, {}).setdefault(verb, []).append({
            "when": cond(r["Условие"], w), "slot": slot_ref(r["Слот"], w, groups),
            "action": action(r["Граф"], w), "effects": effects(r["Эффекты"], w), "line": r["_line"]})

    # ---- сцены
    scenes = {}
    for r in L.table(S, "Сцены"):
        w = f"{lname}:{r['_line']}"
        scenes.setdefault(r["Сцена"], []).append({
            "slot": slot_ref(r["Слот"], w, groups), "frames": frame(r["Кадр"], w),
            "sound": effects(r["Звук"], w), "effects": effects(r["Эффекты"], w)})

    # ---- меню
    menus = {}
    for r in L.table(S, "Меню"):
        w = f"{lname}:{r['_line']}"
        lab = r["Подпись"]
        if lab in texts:
            choice = [l["text"] for l in texts[lab]["lines"] if l["speaker"] == "choice"]
            if not choice:
                err(w, f"у слота {lab} нет строки choice для подписи")
            label = {"text": choice[0] if choice else lab}
        elif lab in ui:
            label = {"ui": lab}
        else:
            err(w, f"подпись «{lab}» — ни слот с choice, ни ключ интерфейса")
            label = {"text": lab}
        items = menus.setdefault(r["Меню"], [])
        it = next((i for i in items if i["id"] == r["Пункт"]), None)
        if it is None:
            it = {"id": r["Пункт"], "label": label, "rules": []}
            items.append(it)
        it["rules"].append({"when": cond(r["Условие"], w), "slot": slot_ref(r["Слот"], w, groups),
                            "action": action(r["Граф"], w), "effects": effects(r["Эффекты"], w),
                            "line": r["_line"]})

    # ---- подсказки
    hints = []
    for r in L.table(S, "Подсказки"):
        w = f"{lname}:{r['_line']}"
        topic = r["Тема"]
        for k in (1, 2, 3):
            if f"HINT.{topic}.{k}" not in texts:
                err(w, f"нет слота HINT.{topic}.{k}")
        hints.append({"topic": topic, "when": cond(r["Открыта, когда"], w)})

    # ---- предметы
    items = {}
    for r in L.table(S, "Предметы", 0):
        w = f"{lname}:{r['_line']}"
        icon = r["Иконка"]
        if not gfx_exists(icon):
            err(w, f"иконки {icon}.png нет")
        items[r["Предмет"]] = {"icon": icon, "when": cond(r["При себе, когда"], w),
                               "look": slot_ref(r["Осмотр"], w, groups),
                               "look_effects": effects(r["Эффекты осмотра"], w),
                               "miss": slot_ref(r["Мимо (неплоское)"], w, groups),
                               "miss_flat": slot_ref(r["Мимо (плоское)"], w, groups)}
    for zk, vv in rules.items():
        for verb in vv:
            if verb.startswith("предмет:") and verb[8:] not in items:
                err(lname, f"{zk}: предмета {verb[8:]} нет в «Предметах»")

    # ---- документы
    docs = {}
    for r in L.table(S, "Документы"):
        w = f"{lname}:{r['_line']}"
        d = r["Документ"]
        if not known(d) or not texts[d].get("doc"):
            err(w, f"документа {d} (блок text) нет в текстах")
        carrier = r["Носитель"]
        if "+" in carrier:
            # план на подсвеченном стекле (DOC.map_*, спека §7.2): подписи — по меткам плёнки
            carrier, plan = [c.strip() for c in carrier.split("+", 1)]
            for c in (carrier, plan):
                if not gfx_exists(c):
                    err(w, f"носителя {c}.png нет")
            film = next((f for f in plan_films("рамки") if f["img"] == plan), None)
            if film is None:
                err(w, f"плёнки {plan} нет в {PLANS.name}")
                continue
            lines = texts.get(d, {}).get("doc") or []
            for lab in film["labels"]:
                if lab["t"] not in [l.strip() for l in lines]:
                    err(w, f"подписи «{lab['t']}» с плёнки нет в тексте {d}")
            docs[d] = {"carrier": carrier, "plan": film, "lines": lines, "font": film["font"],
                       "first": film["font"], "field": {}, "caption": None}
            continue
        if not gfx_exists(carrier):
            err(w, f"носителя {carrier}.png нет")
        cname = carrier.split("/")[-1]
        if cname not in fields:
            err(w, f"поля носителя {cname} нет в design/docs/fields.json")
        if d not in DP.DOC:
            err(w, f"шрифтов документа {d} нет в tools/assets/doc_preview.py")
            font, first = DP.SANS, None
        else:
            dc, font, first = DP.DOC[d]
            if dc != cname:
                err(w, f"носитель {cname} не совпадает с пробой приёмки ({dc})")
        cap = None
        m = re.match(r"(.+?)\s*→\s*(\S+)$", r["Подпись при условии"].strip())
        if m:
            cap = {"when": cond(m.group(1), w), "slot": slot_ref(m.group(2), w, groups)}
        docs[d] = {"carrier": carrier, "field": fields.get(cname, {}), "font": FONT_CSS[font],
                   "first": FONT_CSS[first] if first else None, "lines": texts.get(d, {}).get("doc") or [],
                   "caption": cap}

    # ---- тексты
    out_texts = {}
    for sid, s in texts.items():
        lines = []
        for l in s["lines"]:
            if l["speaker"] not in SPEAKERS:
                err(f"тексты {sid}", f"спикер {l['speaker']} неизвестен")
            if l["speaker"] == "choice":
                continue
            lines.append({"s": l["speaker"], "e": l["emotion"], "t": l["text"]})
        out_texts[sid] = {"lines": lines}

    other = {r["Слот"]: r["Где звучит"] for r in L.table(S, "Прочее")}

    # области экранных флагов: на каких видах флаг живёт (без области — только на своём виде)
    scopes = {}
    for r in L.table(S, "Экранные флаги"):
        w = f"{lname}:{r['_line']}"
        f = r["Флаг"]
        if not L.is_screen(f):
            err(w, f"«{f}» — не экранный флаг (scr_*)")
        vs = [v.strip() for v in r["Виды"].split(",") if v.strip()]
        for v in vs:
            if v not in views:
                err(w, f"вида {v} нет")
        scopes[f] = vs

    # служебные советы Предка: «Подожди» и первое нажатие есть только в Акте I — в других актах
    # движок берёт их оттуда (SLOT_FLAGS, Акты II–IV: «та же реплика»)
    hint_slots = {"intro": "HINT.intro", "cooldown": "HINT.cooldown", "done": "HINT.done"}
    if act != 1:
        t1, _ = CT.parse_texts(ROOT / "texts" / "act1" / "ACT1_TEXTS_FINAL.md")
        for k in ("HINT.intro", "HINT.cooldown", "UI.inventory"):   # подпись «При себе» — тоже из Акта I
            if k not in out_texts:
                out_texts[k] = {"lines": [{"s": l["speaker"], "e": l["emotion"], "t": l["text"]} for l in t1[k]["lines"]]}
    for k, v in hint_slots.items():
        if v not in out_texts:
            err(lname, f"нет слота {v} для совета Предка")

    data = {
        "act": act, "roman": ROMAN[act], "start_flags": graph["start_flags"], "goal_flags": graph["act_goal_flags"],
        "graph": {a["id"]: {"requires": a["requires"], "adds": a["adds"], "removes": a["removes"],
                            "optional": a["optional"]} for a in graph["actions"]},
        "flags": sorted(gflags), "views": views, "rules": rules, "chains": groups, "scenes": scenes,
        "menus": menus, "hints": hints, "hint_slots": hint_slots, "items": items, "docs": docs,
        "texts": out_texts, "other": other, "speakers": speaker_names(),
        "screen_scopes": scopes, "borrowed": sorted(borrowed),
    }
    if errors:
        raise DesignError(errors)
    return data


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("acts", nargs="+", type=int)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for act in a.acts:
        try:
            data = build(act)
        except DesignError as e:
            print(f"Акт {act}: ошибок {len(e.errors)}")
            for x in e.errors:
                print("  " + x)
            return 1
        (out / f"act{act}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"Акт {act}: видов {len(data['views'])}, зон {sum(len(v['zones']) for v in data['views'].values())}, "
              f"правил {sum(len(r) for z in data['rules'].values() for r in z.values())}, сцен {len(data['scenes'])}, "
              f"слотов {len(data['texts'])} → {out / f'act{act}.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
