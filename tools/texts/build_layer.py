#!/usr/bin/env python3
"""Весь текстовый слой игры одним файлом — для чтения и для другой нейросети.

Берёт итоговые файлы актов и их ТЗ. Перед репликами каждого слота — пояснение
строками `>` (парсер текстов их пропускает): когда звучит слот, что в нём
обязано быть, кто говорит, сколько реплик, обязательные строки из таблицы §7.2
ТЗ и строки автора, которые не менять (`texts/AUTHOR_LINES.json`). Реплики и
документы — как в итоговых файлах. Итоговый файл, не прошедший проверку по ТЗ
или потерявший строку автора, в слой не попадает.

Ответ другой нейросети в том же формате режется на акты (`split_acts`) по
заголовкам «# АКТ …»; каждый акт проверяется своим ТЗ и списком строк автора
(`check_locks`).

Запуск:
    python tools/texts/build_layer.py ВЫХОД.md ИТОГ.md ТЗ.md [ИТОГ.md ТЗ.md ...]
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_texts as ct  # noqa: E402
from build_compare import ROMAN, act_title, sections, strip_md  # noqa: E402

AUTHOR_LINES = ct.ROOT / "texts" / "AUTHOR_LINES.json"
SIGNATURE = ("подпись управляющего — две строки дословно: "
             "«Ваш комфорт — наша концепция.» / «Управляющий»")
SPEAKERS = [
    ("lap", "Лапидус"), ("iz", "Изольда Тихоновна"), ("anc", "Предок"),
    ("pa", "громкая связь (голос управляющего)"), ("paiz", "Изольда по громкой связи"),
    ("ans", "автоответчик"), ("guest", "гость"), ("guestf", "гостья"),
    ("waiter", "официант"), ("cap", "титр"), ("choice", "пункт меню"),
    ("ui", "надпись интерфейса"),
]
LOCK_TEXT = {
    "verbatim": "🔒 Строка автора — перенести дословно: «%s»",
    "part": "🔒 Добавка автора — сохранить дословно внутри реплики: «%s»",
    "joke": "🔒 Шутка автора — сохранить смысл и обе части, формулировку можно оживить: «%s»",
}


def author_lines(roman):
    data = json.loads(AUTHOR_LINES.read_text(encoding="utf-8"))
    return [e for e in data["lines"] if e["act"] == roman]


def check_locks(roman, texts):
    """Строки автора на месте: [(слот, сообщение)]. Шутку («joke») скрипт не
    проверяет — её сверяет глаз."""
    errs = []
    for e in author_lines(roman):
        slot = texts.get(e["slot"])
        if slot is None:
            errs.append((e["slot"], "слота нет, а в нём строка автора"))
            continue
        if e["speaker"] == "doc":
            ok = any(ct.same_line(l, e["text"]) for l in (slot["doc"] or []))
        elif e["kind"] == "part":
            ok = any(ct.norm_match(e["text"]) in ct.norm_match(l["text"])
                     for l in slot["lines"] if l["speaker"] == e["speaker"])
        elif e["kind"] == "verbatim":
            ok = any(ct.same_line(l["text"], e["text"])
                     for l in slot["lines"] if l["speaker"] == e["speaker"])
        else:
            continue
        if not ok:
            errs.append((e["slot"], "нет строки автора «%s»" % e["text"]))
    return errs


def fixed_rows(brief_path):
    """Таблица §7.2 ТЗ: [(слоты, где, требование)]; без слотов — на весь акт."""
    text = Path(brief_path).read_text(encoding="utf-8")
    start = text.find("\n### 7.2.")
    end = text.find("\n### 7.3.", start)
    rows = []
    for line in text[start:end].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 2 or cells[0] in ("Где", "") or set(cells[0]) <= set("-: "):
            continue
        slots = re.findall(r"`(" + ct.SLOT_ID + r")`", cells[0])
        where = cells[0]
        for sid in slots:
            where = where.replace("`%s`" % sid, "")
        where = strip_md(where).strip(" ,")
        req = re.sub(r"подпись управляющего §6\.\d+ — две строки дословно", SIGNATURE, cells[1])
        rows.append((slots, where, strip_md(req)))
    return rows


def range_text(spec):
    if spec["kind"] == "doc":
        return "документ, не длиннее %d строк" % spec["doc_max"]
    rng = (str(spec["min"]) if spec["min"] == spec["max"]
           else "%d–%d" % (spec["min"], spec["max"]))
    if spec["kind"] == "choice":
        return "первая строка — пункт меню (choice), затем реплик: %s" % rng
    return "реплик: %s" % rng


def line_text(l):
    return "%s | %s | %s | %s" % (l["speaker"], l["emotion"], ",".join(l["funcs"]), l["text"])


def build_act(final_path, brief_path):
    """Текст одного акта в формате слоя и его счётчики; ValueError при ошибках."""
    brief = ct.parse_brief(brief_path)
    act = ct.detect_act(brief_path)
    roman = ROMAN[act]
    texts, fmt = ct.parse_texts(final_path)
    errs, _, _ = ct.check(brief, texts, fmt, act)
    errs += check_locks(roman, texts)
    if errs:
        raise ValueError("%s не проходит проверку:\n  %s" % (
            final_path, "\n  ".join("%s: %s" % (s or "файл", m) for s, m in errs)))
    secs = sections(brief_path)
    rows = fixed_rows(brief_path)
    locks = {}
    for e in author_lines(roman):
        locks.setdefault(e["slot"], []).append(LOCK_TEXT[e["kind"]] % e["text"])
    out = ["# АКТ %s «%s»" % (roman, act_title(brief_path)), ""]
    whole = ["> На весь акт — %s: %s" % (where, req) for slots, where, req in rows if not slots]
    if whole:
        out += whole + [""]
    cur_sec = None
    n_lines = n_docs = 0
    for sid, spec in brief.items():
        if secs.get(sid) != cur_sec:
            cur_sec = secs.get(sid)
            out += ["## %s" % cur_sec, ""]
        slot = texts[sid]
        out.append("### %s" % sid)
        if spec["star"]:
            out.append("> ★ ключевой слот")
        out.append("> Когда: %s" % strip_md(spec["when"]))
        out.append("> Обязано быть: %s" % strip_md(spec["must"]))
        if spec["kind"] == "doc":
            out.append("> Форма: %s" % range_text(spec))
        else:
            out.append("> Говорят: %s · %s" % (", ".join(sorted(spec["speakers"])), range_text(spec)))
        for slots, where, req in rows:
            if sid in slots:
                out.append("> Обязательно%s: %s" % (" (%s)" % where if where else "", req))
        out += ["> " + l for l in locks.get(sid, [])]
        if slot["doc"] is not None:
            doc = list(slot["doc"])
            while doc and not doc[-1].strip():
                doc.pop()
            out += ["```text"] + doc + ["```"]
            n_docs += 1
        if slot["silence"]:
            out.append("silence")
        out += [line_text(l) for l in slot["lines"]]
        n_lines += len(slot["lines"])
        out.append("")
    out += ["КОНЕЦ АКТА %s" % roman, ""]
    return {"roman": roman, "title": act_title(brief_path), "final": str(final_path),
            "slots": len(brief), "lines": n_lines, "docs": n_docs,
            "locks": sum(len(v) for v in locks.values()), "text": "\n".join(out)}


def header(acts):
    names = ", ".join("`%s`" % Path(a["final"]).resolve().relative_to(ct.ROOT).as_posix() for a in acts)
    span = "%s–%s" % (acts[0]["roman"], acts[-1]["roman"]) if len(acts) > 1 else acts[0]["roman"]
    out = [
        "# «Латунный янычар: Гидроудар» — текстовый слой, Акты %s" % span,
        "",
        "Все тексты игры, которые уже написаны: реплики, титры, пункты меню, советы предка, документы. Акт IV ещё не написан.",
        "",
        "Собрано `tools/texts/build_layer.py` из итоговых файлов актов (%s) и их ТЗ. Руками не править: правки вносятся в итоговые файлы, затем сборка заново." % names,
        "",
        "## Как читать",
        "",
        "- `# АКТ …` — начало акта, `КОНЕЦ АКТА …` — его конец; `## …` — место или сцена.",
        "- `### ID` — слот: одно место в игре, где звучит текст.",
        "- Строки, которые начинаются с `>`, — пояснение к слоту, в игре их нет: когда звучит слот, что в нём обязано быть, кто говорит и сколько реплик. «Обязательно» — строка, которую требует ТЗ акта. 🔒 — строка автора игры.",
        "- Реплика: `говорящий | эмоция | функции | текст`. Документ — блок между строками ```` ```text ```` и ```` ``` ````.",
        "- Говорящие: %s." % "; ".join("`%s` — %s" % s for s in SPEAKERS),
        "- Функции реплики: `PLOT` — двигает сюжет, `STATE` — сообщает, что изменилось, `CLUE` — улика, `CHAR` — характер, `RHYTHM` — темп, `JOKE` — шутка.",
        "",
        "| Акт | Слотов | Реплик | Документов | Строк автора |",
        "|---|---|---|---|---|",
    ]
    for a in acts:
        out.append("| %s «%s» | %d | %d | %d | %d |" % (a["roman"], a["title"], a["slots"],
                                                       a["lines"], a["docs"], a["locks"]))
    out += ["", "---", "", ""]
    return "\n".join(out)


def build(pairs):
    acts = [build_act(f, b) for f, b in pairs]
    return header(acts) + "\n".join(a["text"] for a in acts), acts


START = re.compile(r"^\W*#\W*АКТ\s+(IV|I{1,3})\b")
END = re.compile(r"^\W*КОНЕЦ АКТА\s+(IV|I{1,3})\b")


def split_acts(text):
    """Текст в формате слоя → {«I»: текст акта, …}. Акт начинается заголовком
    «# АКТ I …» и идёт до «КОНЕЦ АКТА I» или до следующего заголовка акта;
    повторный заголовок того же акта (после обрыва ответа) дописывает его."""
    acts, cur = {}, None
    for line in text.splitlines():
        m = START.match(line)
        if m:
            cur = m.group(1)
            acts.setdefault(cur, [])
        if cur is not None:
            acts[cur].append(line)
            m = END.match(line)
            if m and m.group(1) == cur:
                cur = None
    return {k: "\n".join(v) + "\n" for k, v in acts.items()}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 3 or len(argv) % 2 == 0:
        print(__doc__)
        return 2
    try:
        text, acts = build(list(zip(argv[1::2], argv[2::2])))
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    Path(argv[0]).write_text(text, encoding="utf-8")
    for a in acts:
        print("Акт %s «%s»: слотов %d, реплик %d, документов %d, строк автора %d"
              % (a["roman"], a["title"], a["slots"], a["lines"], a["docs"], a["locks"]))
    print("Слой: %s (%d знаков)" % (argv[0], len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
