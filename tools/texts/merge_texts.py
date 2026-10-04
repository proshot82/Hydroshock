#!/usr/bin/env python3
"""Итоговая версия текстов акта: голоса слепого сравнения плюс правки.

Для каждого слота ТЗ, по порядку:
  1. слот есть в файле правок → он целиком (строки автора, стыковка);
  2. автор выбрал вариант Claude или другой нейросети → этот вариант;
  3. голоса нет, а одна версия нарушила жёсткое правило ТЗ → другая
     (по ТЗ такой слот проигран автоматически);
  4. голоса нет → версия Claude (такие слоты перечисляются в отчёте).
Под заголовком каждого слота пишется строка «> …» — откуда он взят.

Выход генерируется: руками его не править, правки — в файле правок.

Запуск:
    python tools/texts/merge_texts.py CLAUDE.md OTHER.md VOTES.json EDITS.md FINAL.md
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
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


def merge(brief_path, claude_path, other_path, votes_path, edits_path):
    brief = ct.parse_brief(brief_path)
    versions = {}
    broken = {}
    for who, p in (("claude", claude_path), ("other", other_path)):
        texts, fmt = ct.parse_texts(p)
        errs, _, _ = ct.check(brief, texts, fmt)
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
            slot, note, kind = versions[pick][sid], "голос автора: " + SOURCE[pick], pick
        elif (sid in broken["other"]) != (sid in broken["claude"]):
            who = "claude" if sid in broken["other"] else "other"
            slot, note, kind = versions[who][sid], "по правилам ТЗ: " + SOURCE[who], "rule"
        else:
            slot, note, kind = versions["claude"][sid], "голоса нет: " + SOURCE["claude"], "default"
        report[kind].append(sid)
        blocks.append(render(sid, slot, note))
    unknown = sorted(set(edits) - set(brief))
    if unknown:
        raise ValueError("в файле правок слоты не из ТЗ: %s" % ", ".join(unknown))
    return blocks, report


HEADER = """# Акт I «Комплимент от заведения» — итоговые тексты

Сгенерировано `tools/texts/merge_texts.py` из голосов автора в слепом сравнении (`ACT1_VOTES.json`), двух версий по ТЗ и правок (`ACT1_TEXTS_EDITS.md`). Руками не править: правки вносятся в файл правок, затем сборка заново. Строка `>` под заголовком слота — откуда он взят.
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 5:
        print(__doc__)
        return 2
    claude, other, votes, edits, out = argv
    blocks, report = merge(ct.DEFAULT_BRIEF, claude, other, votes, edits)
    Path(out).write_text(HEADER + "\n" + "\n\n".join(blocks) + "\n\nКОНЕЦ АКТА I\n",
                         encoding="utf-8")
    print("Итог: %s" % out)
    names = {"edit": "правки", "claude": "голос за Claude", "other": "голос за другую нейросеть",
             "rule": "по правилам ТЗ", "default": "голоса нет, версия Claude"}
    for k in ("claude", "other", "edit", "rule", "default"):
        print("  %-28s %3d%s" % (names[k], len(report[k]),
                                 (": " + ", ".join(report[k])) if k in ("rule", "default") and report[k] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
