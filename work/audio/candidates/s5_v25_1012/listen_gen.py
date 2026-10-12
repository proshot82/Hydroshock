#!/usr/bin/env python3
"""Собирает listen.html пакета З5а: все мелодии на Music v2.5 рядом с принятыми, с отметками автора прямо
на странице (capability db: коллекция picks, документ на мелодию — {choice, comment, at})."""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
S1 = HERE.parent / "s1_music_1012" / "listen.html"
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
</style>""")

CUR = "принятая сейчас"
SEAMS = [
    (f"seam_{k}", f"Шов петли: {t}", f"Ваш выбор: {c}. Из него вырезана петля {d}; ниже — {n} секунд её конца и {n} секунд начала подряд, склейка ровно посередине. Слышен ли шов?",
     [("ok", "шов не слышен")])
    for k, t, c, d, n in [
        ("bgm_title", "титул", "новая модель, 1", "51 с", 12),
        ("bgm_hotel", "отель", "новая модель, 1", "77 с", 12),
        ("bgm_service", "служебные коридоры", "новая модель, 1", "77 с", 12),
        ("bgm_below", "пещера Кухтулху", "новая модель, 2", "78 с", 12),
        ("mus_hold", "музыка ожидания", "новая модель, 1 (через «трубку»)", "25 с", 8),
        ("bgm_epilogue", "финал и эпилог", "c4, мультяшный джаз", "91 с", 12),
    ]
]

SLOTS = [
    ("bgm_title", "Титул", "Главное меню: фон «Три плаката», логотип с «II» из труб. Принята v5 прежней модели: загадочный, чуть жутковатый весёлый джаз.",
     [("cur", CUR + " (v1)"), ("v25_1", "новая модель, 1"), ("v25_2", "новая модель, 2")]),
    ("bgm_hotel", "Отель (W1–W2)", "Номер 317 и вестибюль, Акты I–II: главная уютная тема, свинг с кларнетом и флейтой.",
     [("cur", CUR + " (v1)"), ("v25_1", "новая модель, 1"), ("v25_2", "новая модель, 2")]),
    ("bgm_service", "Служебные коридоры (W3–W4)", "Прачечная и зал прекраснодушия: ленивый уютный блюз, фагот и кларнет.",
     [("cur", CUR + " (v1)"), ("v25_1", "новая модель, 1"), ("v25_2", "новая модель, 2")]),
    ("bgm_deep", "Чудовище из глубины", "Спуск под юбкой тележки и начало Акта IV, пока игрок ждёт чудовище; обрывается при появлении Кухтулху. Вариант 3 — «e» из первого круга, тоже новая модель.",
     [("cur", CUR + " (v1, вариант a)"), ("v25_1", "новая модель, 1"), ("v25_2", "новая модель, 2"), ("v25_3", "новая модель, 3 (бывший e)")]),
    ("bgm_below", "Пещера Кухтулху (W5–W6)", "После появления Кухтулху: лукавая медленная хабанера. Принята v9 прежней модели.",
     [("cur", CUR + " (v1, v9)"), ("v25_1", "новая модель, 1"), ("v25_2", "новая модель, 2")]),
    ("mus_hold", "Музыка ожидания", "Автоответчик стойки в Акте I: «оставайтесь на линии». Принята версия из сэмплера; новые — ElevenLabs, пропущены через ту же «трубку».",
     [("cur", CUR + " (сэмплер)"), ("v25_1", "новая модель, 1"), ("v25_2", "новая модель, 2")]),
    ("sting_solved", "Стингер «загадка решена»", "Короткое «ура», когда Лапидус сдвинул дело.",
     [("cur", CUR + " (v1, вариант 2)"), ("v25_1", "новая модель, 1"), ("v25_2", "новая модель, 2")]),
    ("sting_relic", "Стингер «реликвия»", "Найдена одна из трёх старых вещей хозяйки низа.",
     [("cur", CUR + " (v1, вариант 1)"), ("v25_1", "новая модель, 1"), ("v25_2", "новая модель, 2")]),
    ("sting_water", "Стингер «пуск воды»", "Маховик повёрнут, по зданию идёт выдох; оркестровый разворот поверх.",
     [("cur", CUR + " (v1, вариант 2)"), ("v25_1", "новая модель, 1"), ("v25_2", "новая модель, 2")]),
]


def opt(slot, key, label):
    rid = f"{slot}-{key}"
    return (f'<div class="opt"><input type="radio" name="{slot}" id="{rid}" value="{key}">'
            f'<label for="{rid}">{html.escape(label)}</label>'
            f'<audio controls preload="none" src="listen/{slot}_{key}.mp3"></audio></div>')


def section(slot, title, about, opts, redo_label):
    rows = "\n".join(opt(slot, k, l) for k, l in opts)
    redo = (f'<div class="opt"><input type="radio" name="{slot}" id="{slot}-redo" value="redo">'
            f'<label for="{slot}-redo">{redo_label}</label></div>')
    return (f'''<section data-slot="{slot}"><h2>{html.escape(title)}</h2>
<div class="moment"><p><b>{slot}.</b> {html.escape(about)}</p></div>
<div class="opts">{rows}
{redo}</div>
<label class="note" for="{slot}-note">Замечание (необязательно)</label>
<textarea id="{slot}-note" data-note="{slot}" placeholder="например: темп побыстрее, без тромбона"></textarea>
<div class="state" data-state="{slot}"></div></section>''')


parts = ['<h1 style="font-size:1.6rem">Шаг 2 — швы петель (новое)</h1>']
parts += [section(*s, "шов слышен — перерезать") for s in SEAMS]
parts += ['<h1 style="font-size:1.6rem">Шаг 1 — выбор модели (ваши отметки)</h1>']
parts += [section(*s, "ничего не подходит — переделать") for s in SLOTS]

SCRIPT = """<script>
const SLOTS = %s;
const banner = document.getElementById('banner');
const queue = {};
function say(slot, text, cls) { const el = document.querySelector('[data-state="' + slot + '"]'); el.textContent = text; el.className = 'state ' + (cls || ''); }
function current(slot) {
  const r = document.querySelector('input[name="' + slot + '"]:checked');
  return { choice: r ? r.value : null, comment: document.getElementById(slot + '-note').value.trim() };
}
async function start() {
  let db = null;
  try { db = window.claude ? await window.claude.use('db') : null; } catch (e) { db = null; }
  if (!db) { banner.textContent = 'Отметки на этой странице сейчас не сохраняются (страница открыта не в claude.ai или без входа). Напишите выбор в чат.'; return; }
  banner.textContent = 'Отметки сохраняются сами, сразу после выбора; замечание — когда уходите из поля. Claude прочитает их отсюда.';
  function save(slot) {
    const body = Object.assign(current(slot), { at: new Date().toISOString() });
    say(slot, 'Сохраняю…');
    queue[slot] = (queue[slot] || Promise.resolve()).then(() => db.doc('picks/' + slot).set(body))
      .then(() => say(slot, 'Сохранено', 'ok'))
      .catch(e => say(slot, 'Не сохранилось: ' + (e && e.code === 'permission_denied' ? 'нет прав на запись' : 'ошибка связи, выберите ещё раз'), 'err'));
  }
  SLOTS.forEach(slot => {
    document.querySelectorAll('input[name="' + slot + '"]').forEach(r => r.addEventListener('change', () => save(slot)));
    document.getElementById(slot + '-note').addEventListener('change', () => save(slot));
  });
  db.collection('picks').onSnapshot(snap => {
    snap.docs.forEach(d => {
      if (!SLOTS.includes(d.id)) return;
      const v = d.data() || {};
      if (v.choice) { const r = document.getElementById(d.id + '-' + v.choice); if (r) r.checked = true; }
      const ta = document.getElementById(d.id + '-note');
      if (document.activeElement !== ta && typeof v.comment === 'string') ta.value = v.comment;
      if (!d.metadata.hasPendingWrites && v.choice) say(d.id, 'Сохранено', 'ok');
    });
  }, () => { banner.textContent = 'Связь с хранилищем отметок прервалась. Обновите страницу.'; });
}
start();
</script>""" % json.dumps([s[0] for s in SEAMS + SLOTS])

page = f"""<title>Гидроудар: мелодии v2.5</title>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Old+Standard+TT:wght@400;700&family=PT+Sans:wght@400;700&family=PT+Mono&display=swap">
{STYLE}
<div class="wrap">
<header class="lead">
<h1>Все мелодии на новой модели</h1>
<p>Каждая мелодия игры заново сделана новой моделью ElevenLabs Music v2.5 по тому же заданию, что принятая; рядом — принятая сейчас. Громкость у всех одинаковая (−18 LUFS), чтобы сравнивать честно. Тема финала уже на новой модели (c4, ваш выбор) — её здесь нет.</p>
<p><b>Шаг 1 сделан</b> — ваши отметки ниже. <b>Шаг 2:</b> из выбранных вырезаны петли (музыка в игре крутится по кругу); послушайте склейку каждой и отметьте «шов не слышен» или «перерезать». После этого и вашего «да» всё уходит в игру.</p>
<div id="banner" class="note">Загружаю отметки…</div>
</header>
{chr(10).join(parts)}
<footer>Петли режет tools/music/make_loop.py (шов по долям, перехлёст, −18 LUFS). Подробности — work/audio/candidates/s5_v25_1012/README.md.</footer>
</div>
{SCRIPT}
"""
(HERE / "listen.html").write_text(page, encoding="utf-8")
print("listen.html", len(page))
