// Автопрохождение через настоящий интерфейс (DoD DESIGN_BIBLE §16 п. 5): Playwright щёлкает мышью
// по зонам, пунктам меню действий, «При себе», меню выбора и окнам реплик — как игрок.
// Координаты зон берутся из живой игры (window.__bj3.game()), ответы — из логики акта.
//
//   NODE_PATH=$(npm root -g) node tools/web/autoplay.js http://127.0.0.1:8766/ [ПАПКА_СКРИНОВ]
//
// Сценарий Акта I: кратчайший путь до конца акта + негативы (ранние попытки, повторы, советы,
// сохранение и «Продолжить»). Код выхода 0 — AUTOPLAY OK.

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const URL = process.argv[2] || "http://127.0.0.1:8766/";
const OUT = process.argv[3] || "work/autoplay";
fs.mkdirSync(OUT, { recursive: true });

const fails = [];
let shot = 0;
function check(ok, msg) {
  console.log(`${ok ? "OK  " : "FAIL"} ${msg}`);
  if (!ok) fails.push(msg);
}

(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });

  const g = () => page.evaluate(() => window.__bj3.game());
  const toClient = (x, y) => page.evaluate(([x, y]) => {
    const r = document.getElementById("game").getBoundingClientRect();
    const s = Math.min(r.width / 1920, r.height / 1080);
    return { x: r.left + (r.width - 1920 * s) / 2 + x * s, y: r.top + (r.height - 1080 * s) / 2 + y * s };
  }, [x, y]);
  async function clickAt([x, y], button = "left") {
    const c = await toClient(x, y);
    await page.mouse.click(c.x, c.y, { button });
    await page.waitForTimeout(60);
  }
  const reachChecked = new Set();
  async function zonesReachable() {
    const s = await g();
    if (s.frame || reachChecked.has(s.view)) return;
    reachChecked.add(s.view);
    const bad = s.zones.filter((z) => !z.at).map((z) => z.id);
    check(bad.length === 0, `вид ${s.view}: каждую зону можно щёлкнуть${bad.length ? " — перекрыты: " + bad.join(", ") : ""}`);
  }
  async function snap(name) {
    shot += 1;
    await page.screenshot({ path: path.join(OUT, `${String(shot).padStart(2, "0")}_${name}.png`) });
  }
  // пролистать реплики и документы, дождаться, пока игра освободится
  async function settle(limit = 200) {
    for (let i = 0; i < limit; i++) {
      const s = await g();
      if (s.ended) return s;
      if (s.dialog || s.reader) { await clickAt([960, 900]); continue; }
      if (!s.busy) { if (!s.choice && !s.menuItems) await zonesReachable(); return s; }
      await page.waitForTimeout(40);
    }
    throw new Error("игра не освободилась");
  }
  async function zone(id) {
    const s = await g();
    const z = s.zones.find((v) => v.id === id);
    if (!z) throw new Error(`на виде ${s.view} нет зоны ${id}; есть: ${s.zones.map((v) => v.id).join(", ")}`);
    if (!z.at) throw new Error(`зону ${s.view}.${id} целиком перекрыли другие — по ней не щёлкнуть`);
    return z;
  }
  async function look(id) {
    await clickAt((await zone(id)).at, "right");
    return settle();
  }
  async function go(id) {
    await clickAt((await zone(id)).at);
    return settle();
  }
  async function verb(id, v) {
    await clickAt((await zone(id)).at);
    const s = await g();
    if (!s.menuItems) throw new Error(`у зоны ${id} не открылось меню действий`);
    const it = s.menuItems.find((m) => m.verb === v);
    if (!it) throw new Error(`у зоны ${id} нет действия «${v}»; есть: ${s.menuItems.map((m) => m.verb).join(", ")}`);
    await clickAt(it.at);
    return settle();
  }
  async function hasVerb(id, v) {
    await clickAt((await zone(id)).at);
    const s = await g();
    const ok = !!(s.menuItems && s.menuItems.some((m) => m.verb === v));
    await page.keyboard.press("Escape");
    return ok;
  }
  async function useItem(item, id) {
    const s = await g();
    const it = s.items.find((v) => v.id === item);
    if (!it) throw new Error(`предмета ${item} нет при себе`);
    await clickAt(it.at);
    await clickAt((await zone(id)).at);
    return settle();
  }
  async function choose(id) {
    const s = await g();
    if (!s.menuItems || !s.choice) throw new Error("меню выбора не открыто");
    const it = s.menuItems.find((m) => m.id === id);
    if (!it) throw new Error(`в меню нет пункта ${id}; есть: ${s.choice.map((c) => c.id).join(", ")}`);
    await clickAt(it.at);
    return settle();
  }
  async function back() {
    const s = await g();
    await clickAt(s.hud.back);
    return settle();
  }
  const lastSlot = (s) => s.log[s.log.length - 1];
  const has = (s, f) => s.flags.includes(f);

  // ---------------------------------------------------------------- старт
  await page.goto(URL);
  await page.waitForFunction(() => !document.getElementById("play").disabled, null, { timeout: 30000 });
  await page.click("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title" && window.__bj3.buttons().length === 4);
  const tb = await page.evaluate(() => window.__bj3.buttons());
  await clickAt([tb[0].x + 200, tb[0].y + 36]);
  await page.waitForFunction(() => window.__bj3.scene() === "game" && window.__bj3.game());
  await page.waitForTimeout(300);
  let s = await g();
  check(s.dialog && s.dialog.portrait === "portraits/port_lap_soap_neutral", "вступление: портрет без пены (OPEN.1_voucher)");
  await snap("open_voucher");
  s = await settle();
  check(s.log.slice(0, 5).join(",") === "OPEN.1_voucher,OPEN.2_shower,OPEN.3_shock,OPEN.4_after,OPEN.5_anc", "вступление OPEN.1–5 по порядку");
  check(s.view === "W1" && !s.busy, "управление у игрока, номер 317");
  await snap("w1");

  // ---------------------------------------------------------------- негативы и осмотры
  s = await look("bed");
  check(lastSlot(s) === "W1.bed", "осмотр кровати → W1.bed");
  s = await go("desk");
  check(s.view === "Z02", "стол → зум Z02");
  s = await verb("mineral", "взять");
  check(lastSlot(s) === "Z02.bottle.take", "взять бутылку → мыльный хват (Z02.bottle.take)");
  s = await verb("mineral", "взять");
  check(lastSlot(s) === "Z02.bottle.take.repeat", "повтор — короче (Z02.bottle.take.repeat)");
  // совет Предка: первое нажатие — знакомство, второе — тема plunger, третье подряд — «подожди»
  await clickAt(s.hud.hint); s = await settle();
  check(lastSlot(s) === "HINT.intro", "совет: первое нажатие — HINT.intro");
  await clickAt(s.hud.hint); s = await settle();
  check(lastSlot(s) === "HINT.plunger.1", "совет: первая тема — вантуз (HINT.plunger.1)");
  await clickAt(s.hud.hint); s = await settle();
  check(lastSlot(s) === "HINT.cooldown", "совет подряд без действия — HINT.cooldown");
  // P01 часть: меню мини-бара
  s = await verb("menu", "взять");
  check(has(s, "has_menu_card") && s.log.includes("DOC.menu"), "меню снято, прочитан DOC.menu (A11)");
  check(s.items.some((i) => i.id === "menu"), "меню — в «При себе»");
  await snap("z02_menu_taken");
  s = await back();
  check(s.view === "W1", "назад → номер");
  // N01: вантуз — сначала ошибка, потом меню кромкой
  s = await go("shower");
  check(s.view === "Z01", "душевая → зум Z01");
  s = await verb("plunger", "потянуть");
  check(lastSlot(s) === "Z01.plunger.pull" && has(s, "plunger_pull_tried"), "потянуть вантуз — не снимается (N01a)");
  s = await useItem("menu", "plunger");
  check(has(s, "plunger_taken") && !has(s, "plunger_on_panel") && lastSlot(s) === "Z01.plunger.take", "меню под край присоски — вантуз снят (N01)");
  s = await look("dispenser");
  check(s.log.includes("DOC.pictograms"), "дозатор: пиктограммы дочитаны (DOC.pictograms)");
  await snap("z01_after");
  s = await back();
  // P01: проба жидкостью
  s = await go("desk");
  s = await verb("mineral", "облиться");
  check(has(s, "foam_class_closed") && has(s, "foam_swollen"), "облиться минералкой — пена раздулась (A02)");
  check(s.log.slice(-2).join(",") === "PROBE.mineral,PROBE.rule.known", "после первой пробы — PROBE.rule.known");
  s = await verb("kombucha", "облиться");
  check(lastSlot(s) === "PROBE.repeat.1", "повторная проба — PROBE.repeat.1");
  s = await verb("phone", "позвонить");
  check(has(s, "reception_called"), "звонок на стойку (A03)");
  await snap("z02_after");
  s = await back();
  // P02: тележка
  s = await go("trolley");
  check(s.view === "Z03", "тележка → зум Z03");
  s = await verb("skirt", "под_тележку");
  check(lastSlot(s) === "Z03.under.no_peek", "под тележку до разведки — Z03.under.no_peek");
  s = await verb("handle", "толкнуть");
  check(lastSlot(s) === "Z03.trolley.push", "толкнуть со звёздами — застревает (Z03.trolley.push)");
  check(!(await hasVerb("stars", "сложить")), "«сложить звёзды» скрыто, пока звёзды не осмотрены");
  s = await look("stars");
  check(has(s, "knows_stars_fold") && lastSlot(s) === "Z03.stars.look", "осмотр звёзд — «МИНУС четыре звезды» (A05)");
  s = await verb("stars", "сложить");
  check(has(s, "stars_folded"), "звёзды сложены (A06)");
  check(!s.zones.some((z) => z.id === "plate"), "табличку под юбкой не видно, пока шторка задвинута");
  s = await verb("skirt", "снять_юбку");
  check(has(s, "knows_trolley_chamber") && has(s, "scr_skirt_open"), "юбку не снять, шторка отъехала — внутри пусто (A04)");
  check(s.zones.some((z) => z.id === "plate"), "шторка отодвинута — видна табличка на раме");
  check(!(await hasVerb("skirt", "отодвинуть")), "«отодвинуть шторку» скрыто, пока она отодвинута");
  s = await look("plate");
  check(s.log.includes("DOC.plate"), "пластина водолечебницы (DOC.plate)");
  await snap("z03_after");
  s = await back();
  check(!has(s, "scr_skirt_open"), "ушёл с зума — шторка снова задвинута (экранный флаг снят)");
  s = await go("trolley_f");
  check(!s.zones.some((z) => z.id === "plate"), "вернулся к тележке — таблички не видно");
  s = await verb("skirt", "отодвинуть");
  check(has(s, "scr_skirt_open") && s.zones.some((z) => z.id === "plate"), "«отодвинуть шторку» — табличка снова видна");
  s = await back();
  // P03: разведка — игрок сам выходит в коридор, идёт к лифту и жмёт «Вестибюль»
  s = await verb("door", "выйти");
  check(s.view === "C1" && lastSlot(s) === "SEQ.peek.1_corridor" && !has(s, "need_cover"), "дверь → коридор (SEQ.peek.1), дальше — сам игрок");
  await snap("c1_corridor");
  s = await back();
  check(s.view === "W1", "из коридора можно вернуться в номер");
  s = await verb("door", "выйти");
  check(s.view === "C1" && s.log.filter((x) => x === "SEQ.peek.1_corridor").length === 1, "второй выход в коридор — без повтора реплики");
  s = await go("lift");
  check(s.view === "L1" && lastSlot(s) === "SEQ.peek.2_lift", "щелчок по лифту → панель лифта (SEQ.peek.2)");
  await snap("l1_lift");
  s = await go("lobby");
  check(has(s, "need_cover") && s.log.includes("SEQ.peek.5_back") && s.view === "W1", "кнопка «Вестибюль» → вестибюль из кабины, назад в номер (A07)");
  s = await verb("door", "выйти");
  check(lastSlot(s) === "W1.door.again", "выйти голым ещё раз — W1.door.again");
  // проезд
  s = await go("trolley_f");
  s = await verb("skirt", "под_тележку");
  check(s.view === "W2u" && has(s, "trolley_at_crowd"), "под тележкой до толпы (A08)");
  await snap("w2u_crowd");
  s = await verb("crowd", "протолкнуться");
  check(lastSlot(s) === "W2.crowd.push", "протолкнуться — стоят стеной");
  await clickAt((await zone("crowd")).at);
  s = await g();
  const it = s.menuItems.find((m) => m.verb === "обратиться");
  await clickAt(it.at);
  s = await settle();
  check(!!s.choice && s.choice.some((c) => c.id === "shout"), "меню у толпы: есть «Осторожно, горячее!»");
  s = await choose("pass");
  check(lastSlot(s) === "CHOICE.pass", "вежливая просьба — не слышат (CHOICE.pass)");
  // сохранение и «Продолжить»: перезагрузка посреди акта
  const before = (await g()).flags.join(",");
  await page.reload();
  await page.waitForFunction(() => !document.getElementById("play").disabled, null, { timeout: 30000 });
  await page.click("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title" && window.__bj3.buttons().length === 4);
  const tb2 = await page.evaluate(() => window.__bj3.buttons());
  check(tb2.find((b) => b.id === "cont").enabled, "после перезагрузки «ПРОДОЛЖИТЬ» доступна");
  const cb = tb2.find((b) => b.id === "cont");
  await clickAt([cb.x + 200, cb.y + 36]);
  await page.waitForFunction(() => window.__bj3.scene() === "game" && window.__bj3.game());
  s = await settle();
  check(s.flags.join(",") === before && s.view === "W2u", "сохранение восстановлено: те же флаги, вид у толпы");
  // крик
  await clickAt((await zone("crowd")).at);
  s = await g();
  await clickAt(s.menuItems.find((m) => m.verb === "обратиться").at);
  await settle();
  s = await choose("shout");
  check(has(s, "trolley_service_side") && s.choice && s.choice.some((c) => c.id === "exit"), "крик: толпа расступилась, тележка за стойкой, разговор (A09)");
  await snap("talk");
  s = await choose("clothes");
  s = await choose("clothes");
  check(lastSlot(s) === "TALK.iz.again", "повтор темы — TALK.iz.again");
  s = await choose("exit");
  check(s.ended, "конец акта (END.act1)");
  check(["trolley_service_side", "shock_report_known", "iz_rules_all_shown", "w3_open", "w4_open"].every((f) => has(s, f)), "цели Акта I выполнены");
  await snap("end");

  check(errors.length === 0, `ошибок страницы нет${errors.length ? ": " + errors.join(" | ") : ""}`);
  await browser.close();
  console.log(fails.length ? `\nAUTOPLAY FAIL: ${fails.length}` : "\nAUTOPLAY OK");
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error("AUTOPLAY FAIL:", e.message); process.exit(1); });
