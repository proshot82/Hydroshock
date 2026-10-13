// Смок браузерной сборки в Chromium (Playwright): загрузка, «Играть», раскладка
// титула (спека §10 + поправка автора 13.10.2026), курсоры, настройки и их
// сохранение после перезагрузки, поля при разных окнах, ошибки страницы.
//
//   python tools/web/build_web.py --gfx ui --serve 8765 &
//   NODE_PATH=$(npm root -g) node tools/web/web_smoke.js http://127.0.0.1:8765/ [ПАПКА_СКРИНОВ]
//
// Код выхода 0 — всё прошло; 1 — есть провалы (печатаются).

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const URL = process.argv[2] || "http://127.0.0.1:8765/";
const OUT = process.argv[3] || "work/web_shots";
fs.mkdirSync(OUT, { recursive: true });

const fails = [];
function check(ok, msg) {
  console.log(`${ok ? "OK  " : "FAIL"} ${msg}`);
  if (!ok) fails.push(msg);
}

// точка мира 1920×1080 → точка окна (поля letterbox учтены)
async function toClient(page, x, y) {
  return page.evaluate(([x, y]) => {
    const r = document.getElementById("game").getBoundingClientRect();
    const s = Math.min(r.width / 1920, r.height / 1080);
    return { x: r.left + (r.width - 1920 * s) / 2 + x * s, y: r.top + (r.height - 1080 * s) / 2 + y * s };
  }, [x, y]);
}

async function clickButton(page, id) {
  const b = (await page.evaluate(() => window.__bj3.buttons())).find((v) => v.id === id);
  if (!b) throw new Error(`нет кнопки ${id}`);
  const p = await toClient(page, b.x + b.w / 2, b.y + b.h / 2);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(150);
}

(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=user-gesture-required"] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("requestfailed", (r) => errors.push(`запрос не прошёл: ${r.url()}`));

  const ready = page.waitForEvent("console", { predicate: (m) => m.text() === "BJ3 READY", timeout: 30000 });
  await page.goto(URL);
  await ready;
  check(true, "страница загрузилась, BJ3 READY");
  check(await page.isEnabled("#play"), "кнопка «Играть» доступна после загрузки");
  await page.screenshot({ path: path.join(OUT, "01_shell.png") });

  await page.click("#play");
  await page.waitForFunction(() => window.__bj3.started());
  await page.waitForTimeout(400);
  check(await page.evaluate(() => document.getElementById("shell").classList.contains("hidden")), "карточка загрузки скрыта");
  check(await page.evaluate(() => document.fonts.check('700 44px "PT Sans"')), "шрифт PT Sans Bold загружен");
  await page.screenshot({ path: path.join(OUT, "02_title_1280x720.png") });
  await page.waitForFunction(() => window.__bj3.audio().music === "bgm_title", null, { timeout: 15000 }).catch(() => {});
  const au = await page.evaluate(() => window.__bj3.audio());
  check(au.state === "running" && au.music === "bgm_title", `звук после «Играть»: контекст ${au.state}, музыка ${au.music}, формат ${au.format}`);

  const btns = await page.evaluate(() => window.__bj3.buttons());
  check(btns.map((b) => b.id).join(",") === "start,cont,settings,fullscreen", `кнопки титула: ${btns.map((b) => b.t).join(" / ")}`);
  btns.forEach((b, i) => {
    check(b.x === 160 && b.y === 450 + i * 92 && b.w === 400 && b.h === 72,
      `кнопка «${b.t}»: (${b.x}, ${b.y}) ${b.w}×${b.h}`);
    check(b.x + b.w / 2 === 360, `кнопка «${b.t}» по центру логотипа BJ2 (x = 360)`);
    check(b.x + b.w <= 900, `кнопка «${b.t}» не заходит на плакаты (x ≤ 900)`);
  });
  check(!btns.find((b) => b.id === "cont").enabled, "«ПРОДОЛЖИТЬ» неактивна без сохранения");

  // курсор: над кнопкой — «действие», мимо — обычный
  let p = await toClient(page, 360, 486);
  await page.mouse.move(p.x, p.y);
  await page.waitForTimeout(100);
  check((await page.evaluate(() => document.getElementById("game").style.cursor)).includes("cursor_act"), "курсор над кнопкой — cursor_act");
  p = await toClient(page, 1400, 900);
  await page.mouse.move(p.x, p.y);
  await page.waitForTimeout(100);
  check((await page.evaluate(() => document.getElementById("game").style.cursor)).includes("cursor_normal"), "курсор мимо кнопок — cursor_normal");

  await clickButton(page, "settings");
  const sb = await page.evaluate(() => window.__bj3.buttons());
  check(sb.map((b) => b.id).join(",") === "opt_music,opt_sound,opt_fasttext,back", "панель настроек: музыка, звуки, быстрый текст, назад");
  await page.screenshot({ path: path.join(OUT, "04_settings.png") });
  await clickButton(page, "opt_music");
  check((await page.evaluate(() => window.__bj3.settings())).music === false, "музыка выключается");
  await clickButton(page, "back");
  check((await page.evaluate(() => window.__bj3.buttons()))[0].id === "start", "«Назад» возвращает на титул");

  // настройки переживают перезагрузку
  const ready2 = page.waitForEvent("console", { predicate: (m) => m.text() === "BJ3 READY", timeout: 30000 });
  await page.reload();
  await ready2;
  await page.click("#play");
  await page.waitForFunction(() => window.__bj3.started());
  check((await page.evaluate(() => window.__bj3.settings())).music === false, "настройка музыки сохранилась после перезагрузки");
  await clickButton(page, "settings");
  await clickButton(page, "opt_music");
  await clickButton(page, "back");

  // клавиатура: стрелка вниз + Enter на «НАСТРОЙКИ», Esc — назад
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(150);   // раскладка кнопок обновляется на следующем кадре
  check((await page.evaluate(() => window.__bj3.buttons()))[0].id === "opt_music", "клавиатура: ↓↓ Enter открывает настройки");
  await page.keyboard.press("Escape");
  await page.waitForTimeout(150);
  check((await page.evaluate(() => window.__bj3.buttons()))[0].id === "start", "клавиатура: Esc закрывает настройки");

  // разные окна: картинка 16:9 с полями
  for (const [w, h] of [[1920, 1080], [1600, 1000], [1000, 800], [2560, 1080]]) {
    await page.setViewportSize({ width: w, height: h });
    await page.waitForTimeout(250);
    await page.screenshot({ path: path.join(OUT, `05_window_${w}x${h}.png`) });
    const c = await toClient(page, 0, 0);
    const e = await toClient(page, 1920, 1080);
    const ratio = (e.x - c.x) / (e.y - c.y);
    check(Math.abs(ratio - 16 / 9) < 0.01 && c.x >= -0.5 && c.y >= -0.5 && e.x <= w + 0.5 && e.y <= h + 0.5,
      `окно ${w}×${h}: кадр ${Math.round(e.x - c.x)}×${Math.round(e.y - c.y)} от (${c.x.toFixed(1)}, ${c.y.toFixed(1)}), 16:9`);
  }

  // браузер без Vorbis (старые Safari): звук берётся из запасного MP3
  const ctx2 = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  await ctx2.addInitScript(() => {
    const orig = HTMLMediaElement.prototype.canPlayType;
    HTMLMediaElement.prototype.canPlayType = function (t) { return /ogg/.test(t) ? "" : orig.call(this, t); };
  });
  const page2 = await ctx2.newPage();
  page2.on("pageerror", (e) => errors.push(String(e)));
  const ready3 = page2.waitForEvent("console", { predicate: (m) => m.text() === "BJ3 READY", timeout: 30000 });
  await page2.goto(URL);
  await ready3;
  await page2.click("#play");
  await page2.waitForFunction(() => window.__bj3.audio().music === "bgm_title", null, { timeout: 15000 }).catch(() => {});
  const au2 = await page2.evaluate(() => window.__bj3.audio());
  check(au2.format === "mp3" && au2.music === "bgm_title", `без Vorbis: формат ${au2.format}, музыка ${au2.music}`);
  await ctx2.close();

  check(errors.length === 0, `ошибок страницы нет${errors.length ? ": " + errors.join(" | ") : ""}`);
  await browser.close();
  console.log(fails.length ? `\nПРОВАЛОВ: ${fails.length}` : "\nWEB SMOKE OK");
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
