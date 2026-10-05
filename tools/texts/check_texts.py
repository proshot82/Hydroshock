#!/usr/bin/env python3
"""Проверка текстов акта по ТЗ (texts/actN/BRIEF_ACTN_TEXTS.md; акт — по заголовку ТЗ).

Список слотов, допустимые спикеры и число реплик берутся из таблиц §9 ТЗ.
Фиксированные строки и запреты — из §5 и §7 ТЗ (продублированы ниже,
при правке ТЗ править и здесь).

Запуск:
    python tools/texts/check_texts.py texts/act1/ACT1_TEXTS_CLAUDE.md
    python tools/texts/check_texts.py texts/act2/ACT2_TEXTS_CLAUDE.md --brief texts/act2/BRIEF_ACT2_TEXTS.md
    python tools/texts/check_texts.py ФАЙЛ --json разбор.json

Код выхода: 0 — ошибок нет, 1 — есть ошибки, 2 — файл не прочитан.
Только стандартная библиотека Python 3.8+.
"""

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BRIEF = ROOT / "texts" / "act1" / "BRIEF_ACT1_TEXTS.md"

SLOT_ID = r"[A-Z][A-Z0-9]*(?:\.[A-Za-z0-9_]+)+"

# --- §5 ТЗ: спикеры и эмоции -------------------------------------------------

EMOTIONS = {
    "lap": {"lap_soap_neutral", "lap_soap_tired", "lap_soap_worried",
            "lap_soap_ashamed", "lap_soap_angry", "lap_soap_smug",
            "lap_soap_inspired", "lap_soap_panic", "lap_soap_triumphant"},
    "iz": {"iz_formal", "iz_averted", "iz_tired", "iz_stern", "iz_flustered"},
    "anc": {"anc_calm", "anc_stern", "anc_proud", "anc_smug"},
}
VOICE_SPEAKERS = {"pa", "ans", "guest", "guestf", "waiter", "cap", "choice", "ui"}
ALL_SPEAKERS = set(EMOTIONS) | VOICE_SPEAKERS
FUNCTIONS = {"CLUE", "STATE", "CHAR", "PLOT", "RHYTHM", "JOKE"}
HINT_LEVEL_EMOTION = {"1": "anc_calm", "2": "anc_stern", "3": "anc_smug"}

# --- §7.1 ТЗ: длины ---------------------------------------------------------

MAX_LEN = {"lap": 160, "iz": 200, "anc": 160, "pa": 220, "ans": 140,
           "guest": 140, "guestf": 140, "waiter": 140, "cap": 140,
           "choice": 40, "ui": 12}

# --- §7.2 ТЗ: фиксированные строки -------------------------------------------

OWNER_STARS = ("Сраный отдел кадров. Вот тебе, мол, Лапидус, отель тире четыре "
               "звезды. А это не тире, это МИНУС четыре звезды.")
VOUCHER_LINE = "Отель „Каскад“ — четыре звезды"
ANSWERING = "Спасибо! Ваше мнение очень важно для нас, оставайтесь на линии."
MINERAL = "Вода питьевая очищенная, по мотивам исторической рецептуры"
POT = "Осторожно, горячо!"
HOT = "Осторожно, горячее!"
STAFF_WORD = r"обслуживани|обслуживающ\w* персонал"

# --- §7.3 ТЗ: запреты -------------------------------------------------------
# Шаблоны применяются к тексту после norm_match(): нижний регистр, ё → е.

BANNED_COMMON = [
    (r"гидрофор", "техжаргон «гидрофор»"),
    (r"мембран", "техжаргон «мембрана»"),
    (r"предзаряд", "техжаргон «предзарядка»"),
    (r"\bстояк", "техжаргон «стояк»"),
    (r"\bфитинг", "сантехнический жаргон «фитинг»"),
    (r"\bсгон(?:а|ы|ом|ов|у)?\b", "сантехнический жаргон «сгон»"),
    (r"\bобратк", "сантехнический жаргон «обратка»"),
    (r"контргайк", "сантехнический жаргон «контргайка»"),
    (r"\bбайпас", "сантехнический жаргон «байпас»"),
    (r"фхтагн", "лавкрафтиана «фхтагн»"),
    (r"\bр['’ʼ]?льех", "лавкрафтиана «Р'льех»"),
    (r"некрономикон", "лавкрафтиана «Некрономикон»"),
    (r"аркх[эе]м", "лавкрафтиана «Аркхэм»"),
    (r"кухтулх", "раньше времени: «Кухтулху»"),
    (r"ктулх", "раньше времени: «Ктулху»"),
    (r"щупальц", "раньше времени: «щупальца»"),
    (r"задолженност", "раньше времени: «задолженность»"),
]
BANNED_BY_ACT = {
    1: [
        (r"старш\w* по вод", "раньше времени: «старший по воде»"),
        (r"подношени", "раньше времени: «подношение»"),
        (r"до выяснения", "раньше времени: «до выяснения» (формула Кухтулху)"),
    ],
    2: [
        (r"\bдолг(?:а|у|ом|и|ов|е)?\b", "раньше времени: «долг»"),
        (r"\bпени\b", "раньше времени: «пени»"),
        (r"я держала стремянку", "owner-canon Акта III: «Я держала стремянку»"),
    ],
}
BANNED = BANNED_COMMON + BANNED_BY_ACT[1]   # Акт I — как было

# Акт II: два прочтения (подношение или оплата) живут до P12 — оба слова
# звучат только вместе, в итоговой реплике акта (ТЗ Акта II §7.3).
ACT2_READINGS = [(r"оплат", "«оплата»"), (r"подношени", "«подношение»")]
ACT2_READINGS_SLOT = "END.act2"

# Решения автора 04.10.2026: «по правилам тона — всё можно, лишь бы было
# остроумно и смешно», но «ломка четвёртой стены — нет». Поэтому мат сверх
# ориентира — предупреждение (судит автор), а четвёртая стена — ошибка.
# Ошибками остаются и локи канона, знание героя, производственный формат.
FOURTH_WALL = [
    (r"\bигрок", "«игрок»"),
    (r"\bкурсор", "«курсор»"),
    (r"\bсохранени", "«сохранение»"),
    (r"\bквест", "«квест»"),
    (r"\bразработчик", "«разработчик»"),
    (r"\bсценари", "«сценарий»"),
    (r"\bкликн", "«кликнуть»"),
]
NO_MAT_SPEAKERS = {"kuh"}   # канон, лок 4: Кухтулху не матерится никогда

# «инвентарь» в мире — гостиничный («мягкий инвентарь», «инвентарный номер»);
# у героя и Предка это может быть четвёртая стена — только предупреждение.
INVENTORY_WORD = r"\bинвентар(?:ь|я|ю|ем|е)\b"   # существительное; «инвентарный номер» — слово мира
INVENTORY_SPEAKERS = {"lap", "anc"}

KEFIR_OK = {"DOC.menu", "Z02.menu.take", "INV.menu.look"}

ETO_NE_ETO = r"\bэто\s+не\b[^.!?…]*?,\s*(?:а\s+)?это\b"

MAT = [
    r"\bху[йяеиюё]",
    r"пизд",
    r"\bбля(?!х)",
    r"\b(?:за|по|на|вы|у|от|об|обо|пере|при|до|раз|рас|недо|подъ|съ|въ)?ъ?е"
    r"б(?:а|у|е|л|н|и|ш|т|ь|о)",
    r"\bмуд(?:ак|ил|оз|охал)",
    r"\bпид(?:о|а)?р",
    r"залуп",
    r"гандон",
    r"\bсук(?:а|и|у|ой)\b",
]

IZ_FIRST_PERSON = (r"\b(?:я|мне|меня|мной|мною|мой|моя|мое|мои|моего|моей|моих|"
                   r"моим|моими|моему|моем)\b")
IZ_BANNED = [(r"одновременн", "«одновременно»"), (r"сигнал", "«сигнал»")]
PA_BANNED = [(r"авари", "«авария»"), (r"нет воды", "«нет воды»")]
PA_REQUIRED = r"планов\w* улучшени"
MAX_GUEST_LINES = 8
MAX_MAT = 2


# --- нормализация -----------------------------------------------------------

def norm_typo(text):
    """Типографика к одному виду (для слепого сравнения и сверки строк)."""
    t = text.strip()
    t = t.replace("...", "…")
    t = re.sub(r"\s+[-–—]{1,2}\s+", " — ", t)
    t = re.sub(r"^[-–—]{1,2}\s+", "— ", t)
    # прямые и английские кавычки → ёлочки, внутренние → лапки
    out, depth = [], 0
    for i, ch in enumerate(t):
        if ch in "\"“”«»„":
            if ch == "«" or ch == "„":
                opening = True
            elif ch == "»":
                opening = False
            else:
                prev = t[i - 1] if i else " "
                opening = prev.isspace() or prev in "([—–-"
                if ch == "“" and depth >= 2:
                    opening = False
            if opening:
                out.append("«" if depth == 0 else "„")
                depth += 1
            else:
                depth = max(depth - 1, 0)
                out.append("»" if depth == 0 else "“")
        else:
            out.append(ch)
    t = "".join(out)
    return re.sub(r"[ \t]+", " ", t)


def norm_match(text, keep_case=False):
    t = norm_typo(text)
    if not keep_case:
        t = t.lower()
    t = t.replace("ё", "е").replace("Ё", "Е")
    t = re.sub(r"[«»„“\"”]", '"', t)
    return t


def same_line(text, fixed):
    """Реплика совпадает с фиксированной строкой: буквы и регистр — точно,
    типографика, ё/е и знак в конце — свободно."""
    def core(x):
        return norm_match(x, keep_case=True).rstrip(" .!…")
    return core(text) == core(fixed)


# --- разбор ТЗ --------------------------------------------------------------

def parse_range(cell):
    cell = cell.strip()
    m = re.match(r"док\s*≤\s*(\d+)", cell)
    if m:
        return {"kind": "doc", "doc_max": int(m.group(1)), "min": 0, "max": 0}
    choice = cell.startswith("метка")
    if choice:
        cell = cell.split("+", 1)[1] if "+" in cell else "0"
    m = re.match(r"(\d+)\s*(?:[–-]\s*(\d+))?$", cell.strip())
    if not m:
        raise ValueError("не разобран диапазон реплик: %r" % cell)
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) else lo
    return {"kind": "choice" if choice else "lines", "min": lo, "max": hi}


def parse_brief(path):
    text = Path(path).read_text(encoding="utf-8")
    start = text.find("\n## 9. Слоты")
    end = text.find("\n## 10.", start)
    if start < 0 or end < 0:
        raise ValueError("в ТЗ не найден раздел «## 9. Слоты»")
    slots = OrderedDict()
    row = re.compile(r"^\|\s*`(" + SLOT_ID + r")`\s*\|(.*)\|\s*$")
    for line in text[start:end].splitlines():
        m = row.match(line)
        if not m:
            continue
        sid = m.group(1)
        cells = [c.strip() for c in m.group(2).split("|")]
        if len(cells) != 5:
            raise ValueError("слот %s: ожидалось 6 колонок" % sid)
        star, when, must, who, count = cells
        spec = parse_range(count)
        spec.update({
            "star": star == "★",
            "when": when,
            "must": must,
            "speakers": set(re.findall(r"`([a-z]+)`", who)),
        })
        if sid in slots:
            raise ValueError("слот %s повторяется в ТЗ" % sid)
        slots[sid] = spec
    if not slots:
        raise ValueError("в §9 ТЗ не найдено ни одного слота")
    return slots


# --- разбор текстов ---------------------------------------------------------

def parse_texts(path):
    """Возвращает (слоты, ошибки формата)."""
    raw = Path(path).read_text(encoding="utf-8-sig")
    slots = OrderedDict()
    errors = []
    head = re.compile(r"^#{2,4}\s*`?(" + SLOT_ID + r")`?\s*$")
    cur = None
    in_doc = False
    for no, line in enumerate(raw.splitlines(), 1):
        s = line.strip()
        m = head.match(s)
        if m and not in_doc:
            sid = m.group(1)
            if sid in slots:
                errors.append((sid, "слот повторяется (строка %d)" % no))
            cur = slots.setdefault(sid, {"lines": [], "doc": None,
                                         "silence": False, "line_no": no})
            continue
        if cur is None:
            continue
        if s.startswith("```"):
            if in_doc:
                in_doc = False
            else:
                in_doc = True
                if cur["doc"] is None:
                    cur["doc"] = []
            continue
        if in_doc:
            cur["doc"].append(line.rstrip())
            continue
        if not s or s == "---" or s.startswith("## ") or s.startswith("# "):
            continue
        if s == "ПРОДОЛЖЕНИЕ СЛЕДУЕТ" or re.match(r"^КОНЕЦ АКТА [IV]+$", s):
            cur = None
            continue
        if s.startswith(">"):          # пояснение к слоту: источник, причина правки
            continue
        s = re.sub(r"^[-*]\s+", "", s).strip("*` ")
        if s.lower() == "silence":
            cur["silence"] = True
            continue
        parts = [p.strip() for p in s.split("|", 3)]
        if len(parts) != 4:
            errors.append((None, "строка %d не по формату: %s" % (no, s[:70])))
            continue
        speaker, emotion, funcs, txt = parts
        cur["lines"].append({
            "speaker": speaker, "emotion": emotion, "text": txt,
            "funcs": [f.strip().upper() for f in re.split(r"[,\s]+", funcs)
                      if f.strip()],
            "line_no": no,
        })
    if in_doc and cur is not None and cur["doc"] == []:
        cur["doc"] = None
    elif in_doc:
        errors.append((None, "документ не закрыт строкой ``` в конце файла"))
    return slots, errors


# --- проверки ---------------------------------------------------------------

def check(brief, texts, fmt_errors, act=1):
    errs, warns = [], []
    banned = BANNED_COMMON + BANNED_BY_ACT[act]

    def err(sid, msg):
        errs.append((sid, msg))

    def warn(sid, msg):
        warns.append((sid, msg))

    for sid, msg in fmt_errors:
        err(sid, msg)

    for sid in brief:
        if sid not in texts:
            err(sid, "слот отсутствует")
    for sid in texts:
        if sid not in brief:
            err(sid, "лишний слот, в ТЗ его нет")
    order = [s for s in texts if s in brief]
    if order != [s for s in brief if s in texts]:
        warn(None, "порядок слотов отличается от §9 ТЗ")

    mat_hits = []
    guest_lines = 0
    pa_texts = []
    for sid, slot in texts.items():
        spec = brief.get(sid)
        if spec is None:
            continue
        lines = slot["lines"]
        if spec["kind"] == "doc":
            if slot["doc"] is None:
                err(sid, "нужен документ в блоке ```text … ```")
            else:
                body = [ln for ln in slot["doc"] if ln.strip()]
                if len(body) > spec["doc_max"]:
                    err(sid, "документ длиннее %d строк (%d)"
                        % (spec["doc_max"], len(body)))
                if not body:
                    err(sid, "документ пуст")
            if lines or slot["silence"]:
                err(sid, "в слоте документа лишние реплики")
        else:
            if slot["doc"] is not None:
                err(sid, "документ в слоте, где нужны реплики")
            n = len(lines)
            if spec["kind"] == "choice":
                if not lines or lines[0]["speaker"] != "choice":
                    err(sid, "первая строка должна быть пунктом меню (choice)")
                else:
                    n -= 1
                if any(l["speaker"] == "choice" for l in lines[1:]):
                    err(sid, "пункт меню (choice) только первой строкой")
            elif any(l["speaker"] == "choice" for l in lines):
                err(sid, "пункт меню (choice) в слоте без выбора")
            if slot["silence"]:
                if lines:
                    err(sid, "silence вместе с репликами")
                elif spec["min"] > 0:
                    err(sid, "тишина недопустима: нужно не меньше %d реплик"
                        % spec["min"])
            elif not spec["min"] <= n <= spec["max"]:
                rng = (str(spec["min"]) if spec["min"] == spec["max"]
                       else "%d–%d" % (spec["min"], spec["max"]))
                err(sid, "реплик %d, а по ТЗ %s" % (n, rng))

        for ln in lines:
            sp, em, txt = ln["speaker"], ln["emotion"], ln["text"]
            where = "строка %d" % ln["line_no"]
            if sp not in ALL_SPEAKERS:
                err(sid, "%s: неизвестный спикер %r" % (where, sp))
                continue
            if sp not in spec["speakers"]:
                err(sid, "%s: спикер %s в этом слоте не разрешён (можно: %s)"
                    % (where, sp, ", ".join(sorted(spec["speakers"]))))
            if sp in EMOTIONS:
                if em not in EMOTIONS[sp]:
                    err(sid, "%s: эмоция %r не из реестра %s" % (where, em, sp))
            elif em != "none":
                err(sid, "%s: у голоса %s эмоция должна быть none" % (where, sp))
            if sid.startswith("HINT.") and sid.rsplit(".", 1)[-1] in HINT_LEVEL_EMOTION:
                need = HINT_LEVEL_EMOTION[sid.rsplit(".", 1)[-1]]
                if em != need:
                    err(sid, "%s: ступень подсказки требует %s" % (where, need))
            bad = [f for f in ln["funcs"] if f not in FUNCTIONS]
            if bad:
                err(sid, "%s: неизвестные функции %s" % (where, ", ".join(bad)))
            if not ln["funcs"]:
                err(sid, "%s: нет функций" % where)
            elif set(ln["funcs"]) <= {"JOKE"}:
                err(sid, "%s: строка только с JOKE запрещена" % where)
            if not txt:
                err(sid, "%s: пустой текст" % where)
            owner = act == 1 and sid == "Z03.stars.look" and same_line(txt, OWNER_STARS)
            if len(txt) > MAX_LEN[sp] and not owner:
                err(sid, "%s: %d знаков, предел для %s — %d"
                    % (where, len(txt), sp, MAX_LEN[sp]))
            if sp == "ui" and txt != txt.upper():
                err(sid, "%s: надпись интерфейса — заглавными" % where)
            if sp == "waiter" and not same_line(txt, HOT):
                err(sid, "%s: официант говорит только «%s»" % (where, HOT))
            if sp in ("guest", "guestf"):
                guest_lines += 1
            if sp == "pa":
                pa_texts.append(txt)
            low = norm_match(txt)
            if sp == "iz":
                if re.search(IZ_FIRST_PERSON, low):
                    err(sid, "%s: у Изольды до Акта III нет «я»: %s" % (where, txt))
                for pat, name in IZ_BANNED:
                    if re.search(pat, low):
                        err(sid, "%s: Изольда не говорит %s" % (where, name))
            if sp == "pa":
                for pat, name in PA_BANNED:
                    if re.search(pat, low):
                        err(sid, "%s: громкая связь не говорит %s" % (where, name))
            if sp in INVENTORY_SPEAKERS and re.search(INVENTORY_WORD, low):
                warn(sid, "%s: «инвентарь» у %s — не четвёртая ли стена? %s"
                     % (where, sp, txt))
            if not owner and re.search(ETO_NE_ETO, low):
                err(sid, "%s: конструкция «это не …, это …» вне owner-canon"
                    % where)
            for pat in MAT:
                for m in re.finditer(pat, low):
                    mat_hits.append((sid, sp, m.group(0), ln["line_no"]))

        texts_all = [l["text"] for l in lines]
        if slot["doc"]:
            texts_all += slot["doc"]
        for txt in texts_all:
            low = norm_match(txt)
            for pat, name in banned:
                if re.search(pat, low):
                    err(sid, "запрет — %s: %s" % (name, txt.strip()[:80]))
            for pat, name in FOURTH_WALL:
                if re.search(pat, low):
                    err(sid, "четвёртая стена — %s (запрет автора): %s" % (name, txt.strip()[:80]))
            if act == 1 and "кефир" in low and sid not in KEFIR_OK:
                err(sid, "«кефир» вне разрешённых слотов: %s" % txt.strip()[:80])
            if act >= 2 and re.search(r"[a-z]{2,}", low):
                err(sid, "английское слово (решение автора — английских слов в игре нет): %s"
                    % txt.strip()[:80])
            if act == 2 and sid != ACT2_READINGS_SLOT:
                for pat, name in ACT2_READINGS:
                    if re.search(pat, low):
                        err(sid, "%s — только в %s, вместе со вторым прочтением: %s"
                            % (name, ACT2_READINGS_SLOT, txt.strip()[:80]))
            if slot["doc"] and txt in slot["doc"]:
                for pat in MAT:
                    if re.search(pat, low):
                        warn(sid, "мат в документе: %s" % txt.strip()[:80])

    # фиксированные строки
    def lines_of(sid, speaker=None):
        return [l["text"] for l in texts.get(sid, {}).get("lines", [])
                if speaker is None or l["speaker"] == speaker]

    def require(sid, cond, msg):
        if sid in texts and not cond:
            err(sid, msg)

    if act == 1:
        require("Z03.stars.look",
                any(same_line(t, OWNER_STARS) for t in lines_of("Z03.stars.look", "lap")),
                "нет owner-canon реплики дословно одной репликой")
        doc_v = (texts.get("DOC.voucher") or {}).get("doc") or []
        require("DOC.voucher",
                any(norm_match(VOUCHER_LINE) in norm_match(l) for l in doc_v),
                "нет строки «%s»" % VOUCHER_LINE)
        require("Z02.phone.call",
                any(same_line(t, ANSWERING) for t in lines_of("Z02.phone.call", "ans")),
                "нет строки автоответчика дословно")
        ans_n = len(lines_of("Z02.phone.call", "ans"))
        if "Z02.phone.call" in texts and ans_n > 2:
            err("Z02.phone.call", "у автоответчика больше двух реплик (%d)" % ans_n)
        require("Z02.mineral.look",
                any(norm_match(MINERAL) in norm_match(t) for t in lines_of("Z02.mineral.look")),
                "нет строки этикетки «%s»" % MINERAL)
        require("Z03.pot.look",
                any(norm_match(POT) in norm_match(t) for t in lines_of("Z03.pot.look")),
                "нет надписи «%s»" % POT)
        require("SEQ.peek.4_waiter",
                any(same_line(t, HOT) for t in lines_of("SEQ.peek.4_waiter", "waiter")),
                "нет фразы официанта «%s»" % HOT)
        require("SEQ.shout.1",
                any(same_line(t, HOT) for t in lines_of("SEQ.shout.1", "lap")),
                "нет крика «%s» отдельной репликой" % HOT)
        # «обслуживание» в ТЗ v1; решение автора 04.10.2026 — «обслуживающий персонал»
        require("SEQ.shout.4",
                any(re.search(STAFF_WORD, norm_match(t)) for t in lines_of("SEQ.shout.4", "iz")),
                "Изольда не называет его обслуживающим персоналом")
        require("TALK.iz.open",
                any("во всем здании" in norm_match(t) for t in lines_of("TALK.iz.open", "iz")),
                "Изольда не говорит «во всём здании»")
    else:
        check_act2_fixed(texts, lines_of, require, err)
    if texts and not any(re.search(PA_REQUIRED, norm_match(t)) for t in pa_texts):
        err(None, "громкая связь ни разу не сказала «плановые улучшения»")
    if guest_lines > MAX_GUEST_LINES:
        err(None, "реплик гостей %d, предел %d" % (guest_lines, MAX_GUEST_LINES))

    real_mat = [h for h in mat_hits]
    if len(real_mat) > MAX_MAT:
        warn(None, "мат: %d случаев, ориентир %d — ударение, а не фон" % (len(real_mat), MAX_MAT))
    for sid, sp, word, no in real_mat:
        if sp in NO_MAT_SPEAKERS:
            err(sid, "мат у %s (строка %d): %s — лок канона" % (sp, no, word))
        elif sp != "lap":
            warn(sid, "мат у %s (строка %d): %s" % (sp, no, word))

    # подпись управляющего: общая строка в меню и объявлении
    menu = [l.strip() for l in (texts.get("DOC.menu") or {}).get("doc") or [] if l.strip()]
    bath = [l.strip() for l in (texts.get("DOC.bathday") or {}).get("doc") or [] if l.strip()]
    if act == 1 and menu and bath:
        common = {norm_match(l) for l in menu} & {norm_match(l) for l in bath}
        if not any(len(c) >= 8 for c in common):
            warn("DOC.menu", "нет общей строки-подписи в DOC.menu и DOC.bathday")

    stats = {"slots": len([s for s in texts if s in brief]),
             "lines": sum(len(t["lines"]) for t in texts.values()),
             "mat": len(real_mat), "guest_lines": guest_lines}
    return errs, warns, stats


# --- Акт II: фиксированные строки (ТЗ Акта II §7.2) -------------------------

MANAGER_SIGNATURE = ["Ваш комфорт — наша концепция.", "Управляющий"]
ACT2_LINE_RULES = [
    # (слот, спикер, обязательные подстроки)
    ("OPEN.requests", "ans", ["заявка принята, ожидайте"]),
    ("OPEN.pa", "pa", ["душевой комфорт", "водный акцент холла", "текстильная забота"]),
    ("TALK.iz.vitrine", "iz", ["не запирается"]),
    ("TALK.iz.layoff", "iz", ["поставщик"]),
    ("TALK.iz.ladder", "iz", ["стремянк"]),
]
ACT2_DOC_RULES = [
    # (слот, обязательные подстроки, точные строки)
    ("DOC.plate_k", [], ["Старший по воде — тов. К."]),
    ("DOC.notice_counter", ["[оттиск]"], ["Подача приостановлена до выяснения"]),
    ("DOC.notice_door", ["[оттиск]"], ["Подача приостановлена до выяснения",
                                       "Приём — в установленном порядке"]),
    ("DOC.exhibit", ["не трогать"], []),
    ("DOC.journal", ["принялъ", "[оттиск]"], []),
    ("DOC.instr1908", [], ["Передъ пускомъ — доложиться старшему по водѣ"]),
    ("DOC.memo", [], ["Перед пуском уведомить ответственное лицо"]),
    ("DOC.layoff", ["избыточных ритуалов", "не передавать"], []),
    ("DOC.paint_act", ["табличка", "и. т."], []),
    ("DOC.photo", ["четвергъ"], []),
    ("DOC.token", ["на одно погруженiе"], []),
    ("DOC.map_hotel", ["зал прекраснодушия"], []),
    ("DOC.map_1908", ["пріёмный пунктъ", "залъ водолѣченія"], []),
    ("DOC.map_soviet", ["зал оздоровления"], []),
]
ACT2_SIGNED = ["DOC.layoff", "DOC.exhibit", "DOC.regulation"]


def check_act2_fixed(texts, lines_of, require, err):
    for sid, sp, subs in ACT2_LINE_RULES:
        got = [norm_match(t) for t in lines_of(sid, sp)]
        for sub in subs:
            require(sid, any(norm_match(sub) in g for g in got),
                    "нет «%s» в реплике %s" % (sub, sp))
    got = [norm_match(t) for t in lines_of("TALK.iz.key", "iz")]
    require("TALK.iz.key", any(re.search(r"обслуживающ\w* персонал", g) for g in got),
            "Изольда не называет его обслуживающим персоналом")
    ans_n = len(lines_of("OPEN.requests", "ans"))
    if "OPEN.requests" in texts and ans_n > 2:
        err("OPEN.requests", "у автоответчика больше двух реплик (%d)" % ans_n)
    for sid, subs, exact in ACT2_DOC_RULES:
        doc = [l for l in ((texts.get(sid) or {}).get("doc") or []) if l.strip()]
        joined = norm_match("\n".join(doc))
        for sub in subs:
            require(sid, norm_match(sub) in joined, "в документе нет «%s»" % sub)
        for line in exact:
            # нумерация пункта («2. …») строку не портит
            require(sid, any(same_line(re.sub(r"^\s*\d+[.)]\s*", "", l), line) for l in doc),
                    "нет строки «%s» отдельной строкой" % line)
    for sid in ACT2_SIGNED:
        doc = [l.strip() for l in ((texts.get(sid) or {}).get("doc") or []) if l.strip()]
        ok = len(doc) >= 2 and same_line(doc[-2], MANAGER_SIGNATURE[0]) \
            and same_line(doc[-1], MANAGER_SIGNATURE[1])
        require(sid, ok, "в конце нет подписи управляющего (две строки дословно)")
    end = [norm_match(t) for t in lines_of("END.act2")]
    for pat, name in ACT2_READINGS:
        require("END.act2", any(re.search(pat, g) for g in end),
                "в итоге акта нет %s: два прочтения звучат вместе" % name)


def detect_act(brief_path):
    head = Path(brief_path).read_text(encoding="utf-8").splitlines()[0]
    m = re.search(r"Акта\s+([IV]+)\b", head)
    return {"I": 1, "II": 2}.get(m.group(1), 1) if m else 1


def to_json(texts):
    out = OrderedDict()
    for sid, slot in texts.items():
        out[sid] = {
            "silence": slot["silence"],
            "doc": [norm_typo(l) for l in slot["doc"]] if slot["doc"] is not None else None,
            "lines": [{"speaker": l["speaker"], "emotion": l["emotion"],
                       "function": l["funcs"], "text": norm_typo(l["text"])}
                      for l in slot["lines"]],
        }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Проверка текстов акта по ТЗ")
    ap.add_argument("texts", help="файл текстов в формате §8 ТЗ")
    ap.add_argument("--brief", default=str(DEFAULT_BRIEF), help="файл ТЗ")
    ap.add_argument("--json", help="записать разобранные тексты в JSON")
    args = ap.parse_args(argv)
    try:
        brief = parse_brief(args.brief)
        texts, fmt_errors = parse_texts(args.texts)
    except (OSError, ValueError) as e:
        print("Не прочитано: %s" % e)
        return 2
    errs, warns, stats = check(brief, texts, fmt_errors, detect_act(args.brief))
    print("Файл: %s" % args.texts)
    print("Слотов в ТЗ: %d; заполнено: %d; реплик: %d; мат: %d; реплик гостей: %d"
          % (len(brief), stats["slots"], stats["lines"], stats["mat"],
             stats["guest_lines"]))
    for sid, msg in errs:
        print("  ✗ %s%s" % ((sid + ": ") if sid else "", msg))
    for sid, msg in warns:
        print("  ! %s%s" % ((sid + ": ") if sid else "", msg))
    if args.json:
        Path(args.json).write_text(
            json.dumps(to_json(texts), ensure_ascii=False, indent=1),
            encoding="utf-8")
    if errs:
        print("Итог: ошибок %d, предупреждений %d." % (len(errs), len(warns)))
        return 1
    print("Итог: ошибок нет, предупреждений %d." % len(warns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
