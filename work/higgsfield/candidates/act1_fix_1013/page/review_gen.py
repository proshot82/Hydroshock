#!/usr/bin/env python3
"""Страница выбора по разбору Акта I 13.10.2026: картинки, музыка, тексты.

Отметки автора — прямо на странице (capability db: коллекция picks, документ на вопрос —
{choice, comment, at}), как на прослушке пакета З5а. Стиль и скрипт отметок — оттуда же.
"""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
S1 = ROOT / "work/audio/candidates/s1_music_1012/listen.html"
S5 = ROOT / "work/audio/candidates/s5_v25_1012/listen.html"
STYLE = re.search(r"<style>.*?</style>", S1.read_text(encoding="utf-8"), re.S).group(0).replace("</style>", """
.opts{display:grid;gap:8px}
.opt{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;align-items:center;background:var(--paper);border:1px solid var(--line);border-radius:4px;padding:10px 12px;min-width:0}
.opt:has(input:checked){border-color:var(--brass);box-shadow:inset 3px 0 0 var(--brass)}
.opt input{width:20px;height:20px;accent-color:var(--brass);margin:0}
.opt label{font-weight:700;cursor:pointer}
.opt .tag{grid-column:2}
.opt audio{grid-column:1 / -1}
textarea{width:100%;box-sizing:border-box;min-height:56px;font:inherit;color:var(--fg);background:var(--paper);border:1px solid var(--line);border-radius:4px;padding:8px}
textarea:focus-visible,.opt input:focus-visible{outline:2px solid var(--deep);outline-offset:2px}
.state{font-size:.85rem;color:var(--muted);min-height:1.2em}
.state.ok{color:var(--deep)} .state.err{color:var(--bad)}
#banner{background:var(--brass-soft);border:1px solid var(--brass);border-radius:4px;padding:10px 12px}
.wrap{max-width:980px}
figure{margin:0;display:grid;gap:4px;min-width:0}
figure img{width:100%;height:auto;border:1px solid var(--line);border-radius:2px;display:block}
figcaption{font-size:.85rem;color:var(--muted)}
.pair{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.line{font-size:.95rem;background:var(--paper);border:1px solid var(--line);border-radius:4px;padding:10px 12px;display:grid;gap:4px}
.line .who{font-family:var(--mono);font-size:.8rem;color:var(--brass)}
.line.old{opacity:.75}
.line.old .txt{text-decoration:line-through;text-decoration-color:var(--muted)}
h1.step{font-size:1.6rem}
</style>""")
SCRIPT_SRC = re.search(r"<script>.*?</script>", S5.read_text(encoding="utf-8"), re.S).group(0)
SCRIPT_SRC = re.sub(r"const SLOTS = \[.*?\];", "const SLOTS = %s;", SCRIPT_SRC, count=1, flags=re.S)


def img(src, cap):
    return f'<figure><img src="img/{src}" alt="{html.escape(cap)}" loading="lazy"><figcaption>{html.escape(cap)}</figcaption></figure>'


def radios(slot, opts, redo):
    rows = []
    for key, label, extra in opts + [("redo", redo, "")]:
        rid = f"{slot}-{key}"
        rows.append(f'<div class="opt"><input type="radio" name="{slot}" id="{rid}" value="{key}">'
                    f'<label for="{rid}">{html.escape(label)}</label>{extra}</div>')
    return '<div class="opts">' + "\n".join(rows) + "</div>"


def ask(slot, title, about_html, body_html, opts, redo, placeholder):
    return (f'<section data-slot="{slot}"><h2>{html.escape(title)}</h2>'
            f'<div class="moment">{about_html}</div>{body_html}{radios(slot, opts, redo)}'
            f'<label class="note" for="{slot}-note">Замечание (необязательно)</label>'
            f'<textarea id="{slot}-note" data-note="{slot}" placeholder="{html.escape(placeholder)}"></textarea>'
            f'<div class="state" data-state="{slot}"></div></section>')


def lines(rows):
    out = []
    for who, txt, old in rows:
        out.append(f'<div class="line{" old" if old else ""}"><span class="who">{html.escape(who)}{" — было" if old else ""}</span>'
                   f'<span class="txt">{html.escape(txt)}</span></div>')
    return "".join(out)


SLOTS, parts = [], []


def add(slot, *a):
    SLOTS.append(slot)
    parts.append(ask(slot, *a))


# ---------- раунд 4 (14.10.2026): шов новой тревожной петли; раунды 1–3 — в истории git

add("seam_tense2", "Шов тревожной темы",
    "<p>Ваш выбор: «Крадущийся саспенс», дубль 2 — уже в игре после удара (только Акт I). Из него вырезана петля 66 секунд: музыка в игре крутится по кругу. "
    "Ниже 12 секунд конца петли и 12 секунд её начала подряд, склейка ровно посередине. Слышен ли шов?</p>",
    '<audio controls preload="none" src="audio/seam_bgm_hotel_tense_v2.mp3"></audio>',
    [("ok", "шов не слышен", "")], "шов слышен — перерезать", "")

done = ("<ul>"
        "<li>Тревожная тема — «Крадущийся саспенс», дубль 2, в игре после удара.</li>"
        "<li>Шов курортной темы — принят.</li>"
        "<li>Раньше: вестибюль начисто, яйцо всмятку, путёвка, флакон, курортная тема, тексты.</li></ul>")

page = f"""<title>Гидроудар: разбор Акта I</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Old+Standard+TT:wght@400;700&family=PT+Sans:wght@400;700&family=PT+Mono&display=swap">
{STYLE}
<div class="wrap">
<header class="lead">
<h1>Разбор Акта I: последний вопрос</h1>
<p>Сделано по вашим отметкам и стоит в игре (ссылка на игру прежняя):</p>
{done}
<div id="banner" class="note">Загружаю отметки…</div>
</header>
{chr(10).join(parts)}
<footer>Музыка — work/audio/candidates/s6_resort_1013/ (README).</footer>
</div>
{SCRIPT_SRC.replace("const SLOTS = %s;", "const SLOTS = " + json.dumps(SLOTS) + ";")}
"""
(HERE / "review.html").write_text(page, encoding="utf-8")
print("review.html", len(page), SLOTS)
