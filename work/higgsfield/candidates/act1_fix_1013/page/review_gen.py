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


# ---------- раунд 2 (14.10.2026): что ещё ждёт выбора; раунд 1 — в истории git

parts.append('<h1 class="step">Картинки</h1>')
add("snow2", "Вестибюль из лифта: перерисовано начисто",
    "<p><b>Ваш ответ на прошлом шаге:</b> очистки мало, перерисовать. <b>Что сделано.</b> Оба кадра вестибюля нарисованы заново по прежним, без «снега». "
    "Генератор переврал имя на бейдже Изольды («Г. Петина»), поэтому имя «И. Т. Итьева» впечатано так же, как раньше на её кадрах; надпись «Банный день» проверена по буквам. "
    "На кадре с официантом на его тележке тоже яйцо всмятку вместо круассана — как на нашей тележке. Два варианта перерисовки; ниже лица крупно: было и оба новых.</p>",
    '<div class="pair">' + img("fr_a1_lobby_peek_r1.webp", "из лифта, вариант 1") + img("fr_a1_lobby_peek_r2.webp", "из лифта, вариант 2") + "</div>"
    + '<div class="pair">' + img("fr_a1_lobby_peek_face_0.webp", "было") + img("fr_a1_lobby_peek_face_r1.webp", "вариант 1") + img("fr_a1_lobby_peek_face_r2.webp", "вариант 2") + "</div>"
    + '<div class="pair">' + img("fr_a1_lobby_waiter_r1.webp", "официант, вариант 1") + img("fr_a1_lobby_waiter_r2.webp", "официант, вариант 2") + "</div>"
    + '<div class="pair">' + img("fr_a1_lobby_waiter_face_0.webp", "было") + img("fr_a1_lobby_waiter_face_r1.webp", "вариант 1") + img("fr_a1_lobby_waiter_face_r2.webp", "вариант 2") + img("egg_waiter.webp", "тележка официанта, вариант 1") + "</div>",
    [("r1", "вариант 1 (оба кадра)", ""), ("r2", "вариант 2 (оба кадра)", "")], "ни один — ещё раз", "например: из лифта — 1, официант — 2")
add("egg", "Яйцо всмятку вместо круассана",
    "<p><b>Ваш ответ:</b> «пусть вместо круассана будет яйцо всмятку». <b>Что сделано.</b> На тарелке рядом с колпаком теперь яйцо всмятку в фарфоровой рюмке с ложечкой; круассан, как и говорит текст, под колпаком. "
    "Поправлены все три картинки нашей тележки (зум и два слоя в номере). У яйца своя зона, при осмотре Лапидус говорит одну строку — она ниже, в текстах.</p>",
    '<div class="pair">' + img("egg_z03_a.webp", "зум тележки, вариант А") + img("egg_z03_b.webp", "зум тележки, вариант Б") + "</div>"
    + '<div class="pair">' + img("egg_w1_a.webp", "в номере, А") + img("egg_w1_b.webp", "в номере, Б") + "</div>",
    [("a", "вариант А", ""), ("b", "вариант Б", "")], "не так — переделать", "")

parts.append('<h1 class="step">Музыка: швы петель</h1>')
for slot, title, about, f in [
        ("seam_resort", "Курортная тема (вступление)", "Ваш выбор: «Санаторий 60-х», дубль 1. Петля 42,8 с; в игре звучит на путёвке и в душе.", "seam_bgm_resort"),
        ("seam_tense", "Тревожная вариация (Акт I после удара)", "Ваш выбор: та же тема, вариация по образцу; только в Акте I, в Акте II — прежняя тема отеля. Петля 68,6 с.", "seam_bgm_hotel_tense")]:
    add(slot, "Шов: " + title,
        f"<p>{html.escape(about)} Музыка в игре крутится по кругу. Ниже 12 секунд конца петли и 12 секунд её начала подряд, склейка ровно посередине. Слышен ли шов?</p>"
        "<p>Обе темы уже стоят в игре — можно послушать и там.</p>",
        f'<audio controls preload="none" src="audio/{f}.mp3"></audio>',
        [("ok", "шов не слышен", "")], "шов слышен — перерезать", "")

parts.append('<h1 class="step">Текст</h1>')
add("txt_egg", "Осмотр яйца",
    "<p>Новая строка при осмотре яйца всмятку (одна реплика).</p>",
    lines([("Лапидус", "Яйцо всмятку в рюмке. Хоть кто-то здесь в скорлупе, а не голый.", False)]),
    [("ok", "так", "")], "поправить", "")

done = ("<ul>"
        "<li>Путёвка в голых руках — вариант Б, в игре.</li>"
        "<li>Надпись на флаконе — в игре.</li>"
        "<li>Музыка: «Санаторий 60-х», дубль 1; вариация только в Акте I — в игре (обрыв перед ударом, удар в тишине).</li>"
        "<li>Тексты: ваша строка после путёвки, улика у звёзд, коридор и лифт — приняты.</li></ul>")

page = f"""<title>Гидроудар: разбор Акта I</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Old+Standard+TT:wght@400;700&family=PT+Sans:wght@400;700&family=PT+Mono&display=swap">
{STYLE}
<div class="wrap">
<header class="lead">
<h1>Разбор Акта I: второй круг</h1>
<p>По вашим отметкам первого круга уже сделано и стоит в игре (ссылка на игру прежняя):</p>
{done}
<p>Ниже — что осталось: перерисованный вестибюль, яйцо всмятку, швы двух новых мелодий и одна строка.</p>
<div id="banner" class="note">Загружаю отметки…</div>
</header>
{chr(10).join(parts)}
<footer>Кандидаты картинок — work/higgsfield/candidates/act1_fix_1013/ (README), музыки — work/audio/candidates/s6_resort_1013/ (README).</footer>
</div>
{SCRIPT_SRC.replace("const SLOTS = %s;", "const SLOTS = " + json.dumps(SLOTS) + ";")}
"""
(HERE / "review.html").write_text(page, encoding="utf-8")
print("review.html", len(page), SLOTS)
