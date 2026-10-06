#!/usr/bin/env python3
"""Сверка docs/BJ3_ASSET_SPEC.md с текстами, графами, GDD и шрифтами.

Проверяет:
  • каждое имя файла определено одной строкой таблицы и подходит под шаблон
    своего класса (§1.7 спеки), размер — под класс;
  • у каждого состояния st_* есть база (экран, зум, крупный план, кадр);
  • каждый флаг в колонке «Когда» есть в графах актов (или в §0 SLOT_FLAGS),
    каждый слот — в ТЗ текстов;
  • покрыты: экраны W1–W6 и зумы Z01–Z13; все слоты OPEN/SEQ/END/EPI/PA
    итоговых текстов по актам (§4.2); все эмоции портретов из текстов, у
    эмоций Лапидуса в мыле — варианты пены; все документы DOC.* (§7.2) с
    определённым носителем; все слоты таблицы звуков GDD §8 (§9); все шрифты
    assets/fonts (§8) — ни больше, ни меньше;
  • файлы, на которые ссылаются таблицы кадров и документов, определены;
  • строка «Итого генерировать» в §0 совпадает с подсчётом.
Выход 0 — всё сходится; иначе список ошибок.

Запуск: python tools/check_asset_spec.py [docs/BJ3_ASSET_SPEC.md]
"""

import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "texts"))
import check_texts as ct  # noqa: E402

DOC = ROOT / "docs" / "BJ3_ASSET_SPEC.md"
GDD = ROOT / "docs" / "BJ3_GDD.md"
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4}
FILE = re.compile(r"^[A-Za-z0-9_\-]+\.(png|ogg|ttf)$")
SLOT = re.compile(r"^[A-Z][A-Z0-9]*\.[A-Za-z0-9_.]+$")
FRAME_SLOT = re.compile(r"^(OPEN|SEQ|END|EPI|PA)\.")
# имена вне графов: §0 docs/BJ3_SLOT_FLAGS.md и номер акта
EXTRA = {"act", "trolley.pos", "relics", "probe.n", "call.n", "hint.lock", "hint.n"}
POSITIONS = {"room", "door", "lift", "lobby", "crowd", "service", "exhibit", "stairs", "hall",
             "cabin", "receiving", "office"}

# класс → (шаблон имени, размер или None)
CLASSES = [
    ("room", re.compile(r"^room_w[1-6](_under)?\.png$"), "1920×1080"),
    ("zoom", re.compile(r"^zoom_z(0[1-9]|1[0-3])\.png$"), "1920×1080"),
    ("cu", re.compile(r"^cu_z(0[1-9]|1[0-3])_[a-z0-9_]+\.png$"), "1920×1080"),
    ("fr", re.compile(r"^fr_(a[1-4]|epi)_[a-z0-9_]+\.png$"), "1920×1080"),
    ("st", re.compile(r"^st_[a-z0-9_]+\.png$"), None),
    ("ov", re.compile(r"^ov_[a-z0-9_]+\.png$"), "1920×1080"),
    ("port", re.compile(r"^port_[a-z]+_[a-z0-9_]+\.png$"), "512×512"),
    ("ic", re.compile(r"^ic_[a-z0-9_]+\.png$"), "128×128"),
    ("media", re.compile(r"^(paper|page|plate|plaque|panel|label|card|tag|tray|box|token|photo|plan)_[a-z0-9_]+\.png$"),
     "1400×980"),
    ("mark", re.compile(r"^(stamp|mark)_[a-z0-9_]+\.png$"), None),
    ("ui", re.compile(r"^(bg_title|logo_title|icon_512)\.png$"), None),
    ("audio", re.compile(r"^(sfx|amb|bgm|mus|sting|blip|ui)_[a-z0-9_]+\.ogg$"), None),
    ("font", re.compile(r"^[A-Za-z0-9\-]+\.ttf$"), None),
]
UI_SIZES = {"bg_title.png": "1920×1080", "logo_title.png": "1200×420", "icon_512.png": "512×512"}


def classify(name):
    for cls, rx, _ in CLASSES:
        if rx.match(name):
            return cls
    return None


def sections(text):
    """Номер раздела «## N.» → текст раздела."""
    out, cur, buf = OrderedDict(), None, []
    for line in text.splitlines():
        m = re.match(r"^## (\d+)\. ", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = int(m.group(1)), []
            continue
        buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def rows(text):
    for line in text.splitlines():
        if line.startswith("| `"):
            yield [c.strip() for c in line.strip().strip("|").split("|")]


def ticks(cell):
    return re.findall(r"`([^`]+)`", cell)


def load_world():
    briefs, flags = {}, set()
    for act in range(1, 5):
        briefs[act] = ct.parse_brief(ROOT / "texts" / f"act{act}" / f"BRIEF_ACT{act}_TEXTS.md")
        g = json.loads((ROOT / "acts" / f"act{act}" / f"ACT{act}_graph.json").read_text(encoding="utf-8"))
        flags |= set(g["flags_glossary"]) | set(g["start_flags"])
    emotions, docs = set(), set()
    for act in range(1, 5):
        cur = None
        for line in (ROOT / "texts" / f"act{act}" / f"ACT{act}_TEXTS_FINAL.md").read_text(encoding="utf-8").splitlines():
            if line.startswith("### "):
                cur = line[4:].strip()
                continue
            m = re.match(r"^([a-z]+) \| ([a-z0-9_]+) \| ", line)
            if m and m.group(2) != "none":
                emotions.add(m.group(2))
            if cur and cur.startswith("DOC.") and line.startswith("```text"):
                docs.add(cur)
    return briefs, flags, emotions, docs


def gdd_sound_slots(all_slots):
    """Слоты таблицы звуков GDD §8; «`.after`» — хвост предыдущего слота, «PROBE.*» — семейство."""
    text = GDD.read_text(encoding="utf-8")
    sec = text[text.find("## 8. Звуки"):text.find("## 9. ")]
    need = set()
    for cells in (r for r in (l.strip().strip("|").split("|") for l in sec.splitlines() if l.startswith("| I"))):
        if len(cells) < 3:
            continue
        prev = None
        for tok in ticks(cells[2]):
            if tok.startswith(".") and prev:
                tok = prev + tok
            if tok.endswith(".*"):
                need.add(tok)
            elif tok in all_slots:
                need.add(tok)
            prev = tok
    return need


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0]) if argv else DOC
    text = path.read_text(encoding="utf-8")
    secs = sections(text)
    briefs, flags, emotions, docs = load_world()
    all_slots = set().union(*briefs.values())
    errors = []
    err = errors.append

    # 1. Определения: первая ячейка строки — одно имя файла
    defs, where = OrderedDict(), {}
    for num, body in secs.items():
        for cells in rows(body):
            first = ticks(cells[0])
            if len(first) == 1 and cells[0] == f"`{first[0]}`" and FILE.match(first[0]):
                name = first[0]
                if name in defs:
                    err(f"`{name}` определён дважды (§{where[name]} и §{num})")
                    continue
                defs[name], where[name] = cells, num
    by_class = {}
    for name, cells in defs.items():
        cls = classify(name)
        if cls is None:
            err(f"`{name}`: имя не подходит ни под один шаблон §1.7")
            continue
        by_class.setdefault(cls, []).append(name)
        want = UI_SIZES.get(name) or dict((c, s) for c, _, s in CLASSES)[cls]
        size = re.search(r"(\d+)×(\d+)", " ".join(cells[1:2]))
        if want and size and size.group(0) != want:
            err(f"`{name}`: размер {size.group(0)}, для класса нужно {want}")
        if want and not size and cls != "st":
            err(f"`{name}`: не указан размер ({want})")

    # 2. Состояния: база и флаги
    keys = {}
    for name in by_class.get("room", []):
        stem = name[len("room_"):-4]
        keys[stem.replace("_under", "u")] = name
    for name in by_class.get("zoom", []):
        keys[name[len("zoom_"):-4]] = name
    for name in by_class.get("cu", []) + by_class.get("fr", []):
        keys[name[:-4]] = name
    for name in by_class.get("st", []):
        stem = name[len("st_"):-4]
        base = max((k for k in keys if stem.startswith(k + "_")), key=len, default=None)
        if base is None:
            err(f"`{name}`: нет базы (экран, зум, крупный план или кадр) под префикс")
        when = defs[name][-1]
        for tok in ticks(when):
            if FILE.match(tok):
                if tok not in defs:
                    err(f"`{name}`: ссылка на неопределённый `{tok}`")
                continue
            inner = re.match(r"^shown\((.+)\)$", tok)
            tok = inner.group(1) if inner else tok
            if SLOT.match(tok):
                if tok not in all_slots:
                    err(f"`{name}`: слота `{tok}` нет в ТЗ")
            elif tok in EXTRA or tok in POSITIONS:
                continue
            elif re.match(r"^[a-z][a-z0-9_]*$", tok):
                if tok not in flags:
                    err(f"`{name}`: флага `{tok}` нет в графах")
            else:
                err(f"`{name}`: непонятный токен `{tok}` в «Когда»")
        # «поверх `st_…`» в описании
        for tok in ticks(defs[name][1] if len(defs[name]) > 2 else ""):
            if FILE.match(tok) and tok not in defs:
                err(f"`{name}`: «поверх» неопределённого `{tok}`")

    # 3. Экраны и зумы
    for w in range(1, 7):
        if f"room_w{w}.png" not in defs:
            err(f"нет базы экрана `room_w{w}.png`")
    for z in range(1, 14):
        if f"zoom_z{z:02d}.png" not in defs:
            err(f"нет зума `zoom_z{z:02d}.png`")

    # 4. Кадры немых сцен и кадры в зумах
    s4 = secs.get(4, "")
    seen = Counter()
    for cells in rows(s4):
        if len(cells) == 3 and cells[1] in ROMAN:
            slot, act = cells[0].strip("`"), ROMAN[cells[1]]
            seen[(act, slot)] += 1
            if slot not in briefs[act]:
                err(f"§4.2: слота `{slot}` нет в ТЗ Акта {act}")
        elif len(cells) == 2 and SLOT.match(cells[0].strip("`")):
            if cells[0].strip("`") not in all_slots:
                err(f"§4.3: слота `{cells[0]}` нет в ТЗ")
        else:
            continue
        for tok in ticks(cells[-1]):
            if FILE.match(tok) and tok not in defs:
                err(f"§4: `{cells[0]}` ссылается на неопределённый `{tok}`")
    for act, brief in briefs.items():
        for slot in brief:
            if FRAME_SLOT.match(slot) and not seen[(act, slot)]:
                err(f"§4.2: нет кадра для `{slot}` (Акт {act})")
    for (act, slot), n in seen.items():
        if n > 1:
            err(f"§4.2: `{slot}` (Акт {act}) указан {n} раза")

    # 5. Портреты
    for emo in sorted(emotions):
        if f"port_{emo}.png" not in defs:
            err(f"нет портрета `port_{emo}.png` (эмоция из текстов)")
        if emo.startswith("lap_soap_"):
            for v in ("foam", "cap"):
                if f"port_{emo}_{v}.png" not in defs:
                    err(f"нет варианта пены `port_{emo}_{v}.png`")

    # 7. Документы
    s7 = secs.get(7, "")
    doc_rows = {}
    for cells in rows(s7):
        if len(cells) == 4 and cells[0].startswith("`DOC."):
            doc_rows[cells[0].strip("`")] = cells
            for tok in ticks(cells[2]) + ticks(cells[3]):
                if FILE.match(tok) and tok not in defs:
                    err(f"§7.2: `{cells[0]}` — неопределённый `{tok}`")
            if not any(FILE.match(t) for t in ticks(cells[2])):
                err(f"§7.2: `{cells[0]}` — не указан носитель")
    for d in sorted(docs - set(doc_rows)):
        err(f"§7.2: нет строки для документа `{d}`")
    for d in sorted(set(doc_rows) - docs):
        err(f"§7.2: `{d}` — такого документа нет в итоговых текстах")

    # 8. Шрифты
    have = {p.name for p in (ROOT / "assets" / "fonts").glob("*.ttf")}
    listed = set(by_class.get("font", []))
    for f in sorted(have - listed):
        err(f"§8: шрифт `{f}` лежит в assets/fonts, но не описан")
    for f in sorted(listed - have):
        err(f"§8: шрифт `{f}` описан, но его нет в assets/fonts")

    # 9. Звук: все слоты GDD §8
    s9 = secs.get(9, "")
    s9_slots = {t for t in ticks(s9) if SLOT.match(t)}
    for t in sorted(s9_slots - all_slots):
        err(f"§9: слота `{t}` нет в ТЗ")
    for need in sorted(gdd_sound_slots(all_slots)):
        if need.endswith(".*"):
            if not any(s.startswith(need[:-1]) for s in s9_slots):
                err(f"§9: нет звука для семейства `{need}` (GDD §8)")
        elif need not in s9_slots:
            err(f"§9: нет звука для `{need}` (GDD §8)")

    # 0. Итоги
    anc = [n for n in by_class.get("port", []) if n.startswith("port_anc_")]
    gfx = (len(by_class.get("room", [])) + len(by_class.get("zoom", [])) + len(by_class.get("cu", []))
           + len(by_class.get("fr", [])) + len(by_class.get("st", [])) + len(by_class.get("ov", []))
           + len(by_class.get("port", [])) - len(anc) + len(by_class.get("ic", []))
           + len(by_class.get("media", [])) + len(by_class.get("mark", [])) + len(by_class.get("ui", [])))
    snd = len(by_class.get("audio", []))
    m = re.search(r"Итого генерировать: \*\*графика (\d+) файл\w*, звук (\d+) файл\w*", text)
    if not m:
        err("§0: нет строки «Итого генерировать: **графика N файлов, звук M файлов.**»")
    elif (int(m.group(1)), int(m.group(2))) != (gfx, snd):
        err(f"§0: в итоге графика {m.group(1)}, звук {m.group(2)}; по таблицам — {gfx} и {snd}")

    counts = ", ".join(f"{c} {len(v)}" for c, v in by_class.items())
    print(f"файлов определено {len(defs)}: {counts}")
    print(f"генерировать: графика {gfx}, звук {snd}; кадров слотов {sum(seen.values())}, "
          f"документов {len(doc_rows)}, эмоций {len(emotions)}")
    for e in errors:
        print("ОШИБКА:", e)
    print("ИТОГ:", "ошибок нет" if not errors else f"ошибок {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
