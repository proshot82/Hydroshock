#!/usr/bin/env python3
"""Итоговая версия текстов акта: голоса слепого сравнения плюс правки.

Для каждого слота ТЗ, по порядку:
  1. слот есть в файле правок → он целиком (строки автора, стыковка);
  2. автор выбрал вариант Claude или другой нейросети → этот вариант;
  3. голоса нет, а одна версия нарушила жёсткое правило ТЗ → другая
     (по ТЗ такой слот проигран автоматически);
  4. голоса нет → версия по умолчанию: первый файл (`--default claude`) или
     второй (`--default other`); такие слоты перечисляются в отчёте.
Под заголовком каждого слота пишется строка «> …» — откуда он взят.

Выход генерируется: руками его не править, правки — в файле правок.

Запуск:
    python tools/texts/merge_texts.py [--brief ТЗ.md] [--names "подпись A,подпись B"]
        [--default claude|other] [--note "абзац в шапку"] A.md B.md VOTES.json EDITS.md FINAL.md

ТЗ по умолчанию — Акт I; акт и его правила проверки определяются по ТЗ.
Подписи версий (`--names`) идут в строки «> …» и в шапку; без них — «версия
Claude» и «версия другой нейросети». Раунд доработки 06.10.2026: A — прежний
итог (`ACTN_TEXTS_FINAL_v1.md`), B — доработка (`texts/polish/`), `--default other`.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_compare as bc  # noqa: E402
import check_texts as ct  # noqa: E402

SOURCE = {"claude": "версия Claude", "other": "версия другой нейросети"}


def edit_notes(path):
    """Слот → пояснение из строки «> …» под его заголовком."""
    notes, cur = {}, None
    head = re.compile(r"^#{2,4}\s*(" + ct.SLOT_ID + r")\s*$")
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = head.match(line.strip())
        if m:
            cur = m.group(1)
            continue
        if cur and line.startswith(">") and cur not in notes:
            notes[cur] = line[1:].strip()
    return notes


def render(sid, slot, note):
    out = ["### " + sid, "> " + note]
    if slot["doc"] is not None:
        out.append("```text")
        out.extend(slot["doc"])
        out.append("```")
    if slot["silence"]:
        out.append("silence")
    for l in slot["lines"]:
        out.append("%s | %s | %s | %s" % (l["speaker"], l["emotion"],
                                         ",".join(l["funcs"]), l["text"]))
    return "\n".join(out)


def merge(brief_path, claude_path, other_path, votes_path, edits_path,
          default="claude", names=None):
    """Блоки итогового файла и отчёт. `default` — чья версия берётся без
    голоса («claude» — первый файл, «other» — второй); `names` — подписи
    двух версий в строках «> …»."""
    if default not in ("claude", "other"):
        raise ValueError("default: claude или other, а не %r" % (default,))
    source = dict(SOURCE)
    if names:
        source["claude"], source["other"] = names
    brief = ct.parse_brief(brief_path)
    act = ct.detect_act(brief_path)
    versions = {}
    broken = {}
    for who, p in (("claude", claude_path), ("other", other_path)):
        texts, fmt = ct.parse_texts(p)
        errs, _, _ = ct.check(brief, texts, fmt, act)
        versions[who] = texts
        broken[who] = {s for s, _ in errs if s}
    votes = json.loads(Path(votes_path).read_text(encoding="utf-8"))
    edits, edit_errs = ct.parse_texts(edits_path)
    if edit_errs:
        raise ValueError("файл правок не по формату: %s" % edit_errs[:3])
    notes = edit_notes(edits_path)
    blocks, report = [], {"edit": [], "claude": [], "other": [], "rule": [], "default": []}
    for sid in brief:
        pick = (votes.get(sid) or {}).get("pick")
        if sid in edits:
            slot, note, kind = edits[sid], "правка: " + notes.get(sid, "без пояснения"), "edit"
        elif pick in ("claude", "other"):
            slot, note, kind = versions[pick][sid], "голос автора: " + source[pick], pick
        elif (sid in broken["other"]) != (sid in broken["claude"]):
            who = "claude" if sid in broken["other"] else "other"
            slot, note, kind = versions[who][sid], "по правилам ТЗ: " + source[who], "rule"
        else:
            slot, note, kind = versions[default][sid], "голоса нет: " + source[default], "default"
        report[kind].append(sid)
        blocks.append(render(sid, slot, note))
    unknown = sorted(set(edits) - set(brief))
    if unknown:
        raise ValueError("в файле правок слоты не из ТЗ: %s" % ", ".join(unknown))
    return blocks, report


def rel(path):
    """Путь относительно репозитория (для шапки), иначе имя файла."""
    try:
        return Path(path).resolve().relative_to(ct.ROOT).as_posix()
    except ValueError:
        return Path(path).name


def header(brief_path, claude_path, other_path, votes_path, edits_path, names=None, note=None):
    act = ct.detect_act(brief_path)
    a, b = names or (SOURCE["claude"], SOURCE["other"])
    return ("# Акт %s «%s» — итоговые тексты\n\n"
            "Сгенерировано `tools/texts/merge_texts.py` из голосов автора в слепом сравнении (`%s`), "
            "двух версий по ТЗ — %s (`%s`) и %s (`%s`) — и правок (`%s`). "
            "Руками не править: правки вносятся в файл правок, затем сборка заново. "
            "Строка `>` под заголовком слота — откуда он взят.\n"
            % (bc.ROMAN[act], bc.act_title(brief_path), rel(votes_path), a, rel(claude_path),
               b, rel(other_path), rel(edits_path))
            + ("\n%s\n" % note if note else ""))


def build(brief_path, claude_path, other_path, votes_path, edits_path, default="claude", names=None, note=None):
    """Полный текст итогового файла и отчёт. `note` — абзац в шапке (состояние, решение автора)."""
    blocks, report = merge(brief_path, claude_path, other_path, votes_path, edits_path, default, names)
    act = ct.detect_act(brief_path)
    text = (header(brief_path, claude_path, other_path, votes_path, edits_path, names, note)
            + "\n" + "\n\n".join(blocks) + "\n\nКОНЕЦ АКТА %s\n" % bc.ROMAN[act])
    return text, report


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Итоговые тексты акта из голосов и правок.")
    ap.add_argument("--brief", default=str(ct.DEFAULT_BRIEF), help="ТЗ акта (по умолчанию Акт I)")
    ap.add_argument("--names", default=None, help="подписи версий A и B через запятую")
    ap.add_argument("--default", default="claude", choices=("claude", "other"),
                    help="чья версия берётся без голоса: claude — первый файл, other — второй")
    ap.add_argument("--note", default=None, help="абзац в шапку: состояние текстов, решение автора")
    ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("votes"); ap.add_argument("edits"); ap.add_argument("out")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    names = tuple(s.strip() for s in args.names.split(",")) if args.names else None
    if names and len(names) != 2:
        print("--names: ровно две подписи через запятую", file=sys.stderr)
        return 2
    try:
        text, report = build(args.brief, args.a, args.b, args.votes, args.edits, args.default, names, args.note)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    Path(args.out).write_text(text, encoding="utf-8")
    print("Итог: %s" % args.out)
    a, b = names or (SOURCE["claude"], SOURCE["other"])
    labels = {"edit": "правки", "claude": "голос за «%s»" % a, "other": "голос за «%s»" % b,
              "rule": "по правилам ТЗ", "default": "голоса нет, «%s»" % (a if args.default == "claude" else b)}
    for k in ("claude", "other", "edit", "rule", "default"):
        print("  %-40s %3d%s" % (labels[k], len(report[k]),
                                 (": " + ", ".join(report[k])) if k in ("rule", "edit") and report[k] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
