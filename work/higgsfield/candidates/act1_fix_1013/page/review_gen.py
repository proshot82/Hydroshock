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


parts.append('<h1 class="step">Картинки</h1>')
add("voucher", "Первый кадр: путёвка в голых руках",
    "<p><b>Что не так было.</b> На самом первом кадре игры Лапидус держит путёвку в рукавах пиджака и манжетах рубашки, а портрет рядом уже голый, и через секунду он в душе. Вы предложили: путёвку он держит уже голыми руками.</p>"
    "<p><b>Что сделано.</b> Кадр перерисован по образцу: всё как было, только руки голые до локтя. Два варианта, отличаются положением рук.</p>",
    '<div class="pair">' + img("voucher_0.webp", "было: рукава пиджака") + img("voucher_a.webp", "вариант А") + img("voucher_b.webp", "вариант Б") + "</div>",
    [("a", "вариант А", ""), ("b", "вариант Б", "")], "оба не годятся — переделать", "например: руки покороче, путёвку ближе")
add("dispenser", "Флакон с дозатором в душе: надпись на этикетке",
    "<p><b>Что не так было.</b> На флаконе в душе пустая этикетка, хотя вся завязка держится на этой пене: «премиум»-концентрат, который не смывается порциями.</p>"
    "<p><b>Что сделано.</b> На этикетке напечатано «ПЕНА · концентрат · «премиум»» шрифтами игры, с лёгким размытием, чтобы надпись выглядела нарисованной, а не наклеенной поверх. Буквы проверены по одной.</p>",
    '<div class="pair">' + img("disp_0.webp", "было: пустая этикетка") + img("disp_1.webp", "стало") + "</div>" + img("disp_full.webp", "весь кадр душевой панели"),
    [("ok", "так хорошо", "")], "переделать", "например: только «ПРЕМИУМ», крупнее")
add("croissant", "Круассан под колпаком",
    "<p><b>Что не так было.</b> Текст говорит «под колпаком один круассан», а на картинке круассан лежит рядом на тарелке; и зона круассана называлась «Колпак». "
    "Здесь побеждает замороженная сдача Акта I: шутка «колпак прикрывает круассан, а не меня» (D16) держится на том, что круассан под колпаком. Поэтому исправлена картинка, а не текст.</p>"
    "<p><b>Что сделано.</b> Тарелка с круассаном убрана с подноса на всех трёх картинках с тележкой (зум тележки и два слоя тележки в номере). Зона «Колпак» теперь только на колпаке. Вариант А оставляет на подносе пустое латунное блюдо, вариант Б — чистый поднос с еле заметным бликом.</p>",
    '<div class="pair">' + img("z03_0.webp", "было") + img("z03_a.webp", "вариант А: пустое блюдо") + img("z03_b.webp", "вариант Б: чистый поднос") + "</div>"
    + '<div class="pair">' + img("z03_open_b.webp", "Б со сложенными звёздами и отодвинутой шторкой") + img("w1_0.webp", "тележка в номере: было") + img("w1_b.webp", "в номере, Б") + img("w1_fb.webp", "в номере, звёзды сложены, Б") + "</div>",
    [("a", "вариант А (пустое блюдо)", ""), ("b", "вариант Б (чистый поднос)", "")], "не так — переделать",
    "например: пусть круассан всё-таки останется, а текст поменять")
add("snow", "Вестибюль из лифта: «снег»",
    "<p><b>Что не так было.</b> На двух кадрах вестибюля (Лапидус выглядывает из лифта; официант с тележкой) по волосам, лицам и мрамору рассыпаны белые и тёмные точки — след многократных перегенераций.</p>"
    "<p><b>Что сделано.</b> Отдельные точки найдены программой (крошечные пятна, резко отличающиеся от соседей) и заменены цветом окружения. Контуры и штрихи рисунка не тронуты. Ниже — самые «заснеженные» места крупно, было и стало, и оба кадра целиком.</p>",
    '<div class="pair">' + img("fr_a1_lobby_peek_0_0.webp", "толпа: было") + img("fr_a1_lobby_peek_0_1.webp", "толпа: стало") + "</div>"
    + '<div class="pair">' + img("fr_a1_lobby_peek_1_0.webp", "толпа, другое место: было") + img("fr_a1_lobby_peek_1_1.webp", "стало") + "</div>"
    + '<div class="pair">' + img("fr_a1_lobby_waiter_0_0.webp", "официант: было") + img("fr_a1_lobby_waiter_0_1.webp", "официант: стало") + "</div>"
    + '<div class="pair">' + img("fr_a1_lobby_peek_full.webp", "кадр «из лифта» целиком, стало") + img("fr_a1_lobby_waiter_full.webp", "кадр с официантом целиком, стало") + "</div>",
    [("ok", "так хорошо", "")], "мало — перерисовать кадры заново", "например: на лицах ещё видны точки")

parts.append('<h1 class="step">Музыка вступления</h1>')
DEMOS = [
    ("p1", "Ленивая босса-нова", "вибрафон, нейлоновая гитара, флейта, щётки", [
        ("p1_bossa", "1"), ("p1_bossa_b", "2"), ("p1_bossa_b_medium", "2, вариация свободнее"), ("p1_bossa_b_low", "2, вариация ещё свободнее")]),
    ("p2", "Гавайский шезлонг", "гавайская гитара с глиссандо, укулеле, маримба", [
        ("p2_hawaii", "1"), ("p2_hawaii_medium", "1, вариация свободнее"), ("p2_hawaii_low", "1, вариация ещё свободнее"), ("p2_hawaii_b", "2")]),
    ("p3", "Черноморский санаторий 60-х", "аккордеон, мандолина, вибрафон, кларнет — эстрада советского курорта", [
        ("p3_sanatorium", "1"), ("p3_sanatorium_b", "2"), ("p3_sanatorium_b_medium", "2, вариация свободнее"), ("p3_sanatorium_b_low", "2, вариация ещё свободнее")]),
]
opts = []
for code, name, inst, items in DEMOS:
    for f, lab in items:
        opts.append((f, f"{name} — {lab}", f'<span class="tag">{html.escape(inst)}</span>'
                     f'<audio controls preload="none" src="audio/demo_{f}.mp3"></audio>'))
add("music", "Курортная тема, обрыв, гидроудар, тревожная вариация",
    "<p><b>Что вы просили.</b> В номере в начале — что-то более вальяжно-курортное. За мгновение до гидроудара музыка обрывается, удар звучит в тишине. После него — вариация той же темы, тревожнее, но всё ещё с юмором.</p>"
    "<p><b>Как сделано.</b> Каждое демо собрано так, как будет в игре: курортная тема (38 с) → обрыв → 0,7 с тишины → удар из игры → вариация. "
    "Вариация сделана новой моделью ElevenLabs «по образцу» — ей дают кусок самой темы, и она играет её же, другими инструментами и с другим настроением. "
    "«Свободнее» — образец держит слабее: мелодия узнаётся меньше, зато настроение меняется сильнее. Описания — по заданию и анализу спектра, не на слух: решает ваше ухо. "
    "Я проверил тональность программой: во всех вариациях, кроме гавайской «ещё свободнее», остался мажор, тревогу дают инструменты и темп. Если нужен явный минор — скажите, сделаю следующий круг.</p>"
    "<p><b>В игре уже работает</b> (по ссылке на игру): обрыв музыки и звука номера перед ударом, удар в тишине, потом тема номера входит плавно. Пока на старой теме — новая встанет после вашего выбора.</p>",
    "", opts, "ничего не подходит — новый круг", "например: тема из 2-го, вариация из 1-го; темп медленнее")
add("music_scope", "Где звучит тревожная вариация",
    "<p>Сейчас в номере и вестибюле (Акты I–II) играет одна тема отеля. Тревожная вариация может её заменить, или звучать только в Акте I после удара, а в Акте II вернётся прежняя тема отеля.</p>"
    "<p><b>Мой совет:</b> заменить в Акте I, а в Акте II оставить прежнюю тему отеля: к середине игры Лапидус уже освоился, тревога сменяется азартом.</p>",
    "", [("act1", "вариация только в Акте I, в Акте II — прежняя тема отеля (совет)", ""),
         ("all", "вариация вместо темы отеля везде (Акты I–II)", "")],
    "по-другому — напишу", "")

parts.append('<h1 class="step">Тексты</h1>')
add("txt_open", "Переход к душу: ваша строка",
    "<p>После слов о путёвке добавлена ваша строка; ТЗ Акта I для этого слота расширено до четырёх реплик.</p>",
    lines([("Лапидус", "Пятнадцать лет без больничных. Имею право.", False),
           ("Лапидус", "Что ж, всю одежду в стирку, Лапидуса — в чистку.", False)]),
    [("ok", "так", "")], "поправить", "")
add("txt_stars", "Как Лапидус понимает, что звёзды складываются",
    "<p><b>Что не так было.</b> Вторая реплика при осмотре звёзд говорила только «звёзды на петлях» — игроку непонятно, откуда вывод, что их можно сложить. По ТЗ здесь нужна улика: петли и потёртые дуги на бортике.</p>"
    "<p><b>Что сделано.</b> Добавлены дуги: бортик протёрт, значит звёзды откидывали не раз. Ваша шутка про звезду в петличку осталась. На картинке петли видны у каждой звезды.</p>",
    lines([("Лапидус", "Звёзды на петлях. За такую наблюдательность мне звезду в петличку.", True),
           ("Лапидус", "Стоп, звёзды-то на петлях. И бортик под ними протёрт дугами: их откидывали, и не раз. За такую наблюдательность мне звезду в петличку.", False)]),
    [("ok", "так", "")], "поправить", "")
add("txt_peek", "Коридор и лифт: теперь игрок идёт сам",
    "<p><b>Что не так было.</b> Выйдя в коридор, Лапидус сам собой заходил в лифт и ехал вниз — и при этом говорил, что к людям не хочет.</p>"
    "<p><b>Что сделано.</b> Коридор и кабина лифта стали обычными экранами. Щелчок по двери номера — Лапидус выглядывает в коридор; можно вернуться в номер. Щелчок по лифту — он в кабине у панели; можно выйти. "
    "Кнопка «Вестибюль» — двери открываются в вестибюль, Лапидус смотрит из кабины и едет обратно. Реплика в лифте теперь объясняет, зачем он едет: только посмотреть, не выходя.</p>",
    lines([("Титр (коридор)", "Пустой коридор. Ковровая дорожка, двери номеров, в конце служебный лифт.", False),
           ("Лапидус", "Иду по коридору так, будто на этом этаже такой дресс-код.", True),
           ("Лапидус", "Никого. Если идти уверенно, все решат, что на этом этаже такой дресс-код.", False),
           ("Титр (лифт)", "Лифт приехал. На панели только этажи номеров и вестибюль.", True),
           ("Титр (лифт)", "Служебный лифт приходит сразу. На панели только этажи номеров и вестибюль.", False),
           ("Лапидус", "Ни прачечной, ни служебных этажей. Только вниз, к людям. А к людям мне сейчас хочется меньше всего.", True),
           ("Лапидус", "Ни прачечной, ни служебных этажей. Выходить к людям я не собираюсь: доеду до вестибюля, гляну из кабины, что там творится, и сразу обратно.", False)]),
    [("ok", "так", "")], "поправить", "")

page = f"""<title>Гидроудар: разбор Акта I</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Old+Standard+TT:wght@400;700&family=PT+Sans:wght@400;700&family=PT+Mono&display=swap">
{STYLE}
<div class="wrap">
<header class="lead">
<h1>Разбор Акта I: что поправлено</h1>
<p>Ваши замечания от 13.10.2026 по первой игре в Акт I. Всё, что меняет логику, уже в игре по прежней ссылке: юбка-шторка остаётся отодвинутой, пока вы у тележки (табличку видно только тогда); коридор и лифт — экраны, куда игрок идёт сам; музыка обрывается перед ударом. Картинки и музыка ниже — кандидаты: в игру уйдут после вашего выбора и «да».</p>
<div id="banner" class="note">Загружаю отметки…</div>
</header>
{chr(10).join(parts)}
<footer>Кандидаты картинок — work/higgsfield/candidates/act1_fix_1013/ (README), музыки — work/audio/candidates/s6_resort_1013/ (README).</footer>
</div>
{SCRIPT_SRC.replace("const SLOTS = %s;", "const SLOTS = " + json.dumps(SLOTS) + ";")}
"""
(HERE / "review.html").write_text(page, encoding="utf-8")
print("review.html", len(page), SLOTS)
