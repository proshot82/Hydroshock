#!/usr/bin/env python3
"""Собирает listen.html пакета З8: все звуки игры, переделанные Suno v6, рядом с принятыми,
с отметками автора прямо на странице (capability db: коллекция picks, документ на звук —
{choice, comment, at}; choice: cur — оставить принятый, a/b — версия Suno, redo — переделать)."""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
S1 = HERE.parent / "s1_music_1012" / "listen.html"
STYLE = re.search(r"<style>.*?</style>", S1.read_text(encoding="utf-8"), re.S).group(0)
STYLE = STYLE.replace(".wrap{max-width:760px;margin:0 auto;padding-inline:16px;",
                      ".wrap{max-width:760px;margin:0 auto;padding-left:max(16px, env(safe-area-inset-left, 0px));"
                      "padding-right:max(16px, env(safe-area-inset-right, 0px));")
STYLE = STYLE.replace("</style>", """
.opts{display:grid;gap:8px}
.opt{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;align-items:center;background:var(--paper);border:1px solid var(--line);border-radius:4px;padding:10px 12px;min-width:0}
.opt:has(input:checked){border-color:var(--brass);box-shadow:inset 3px 0 0 var(--brass)}
.opt input{width:20px;height:20px;accent-color:var(--brass);margin:0}
.opt label{font-weight:700;cursor:pointer}
.opt audio{grid-column:1 / -1}
.opt details{grid-column:1 / -1;font-size:.88rem;color:var(--muted)}
.opt details audio{margin-top:6px}
textarea{width:100%;box-sizing:border-box;min-height:56px;font:inherit;color:var(--fg);background:var(--paper);border:1px solid var(--line);border-radius:4px;padding:8px}
textarea:focus-visible,.opt input:focus-visible{outline:2px solid var(--deep);outline-offset:2px}
.state{font-size:.85rem;color:var(--muted);min-height:1.2em}
.state.ok{color:var(--deep)} .state.err{color:var(--bad)}
#banner{background:var(--brass-soft);border:1px solid var(--brass);border-radius:4px;padding:10px 12px}
nav.toc{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.95rem}
nav.toc a{color:var(--deep)}
.group{display:grid;gap:28px}
.group > h1{font-size:1.6rem;border-bottom:1px solid var(--line);padding-bottom:6px}
.src{font-family:var(--mono);font-size:.8rem;color:var(--muted);overflow-wrap:anywhere}
.warn{color:var(--bad);font-size:.9rem}
</style>""")

SPEC = (ROOT / "docs/BJ3_ASSET_SPEC.md").read_text(encoding="utf-8")
S9 = SPEC[SPEC.index("## 9. Звук"):SPEC.index("## 10. Интерфейс")]
ABOUT = {}
for line in S9.splitlines():
    m = re.match(r"^\| `([a-z0-9_]+)\.ogg` \|(.*)\|\s*$", line)
    if m:
        cells = [c.strip() for c in m.group(2).split("|")]
        # §9.1: длина | что | слоты; §9.2: где | что; §9.3/9.4: длина | что
        what = cells[1] if len(cells) >= 2 else cells[0]
        where = cells[2] if len(cells) >= 3 else (cells[0] if m.group(1).startswith("amb_") else "")
        ABOUT[m.group(1)] = (re.sub(r"`", "", what), re.sub(r"`", "", where))
BJ2_UI = {"ui_click": "щелчок интерфейса", "ui_zoom_in": "приближение кадра", "ui_zoom_out": "отдаление кадра",
          "ui_pickup": "предмет взят в инвентарь", "ui_paper": "бумага (записка, документ)",
          "ui_transition": "переход между локациями", "ui_error": "ошибка, «так нельзя»",
          "blip_lap": "блип печати текста — Лапидус (263 Гц)", "blip_anc": "блип печати текста — Предок (145 Гц)"}

GROUPS = [
    ("music", "Мелодии", "Петля вырезана тем же инструментом, что у принятых; громкость −18 LUFS у всех."),
    ("sting", "Стингеры", "Обрезаны до длины принятого, затухание в конце, −18 LUFS."),
    ("sfx", "Эффекты", "Из трека Suno вырезано с первого звука до длины принятого, моно, −16 LUFS (удар −12, душ и затихание вестибюля −20). Под каждой версией — что Suno выдал целиком: вдруг лучшее место не в начале."),
    ("amb", "Амбиенты", "Петля 30 с с перехлёстом, −26 LUFS; для прослушки склеена дважды, шов на 0:30."),
    ("short", "Блипы и интерфейс", "Самый сильный щелчок трека, длина принятого. Принятые — синтез или звуки BJ2."),
]
items = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
report = json.loads((HERE / "build_report.json").read_text(encoding="utf-8"))


def player(name, key):
    return f'<audio controls preload="none" src="listen/{name}_{key}.mp3"></audio>'


def opt(name, key, label, full=False):
    rid = f"{name}-{key}"
    extra = ""
    r = report.get(f"{name}_{key}")
    if key in "ab" and (not r or not r.get("ok")):
        return (f'<div class="opt"><input type="radio" disabled id="{rid}"><label for="{rid}">{html.escape(label)}</label>'
                f'<p class="warn">Не собралось: {html.escape((r or {}).get("note", "нет исходника"))}</p></div>')
    if full:
        extra = (f'<details><summary>Что Suno выдал целиком ({r["raw_sec"]:.0f} с)</summary>'
                 f'{player(name, key + "_full")}</details>')
    return (f'<div class="opt"><input type="radio" name="{name}" id="{rid}" value="{key}">'
            f'<label for="{rid}">{html.escape(label)}</label>{player(name, key)}{extra}</div>')


def section(it):
    n, kind = it["name"], it["kind"]
    what, where = ABOUT.get(n, (BJ2_UI.get(n, ""), ""))
    full = kind != "music"
    rows = [opt(n, "cur", "принятый сейчас — оставить"), opt(n, "a", "Suno v6, версия 1", full),
            opt(n, "b", "Suno v6, версия 2", full),
            f'<div class="opt"><input type="radio" name="{n}" id="{n}-redo" value="redo">'
            f'<label for="{n}-redo">Suno — интересно, но переделать (напишите, что изменить)</label></div>']
    where_html = f"<p><b>Где:</b> {html.escape(where)}</p>" if where else ""
    return (f'''<section data-slot="{n}"><h2>{html.escape(n)}</h2>
<div class="moment"><p>{html.escape(what)}</p>{where_html}</div>
<div class="opts">{"".join(rows)}</div>
<p class="src">Задание Suno: {html.escape(it["style"])}</p>
<label class="note" for="{n}-note">Замечание (необязательно)</label>
<textarea id="{n}-note" data-note="{n}" placeholder="например: версия 1 лучше, но короче"></textarea>
<div class="state" data-state="{n}"></div></section>''')


PICKS = json.loads((HERE / "picks_1023.json").read_text(encoding="utf-8"))["picks"]
TITLES = {"bgm_title": "титул", "bgm_hotel": "отель", "bgm_below": "пещера Кухтулху", "bgm_deep": "чудовище из глубины",
          "bgm_resort": "курорт, до гидроудара", "bgm_hotel_tense": "отель после гидроудара", "bgm_epilogue": "финал и эпилог",
          "sfx_shower_run": "душ в начале игры"}
SEAMS = [n for n in TITLES if PICKS.get(n) in ("a", "b")]


def seam(n):
    v = PICKS[n]
    sec = report[f"{n}_{v}"]["sec"]
    k = 5 if n.startswith("sfx_") else 12
    sid = f"seam_{n}"
    return (f'''<section data-slot="{sid}"><h2>Шов петли: {html.escape(TITLES[n])}</h2>
<div class="moment"><p>Ваш выбор: Suno, версия {"1" if v == "a" else "2"}. В игре она крутится по кругу: петля {sec:.0f} с. Ниже {k} секунд её конца и {k} секунд начала подряд, склейка ровно посередине. Слышен ли шов?</p></div>
<div class="opts"><div class="opt"><input type="radio" name="{sid}" id="{sid}-ok" value="ok"><label for="{sid}-ok">шов не слышен</label>{player("seam", n)}</div>
<div class="opt"><input type="radio" name="{sid}" id="{sid}-redo" value="redo"><label for="{sid}-redo">шов слышен — перерезать</label></div></div>
<label class="note" for="{sid}-note">Замечание (необязательно)</label>
<textarea id="{sid}-note" data-note="{sid}" placeholder="например: на склейке пропадает бас"></textarea>
<div class="state" data-state="{sid}"></div></section>''')


parts, toc = [f'<div class="group" id="g-seams"><h1>Шаг 2 — швы петель (новое)</h1>'
              f'<p class="note">Мелодии и душ, где вы выбрали Suno, в игре звучат по кругу. Проверьте склейку каждой.</p>'
              + "\n".join(seam(n) for n in SEAMS) + "</div>"], [f'<a href="#g-seams">Швы петель ({len(SEAMS)})</a>']
parts.append('<div class="group"><h1>Шаг 1 — выбор (ваши отметки)</h1></div>')
for kind, title, about in GROUPS:
    its = [i for i in items if i["kind"] == kind]
    toc.append(f'<a href="#g-{kind}">{title} ({len(its)})</a>')
    parts.append(f'<div class="group" id="g-{kind}"><h1>{title}</h1><p class="note">{html.escape(about)}</p>'
                 + "\n".join(section(i) for i in its) + "</div>")

SCRIPT = """<script>
const SLOTS = %s;
const banner = document.getElementById('banner');
const queue = {};
function say(slot, text, cls) { const el = document.querySelector('[data-state="' + slot + '"]'); el.textContent = text; el.className = 'state ' + (cls || ''); }
function current(slot) {
  const r = document.querySelector('input[name="' + slot + '"]:checked');
  return { choice: r ? r.value : null, comment: document.getElementById(slot + '-note').value.trim() };
}
function count() {
  const done = SLOTS.filter(s => document.querySelector('input[name="' + s + '"]:checked')).length;
  document.getElementById('count').textContent = 'Отмечено: ' + done + ' из ' + SLOTS.length + ' (вместе со швами)';
}
document.addEventListener('play', e => {
  document.querySelectorAll('audio').forEach(a => { if (a !== e.target) a.pause(); });
}, true);
async function start() {
  let db = null;
  try { db = window.claude ? await window.claude.use('db') : null; } catch (e) { db = null; }
  SLOTS.forEach(slot => document.querySelectorAll('input[name="' + slot + '"]').forEach(r => r.addEventListener('change', count)));
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
    count();
  }, () => { banner.textContent = 'Связь с хранилищем отметок прервалась. Обновите страницу.'; });
}
start();
</script>""" % json.dumps([f"seam_{n}" for n in SEAMS] + [i["name"] for i in items])

page = f"""<title>Гидроудар: звук на Suno v6</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Old+Standard+TT:wght@400;700&family=PT+Sans:wght@400;700&family=PT+Mono&display=swap">
{STYLE}
<div class="wrap">
<header class="lead">
<h1>Весь звук игры на Suno v6</h1>
<p>Каждый из {len(items)} звуков игры заново сделан флагманской моделью Suno v6 (через AceDataCloud) по тому же английскому заданию, по которому делался принятый вариант. Suno на каждый запрос даёт две версии — обе здесь, рядом с принятым. Доводка и громкость — те же, что у принятых, чтобы сравнивать честно.</p>
<p>У Suno нет отдельного режима звуковых эффектов: это музыкальная модель. Для эффектов, амбиентов и щелчков к заданию добавлено «только звук, без музыки», а короткий звук вырезан из трека не меньше 10 секунд. Синтез и звуки BJ2 промпта не имели — для них задание написано по описанию из спеки.</p>
<p><b>Шаг 1 сделан</b> 23.10.2026: Suno выбран для 29 звуков — 7 мелодий из 9, стингер реликвии, 5 блипов из 6, все 7 звуков интерфейса и 9 эффектов из 48; амбиенты все остаются прежними. У звука ключа и двери лестницы (sfx_key_door) отметки нет — остаётся принятый. <b>Шаг 2:</b> проверьте швы петель ниже. После этого и вашего «да» выбранное уходит в игру.</p>
<div id="banner" class="note">Загружаю отметки…</div>
<p id="count" class="note">Отмечено: 0 из {len(items)}</p>
<nav class="toc">{"".join(toc)}</nav>
</header>
{chr(10).join(parts)}
<footer>Генерация — tools/audio/suno.py (модель chirp-v6, журнал work/suno/log.jsonl), доводка — build.py пакета. Подробности — work/audio/candidates/s8_suno_v6_1023/README.md.</footer>
</div>
{SCRIPT}
"""
(HERE / "listen.html").write_text(page, encoding="utf-8")
print("listen.html", len(page))
