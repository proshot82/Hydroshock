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

// ---------------------------------------------------------------- телефон и Telegram
// Опыт BJ2 р.25–27: телефон горизонтально и вертикально (кадр «лёжа»), касания настоящими
// событиями CDP, Telegram — с заглушкой его SDK (telegram.org подменяется): весь экран, свайпы,
// фиксация горизонтали, отступы под кнопки Telegram, «Назад» Telegram, вопрос при закрытии,
// облачная копия партии (второй «телефон» с пустым браузером продолжает партию первого).

const IPHONE = { viewport: { width: 844, height: 390 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
  userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1" };
const IPHONE_V = { ...IPHONE, viewport: { width: 390, height: 844 } };
const TG_HASH = "#tgWebAppData=query_id%3Dsmoke&tgWebAppVersion=8.0&tgWebAppPlatform=ios";

// SDK Telegram в миниатюре: только то, что зовёт игра; вызовы — в window.__tg.log.
const TG_STUB = `(() => {
  const log = [];
  const cbs = {};
  const root = document.documentElement.style;
  const W = {
    isFullscreen: false, isOrientationLocked: false, platform: "ios", version: "8.0",
    isVersionAtLeast: (v) => parseFloat(v) <= 8.0,
    ready: () => log.push("ready"), expand: () => log.push("expand"),
    setHeaderColor: (c) => log.push("header " + c), setBackgroundColor: (c) => log.push("bg " + c),
    setBottomBarColor: (c) => log.push("bottombar " + c),
    disableVerticalSwipes: () => log.push("noswipe"),
    requestFullscreen: () => {
      log.push("fullscreen");
      W.isFullscreen = true;
      // как iPhone в Telegram горизонтально: вырез слева, кнопки Telegram сверху, полоска «домой» снизу
      root.setProperty("--tg-safe-area-inset-left", "47px");
      root.setProperty("--tg-safe-area-inset-bottom", "21px");
      root.setProperty("--tg-content-safe-area-inset-top", "46px");
    },
    exitFullscreen: () => { log.push("exitfullscreen"); W.isFullscreen = false; },
    lockOrientation: () => { log.push("lock " + (innerWidth > innerHeight ? "landscape" : "portrait")); W.isOrientationLocked = true; },
    enableClosingConfirmation: () => log.push("confirm on"), disableClosingConfirmation: () => log.push("confirm off"),
    onEvent: () => {},
    BackButton: { show: () => log.push("back show"), hide: () => log.push("back hide"), onClick: (f) => { cbs.back = f; } },
    HapticFeedback: { impactOccurred: () => log.push("haptic") },
    CloudStorage: {
      setItem: (k, v, cb) => window.__cloudSet(k, v).then(() => cb && cb(null, true)),
      getItem: (k, cb) => window.__cloudGet([k]).then((o) => cb(null, o[k] || "")),
      getItems: (ks, cb) => window.__cloudGet(ks).then((o) => cb(null, o)),
    },
  };
  window.Telegram = { WebApp: W };
  window.__tg = { log, back: () => cbs.back && cbs.back() };
})();`;

async function tapAt(page, cdp, x, y, hold = 40) {
  const c = await page.evaluate(([x, y]) => window.__bj3.toScreen(x, y), [x, y]);
  await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: c.x, y: c.y, id: 1 }] });
  await page.waitForTimeout(hold);
  await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  await page.waitForTimeout(120);
}

async function tapButton(page, cdp, id) {
  const b = (await page.evaluate(() => window.__bj3.buttons())).find((v) => v.id === id);
  if (!b) throw new Error(`нет кнопки ${id}`);
  await tapAt(page, cdp, b.x + b.w / 2, b.y + b.h / 2);
}

// пролистать реплики пальцем, пока игра не освободится
async function settleTouch(page, cdp) {
  for (let i = 0; i < 120; i++) {
    const s = await page.evaluate(() => window.__bj3.game());
    if (s && (s.dialog || s.reader)) { await tapAt(page, cdp, 960, 900); if (s.reader) await page.waitForTimeout(420); continue; }
    if (s && !s.busy) return s;
    await page.waitForTimeout(60);
  }
  throw new Error("игра не освободилась");
}

async function openPhone(browser, errors, opts, url, init) {
  const ctx = await browser.newContext(opts);
  if (init) await init(ctx);
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  const ready = page.waitForEvent("console", { predicate: (m) => m.text() === "BJ3 READY", timeout: 30000 });
  await page.goto(url);
  await ready;
  const cdp = await ctx.newCDPSession(page);
  return { ctx, page, cdp };
}

async function phoneAndTelegram(browser, errors) {
  // 1. iPhone в Safari, горизонтально: подсказки на карточке, касания, крупный интерфейс
  const iosSafari = async (ctx) => ctx.addInitScript(() => {
    // Safari на iPhone не умеет «весь экран» для страницы — как настоящий
    delete Element.prototype.requestFullscreen;
    delete Element.prototype.webkitRequestFullscreen;
  });
  let { ctx, page, cdp } = await openPhone(browser, errors, IPHONE, URL, iosSafari);
  const tips = await page.evaluate(() => [document.getElementById("tip-input").textContent, document.getElementById("tip-home").textContent]);
  check(/коснитесь/i.test(tips[0]) && /«Домой»/.test(tips[1]), "iPhone: на карточке — как играть пальцем и как открыть на весь экран");
  await page.screenshot({ path: path.join(OUT, "10_iphone_shell.png") });
  await page.tap("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title");
  await page.waitForTimeout(300);
  const fsBtn = (await page.evaluate(() => window.__bj3.buttons())).find((b) => b.id === "fullscreen");
  check(fsBtn && fsBtn.enabled, "iPhone: «ВО ВЕСЬ ЭКРАН» доступна (объясняет экран «Домой»)");
  await tapButton(page, cdp, "fullscreen");
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(OUT, "11_iphone_homescreen_tip.png") });
  const pf = await page.evaluate(() => ({ ...window.__bj3.platform(), ui: window.__bj3.uiScale(), touch: window.__bj3.touchMode(), rot: window.__bj3.rotated() }));
  check(pf.touch && pf.ios && !pf.rot && pf.ui > 1.2, `iPhone горизонтально: сенсорный режим, крупный интерфейс ×${pf.ui.toFixed(2)}, кадр не повёрнут`);
  await tapButton(page, cdp, "start");
  await page.waitForFunction(() => window.__bj3.scene() === "game", null, { timeout: 15000 });
  let s = await settleTouch(page, cdp);
  check(s.view === "W1", `пальцем: партия началась, вступление пролистано касаниями (вид ${s.view})`);
  // долгое касание по кровати — осмотр (правая кнопка мыши у пальца)
  const bed = s.zones.find((z) => z.id === "bed");
  const n0 = s.log.length;
  await tapAt(page, cdp, bed.at[0], bed.at[1], 650);
  s = await page.evaluate(() => window.__bj3.game());
  check(s.log.length > n0 && /^W1\.bed/.test(s.log[s.log.length - 1]), `удержание пальца на кровати — осмотр (${s.log[s.log.length - 1]})`);
  s = await settleTouch(page, cdp);
  // «назад» браузера (жест Android) — из крупного плана в комнату, а не со страницы
  const desk = s.zones.find((z) => z.id === "desk");
  await tapAt(page, cdp, desk.at[0], desk.at[1]);
  s = await settleTouch(page, cdp);
  const zoomView = s.view;
  await page.waitForTimeout(100);
  await page.goBack().catch(() => {});
  await page.waitForTimeout(300);
  s = await page.evaluate(() => window.__bj3.game());
  check(zoomView !== "W1" && s.view === "W1" && page.url().startsWith(URL), `«назад» браузера: из ${zoomView} обратно в комнату, игра на месте`);
  await page.screenshot({ path: path.join(OUT, "12_iphone_game.png") });
  await ctx.close();

  // 2. iPhone вертикально: кадр «лёжа», касание по повёрнутой «НАЧАТЬ» начинает партию
  ({ ctx, page, cdp } = await openPhone(browser, errors, IPHONE_V, URL));
  await page.tap("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title");
  await page.waitForTimeout(300);
  check(await page.evaluate(() => window.__bj3.rotated()), "телефон вертикально: кадр «лёжа»");
  await page.screenshot({ path: path.join(OUT, "13_iphone_portrait_title.png") });
  await tapButton(page, cdp, "start");
  await page.waitForFunction(() => window.__bj3.scene() === "game", null, { timeout: 15000 });
  check(true, "касание по повёрнутой «НАЧАТЬ» начало партию");
  await ctx.close();

  // 3. Telegram: весь экран, отступы, «Назад», вопрос при закрытии, облако
  const cloud = new Map();
  const tgInit = async (ctx) => {
    await ctx.route("https://telegram.org/**", (r) => r.fulfill({ contentType: "application/javascript", body: TG_STUB }));
    await ctx.exposeFunction("__cloudSet", (k, v) => { cloud.set(k, v); });
    await ctx.exposeFunction("__cloudGet", (ks) => Object.fromEntries(ks.map((k) => [k, cloud.get(k) || ""])));
  };
  ({ ctx, page, cdp } = await openPhone(browser, errors, IPHONE, URL + TG_HASH, tgInit));
  await page.waitForTimeout(500);
  let log = await page.evaluate(() => window.__tg.log.slice());
  check(["ready", "expand", "noswipe", "fullscreen", "header #000000"].every((x) => log.includes(x)),
    `Telegram: готов, развёрнут, весь экран, свайп не сворачивает, рамка чёрная (${log.join(", ")})`);
  check(log.includes("lock landscape"), "Telegram: горизонталь зафиксирована");
  const box = await page.evaluate(() => { const r = document.getElementById("game").getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; });
  check(box[0] === 47 && box[1] === 46 && box[3] === 390 - 46 - 21, `Telegram: холст обходит вырез и кнопки Telegram (${box.map(Math.round).join(", ")})`);
  check(/облаке Telegram/.test(await page.textContent("#note-save")), "Telegram: на карточке — что сохранение и в облаке");
  await page.tap("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title");
  await page.waitForTimeout(300);
  await tapButton(page, cdp, "start");
  await page.waitForFunction(() => window.__bj3.scene() === "game", null, { timeout: 15000 });
  s = await settleTouch(page, cdp);
  log = await page.evaluate(() => window.__tg.log.slice());
  check(log.includes("confirm on"), "Telegram: в партии закрыть — с вопросом");
  const desk2 = s.zones.find((z) => z.id === "desk");
  await tapAt(page, cdp, desk2.at[0], desk2.at[1]);
  s = await settleTouch(page, cdp);
  await page.waitForTimeout(100);
  log = await page.evaluate(() => window.__tg.log.slice());
  check(log.includes("back show"), `Telegram: в крупном плане (${s.view}) — кнопка «Назад» Telegram`);
  await page.evaluate(() => window.__tg.back());
  await page.waitForTimeout(200);
  s = await page.evaluate(() => window.__bj3.game());
  log = await page.evaluate(() => window.__tg.log.slice());
  check(s.view === "W1" && log.lastIndexOf("back hide") > log.lastIndexOf("back show"), "Telegram: «Назад» — в комнату, кнопка снова спрятана");
  await page.screenshot({ path: path.join(OUT, "14_telegram_game.png") });
  await page.waitForTimeout(2200);   // облако пишется через 1,5 с после последнего сохранения
  check(cloud.has("bj3_meta") && JSON.parse(cloud.get("bj3_meta")).n > 0, `Telegram: партия в облаке (${cloud.get("bj3_meta")})`);
  await ctx.close();

  // второй телефон с пустым браузером — та же партия из облака
  ({ ctx, page, cdp } = await openPhone(browser, errors, IPHONE, URL + TG_HASH, tgInit));
  await page.tap("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title");
  await page.waitForTimeout(300);
  const cont = (await page.evaluate(() => window.__bj3.buttons())).find((b) => b.id === "cont");
  check(cont && cont.enabled, "Telegram, другое устройство: «ПРОДОЛЖИТЬ» — партия из облака");
  await tapButton(page, cdp, "cont");
  await page.waitForFunction(() => window.__bj3.scene() === "game", null, { timeout: 15000 });
  s = await page.evaluate(() => window.__bj3.game());
  check(s && s.view === "W1", `Telegram, другое устройство: партия продолжена (вид ${s && s.view})`);
  await ctx.close();
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

  await phoneAndTelegram(browser, errors);

  check(errors.length === 0, `ошибок страницы нет${errors.length ? ": " + errors.join(" | ") : ""}`);
  await browser.close();
  console.log(fails.length ? `\nПРОВАЛОВ: ${fails.length}` : "\nWEB SMOKE OK");
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
