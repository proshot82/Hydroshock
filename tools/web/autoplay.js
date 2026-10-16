// Автопрохождение через настоящий интерфейс (DoD DESIGN_BIBLE §16 п. 5): Playwright щёлкает мышью
// по зонам, пунктам меню действий, «При себе», меню выбора и окнам реплик — как игрок.
// Координаты зон берутся из живой игры (window.__bj3.game()), ответы — из логики акта.
//
//   NODE_PATH=$(npm root -g) node tools/web/autoplay.js http://127.0.0.1:8766/ [ПАПКА_СКРИНОВ]
//
// Сценарий: Акт I (кратчайший путь + негативы: ранние попытки, повторы, советы, сохранение и
// «Продолжить»), без паузы — Акт II целиком — с ложными попытками, каскадом-ширмой, плёнками,
// разговором с Изольдой, сейвом посреди акта и концом акта; затем Акт III целиком — тележка к лестнице,
// лифт за зеркалом, трап «НАШЕ», пробный пуск, счёт под печать, накладная, спуск грузом. Код выхода 0 — AUTOPLAY OK.

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
  check(lastSlot(s) === "PROBE.kombucha", "комбуча — своя реплика (PROBE.kombucha)");
  s = await verb("mineral", "облиться");
  check(lastSlot(s) === "PROBE.repeat.1", "та же минералка ещё раз — PROBE.repeat.1");
  s = await verb("phone", "позвонить");
  check(lastSlot(s) === "Z02.phone.nonumber" && !has(s, "reception_called"), "звонить, не прочитав путёвку, — некуда: номера нет (Z02.phone.nonumber)");
  s = await look("voucher");
  check(s.log.includes("DOC.voucher"), "путёвка прочитана — номер стойки в ней");
  s = await verb("phone", "позвонить");
  check(has(s, "reception_called"), "звонок на стойку (A03)");
  s = await verb("lemonade", "облиться");
  check(lastSlot(s) === "PROBE.lemonade", "лимонад — своя реплика (каждая жидкость в первый раз — своя)");
  await snap("z02_after");
  s = await back();
  // P02: тележка
  s = await go("trolley");
  check(s.view === "Z03", "тележка → зум Z03");
  s = await verb("skirt", "под_тележку");
  check(lastSlot(s) === "Z03.under.no_peek", "в тележку до разведки — Z03.under.no_peek");
  check(!(await hasVerb("stars", "сложить")), "«сложить звёзды» скрыто, пока тележку не пробовали выкатить");
  s = await verb("handle", "толкнуть");
  check(lastSlot(s) === "Z03.trolley.push", "толкнуть со звёздами — застревает (Z03.trolley.push)");
  check(!(await hasVerb("stars", "сложить")), "«сложить звёзды» скрыто, пока звёзды не осмотрены");
  s = await look("stars");
  check(has(s, "knows_stars_fold") && lastSlot(s) === "Z03.stars.look", "осмотр звёзд — «МИНУС четыре звезды» (A05)");
  s = await verb("stars", "сложить");
  check(has(s, "stars_folded"), "звёзды сложены (A06)");
  s = await verb("juice", "облиться");
  check(lastSlot(s) === "PROBE.juice", "сок на голову — PROBE.juice");
  s = await verb("cup", "облиться");
  check(lastSlot(s) === "PROBE.coffee", "кофе на голову — PROBE.coffee");
  s = await look("egg");
  check(lastSlot(s) === "Z03.egg.look", "яйцо всмятку рядом с колпаком — своя зона (Z03.egg.look)");
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
  // в тележку — только когда голову облили всем, что есть в номере: остался бачок
  s = await go("trolley_f");
  s = await verb("skirt", "под_тележку");
  check(lastSlot(s) === "Z03.under.not_all", "в тележку, не облившись из бачка, — Z03.under.not_all");
  s = await back();
  s = await verb("cistern", "облиться");
  check(lastSlot(s) === "PROBE.cistern", "вода из бачка — PROBE.cistern");
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
  // актов для игрока нет (решение автора 14.10.2026): за последней репликой Акта I сразу идёт Акт II —
  // без заставки и кнопок; settle пролистывает и конец Акта I, и вступление Акта II
  s = await choose("exit");
  if (s.act !== 2) { await page.waitForFunction(() => window.__bj3.game() && window.__bj3.game().act === 2, null, { timeout: 30000 }); s = await settle(); }
  check(!s.ended && s.log.indexOf("END.act1") >= 0 && s.log.indexOf("END.act1") < s.log.indexOf("OPEN.counter"),
    "конец Акта I (END.act1) — и сразу Акт II, без заставки и кнопок");
  check(["trolley_service_side", "shock_report_known", "iz_rules_all_shown", "w3_open", "w4_open"].every((f) => has(s, f)), "цели Акта I выполнены");

  // ================================================================ Акт II
  const open2 = ["OPEN.counter", "OPEN.demo", "OPEN.requests", "OPEN.pa", "OPEN.pa.board", "OPEN.anc"];
  const i0 = s.log.indexOf("OPEN.counter");
  check(i0 >= 0 && s.log.slice(i0, i0 + 6).join(",") === open2.join(","), "Акт II: вступление OPEN.counter … OPEN.anc по порядку");
  check(s.view === "W2" && s.pos === "service" && has(s, "cascade_demo_seen") && has(s, "plunger_taken"),
    "Акт II: вестибюль за стойкой, показ насоса (B00), флаги Акта I при себе");
  await snap("a2_w2");
  await clickAt(s.hud.hint); s = await settle();
  check(lastSlot(s) === "HINT.check.1", "совет Акта II: первая тема — проверить выходы воды (HINT.check.1)");
  // ранний разговор о причине и пункты, которых ещё нет
  await clickAt((await zone("iz")).at);
  s = await settle();
  check(lastSlot(s) === "TALK.iz.open" && !!s.choice, "Изольда: TALK.iz.open и меню разговора");
  check(!s.choice.some((c) => c.id === "duty" || c.id === "signature" || c.id === "seal"), "в меню нет «взять дело», «подписи», «пломбы» — нечего предъявить");
  s = await choose("cause");
  check(lastSlot(s) === "TALK.req.early", "о причине до прачечной — рано (TALK.req.early)");
  s = await choose("vitrine");
  check(lastSlot(s) === "TALK.iz.vitrine", "ключ от витрины — «не запирается» (TALK.iz.vitrine)");
  s = await choose("exit");
  check(!s.choice, "разговор закончен (TALK.iz.exit)");
  // экспонат без каскада: руку видят
  s = await look("exhibit");
  check(s.log.includes("DOC.exhibit"), "экспонат издалека — табличка (DOC.exhibit)");
  s = await verb("exhibit", "подойти");
  check(lastSlot(s) === "SEQ.exhibit.nocover", "пешком к экспонату — нет (SEQ.exhibit.nocover)");
  s = await verb("trolley", "к_экспонату");
  check(s.view === "Z05" && s.pos === "exhibit", "под тележкой к экспонату → Z05");
  s = await verb("vitrine", "нажать_стекло");
  check(lastSlot(s) === "Z05.vitrine.push.seen" && !has(s, "vitrine_open"), "нажать без каскада — руку видят, дверца закрыта");
  s = await useItem("plunger", "vitrine");
  check(lastSlot(s) === "Z05.vitrine.plunger", "вантуз на дверцу — не тянется (Z05.vitrine.plunger)");
  s = await verb("skirt", "вылезти");
  check(lastSlot(s) === "W2.getout", "вылезти у экспоната — нет (W2.getout)");
  s = await go("back");
  check(s.view === "W2" && s.pos === "service" && lastSlot(s) === "SEQ.exhibit.back", "назад за стойку (SEQ.exhibit.back)");
  // каскад — ширма
  s = await go("counter");
  check(s.view === "Z04", "стойка → зум Z04");
  s = await verb("pump", "нажать_кнопку");
  check(has(s, "cascade_on") && has(s, "scr_cascade") && lastSlot(s) === "Z04.pump.use", "кнопка каскада: зал смотрит на камни (B01)");
  s = await back();
  check(s.view === "W2" && has(s, "scr_cascade"), "у стойки каскад всё ещё горит (экранный флаг живёт на W2)");
  await snap("a2_cascade");
  // сохранение посреди Акта II: экранный каскад в сейв не идёт
  const before2 = (await g()).flags.filter((f) => !f.startsWith("scr_")).join(",");
  await page.reload();
  await page.waitForFunction(() => !document.getElementById("play").disabled, null, { timeout: 30000 });
  await page.click("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title" && window.__bj3.buttons().length === 4);
  const tb3 = await page.evaluate(() => window.__bj3.buttons());
  const cb3 = tb3.find((b) => b.id === "cont");
  await clickAt([cb3.x + 200, cb3.y + 36]);
  await page.waitForFunction(() => window.__bj3.scene() === "game" && window.__bj3.game());
  s = await settle();
  check(s.act === 2 && s.flags.join(",") === before2 && !has(s, "scr_cascade"), "сейв Акта II: те же флаги, каскад погас (в сейв не идёт)");
  s = await go("counter");
  s = await verb("pump", "нажать_кнопку");
  check(lastSlot(s) === "Z04.pump.use.repeat" && has(s, "scr_cascade"), "кнопка ещё раз — Z04.pump.use.repeat");
  s = await look("forms");
  check(lastSlot(s) === "Z04.forms.look", "бланки заявок можно осмотреть (Z04.forms.look)");
  s = await verb("map", "взять");
  check(has(s, "has_hotel_map") && s.log.includes("DOC.map_hotel") && s.items.some((i) => i.id === "map"), "карта отеля из подставки (B04) — при себе");
  s = await back();
  s = await verb("trolley", "к_экспонату");
  s = await verb("vitrine", "нажать_стекло");
  check(has(s, "vitrine_open") && lastSlot(s) === "Z05.vitrine.push", "каскад горит — витрина открыта (B08)");
  s = await verb("tag", "отогнуть");
  check(has(s, "meter_reading_seen") && s.log.includes("DOC.tag"), "бирка отогнута: 40 712 (B08)");
  s = await useItem("plunger", "seal");
  check(has(s, "seal_is_mark") && lastSlot(s) === "Z05.seal.plunger.early", "вантуз у пломбы до журнала — одна форма (B09)");
  await snap("a2_z05");
  s = await go("back");
  // прачечная: каскад гаснет
  s = await verb("corridor", "в_прачечную");
  check(s.view === "W3" && lastSlot(s) === "W3.enter" && !has(s, "scr_cascade"), "прачечная: W3.enter, каскад погас");
  s = await verb("tanks", "облиться");
  check(lastSlot(s) === "Z06.tank.probe", "ковш из бака на голову — пена (Z06.tank.probe)");
  s = await go("drums");
  s = await look("drums");
  check(has(s, "drums_same_time") && lastSlot(s) === "Z06.drums.look", "барабаны: одна минута на всех табло (B02)");
  s = await verb("hatch", "открыть_люк");
  check(lastSlot(s) === "Z06.hatch.open", "люк заблокирован (Z06.hatch.open)");
  s = await back();
  s = await go("cabinet");
  s = await verb("inner", "открыть");
  check(has(s, "relic_r2") && s.log.includes("DOC.postcard"), "открытка «тов. К.» (R2)");
  s = await back();
  s = await verb("door", "в_зал");
  check(s.view === "W4" && lastSlot(s) === "W4.enter", "зал прекраснодушия (W4.enter)");
  s = await verb("stairs", "открыть");
  check(lastSlot(s) === "W4.stairs.locked", "служебная дверь заперта (W4.stairs.locked)");
  // доска почёта
  s = await go("board");
  s = await look("board");
  check(has(s, "paint_act_read") && s.log.includes("DOC.paint_act"), "доска почёта: акт малярной приёмки (B11)");
  s = await verb("paint", "тереть");
  check(lastSlot(s) === "Z09.paint.rub", "пальцами краска размазывается (Z09.paint.rub)");
  s = await useItem("plunger", "paint");
  check(lastSlot(s) === "Z09.paint.plunger", "вантуз — без кромки (Z09.paint.plunger)");
  s = await useItem("menu", "paint");
  check(has(s, "name_revealed") && has(s, "menu_smeared") && s.log.includes("DOC.plate_k"), "меню соскоблило краску: «Старший по воде — тов. К.» (B12)");
  check(s.items.some((i) => i.id === "menu_p") && !s.items.some((i) => i.id === "menu"), "меню в «При себе» — в бежевых полосах");
  s = await verb("slot", "нажать_заслонку");
  check(has(s, "relic_r1") && s.log.includes("DOC.token"), "жетон из щели (R1)");
  await snap("a2_z09");
  s = await back();
  // архивный стол и плёнки
  s = await go("table");
  check(s.view === "Z10", "архивный стол → зум Z10");
  s = await useItem("map", "table");
  check(lastSlot(s) === "Z10.films.elsewhere", "карта на стол — совмещать не по чему (Z10.films.elsewhere)");
  s = await verb("papers", "читать_распоряжение");
  check(has(s, "layoff_read") && s.log.includes("DOC.layoff"), "распоряжение о сокращении (B13)");
  s = await look("tube");
  check(has(s, "photo_seen") && s.log.includes("DOC.map_1908") && s.log.includes("DOC.photo"), "тубус: план 1908 и фото «Четвергъ»");
  s = await useItem("map", "glass");
  check(has(s, "overlay_by_frame") && lastSlot(s) === "Z10.films.lay", "плёнки по рамкам — источник в трёх местах (B05)");
  await snap("a2_films_frames");
  s = await verb("glass", "по_куполу");
  check(lastSlot(s) === "Z10.films.dome", "по куполу — купола нет (Z10.films.dome)");
  s = await back();
  // разговор: причина и взять дело сантехника — до совмещения плёнок
  s = await verb("back", "в_вестибюль");
  check(s.view === "W2" && s.log.includes("W2.pa.more"), "в вестибюль: громкая связь зовёт в зал (W2.pa.more)");
  await clickAt((await zone("iz")).at);
  s = await settle();
  s = await choose("cause");
  check(has(s, "requests_stapled") && has(s, "knows_supply_cut") && s.log.slice(-2).join(",") === "TALK.req.open,TALK.req.cut", "одна остановка выше по линии: заявки сшиты (B03)");
  check(s.choice && s.choice.some((c) => c.id === "duty"), "в меню — «взять дело сантехника на себя»");
  s = await choose("signature");
  check(has(s, "iz_defends_seen") && lastSlot(s) === "TALK.iz.signature", "подпись на акте — казённая стена (B20)");
  s = await choose("duty");
  check(has(s, "has_stairs_key") && has(s, "iz_admits_facts") && has(s, "counter_notice_read"), "обязанность сантехника — признание и ключ (B14)");
  check(s.log.slice(-5).join(",") === "TALK.iz.duty,TALK.iz.folder,DOC.notice_counter,TALK.iz.ladder,TALK.iz.key", "признание по порядку: дело, папка, уведомление, стремянка, ключ");
  s = await choose("exit");
  await snap("a2_key");
  // ключ есть, планы не совмещены — вниз не идёт
  s = await verb("corridor", "в_зал");
  s = await useItem("key", "stairs");
  check(lastSlot(s) === "W4.stairs.no_plan" && !has(s, "stairs_open"), "ключ без совмещённых планов — вслепую не спускается");
  s = await go("table");
  s = await verb("hatch", "совместить_с_люком");
  check(has(s, "topology_known") && lastSlot(s) === "Z10.films.align", "нарисованный источник на люк — одна вертикаль (B06)");
  await snap("a2_films_aligned");
  s = await back();
  s = await verb("stairs", "открыть");
  check(has(s, "stairs_open") && s.view === "Z12" && s.log.slice(-2).join(",") === "SEQ.stairs.open,Z12.enter", "лестница открыта, внизу площадка (B15)");
  s = await verb("notice", "сорвать");
  check(lastSlot(s) === "Z12.seal.tear", "пломбу не срывает (Z12.seal.tear)");
  s = await verb("door", "постучать");
  check(lastSlot(s) === "Z12.door.knock" && !s.ended, "стук — тишина; акт ещё не кончен");
  s = await look("door");
  check(has(s, "midpoint_known") && s.log.includes("END.act2"), "уведомление на двери и итог акта (END.act2)");
  check(["midpoint_known", "stairs_open", "office_notice_read", "iz_admits_facts"].every((f) => has(s, f)), "цели Акта II выполнены");
  await snap("a2_end");
  if (!s.ended && s.act !== 3) { await page.waitForFunction(() => window.__bj3.game() && window.__bj3.game().act === 3, null, { timeout: 30000 }); }
  s = await settle();

  // ================================================================ Акт III
  check(s.act === 3 && s.log.indexOf("END.act2") < s.log.indexOf("OPEN.door"), "конец Акта II — и сразу Акт III, без заставки");
  const open3 = ["OPEN.door", "OPEN.pa", "OPEN.anc"];
  const j0 = s.log.indexOf("OPEN.door");
  check(s.log.slice(j0, j0 + 3).join(",") === open3.join(","), "Акт III: вступление OPEN.door, OPEN.pa, OPEN.anc по порядку");
  check(s.view === "Z12" && s.pos === "service" && has(s, "midpoint_known"), "Акт III: у двери конторы, тележка за стойкой, флаги Акта II при себе");
  await snap("a3_z12");
  await clickAt(s.hud.hint); s = await settle();
  check(lastSlot(s) === "HINT.order.1", "совет Акта III: первая тема — порядок у двери (HINT.order.1)");
  s = await verb("door", "постучать");
  check(lastSlot(s) === "Z12.door.knock.again" && !s.ended, "стук — тишина (Z12.door.knock.again)");
  s = await look("instr");
  check(has(s, "knows_order_trolley") && s.log.slice(-2).join(",") === "Z12.instr.read,DOC.instr1908", "инструкция 1908 года: бутыль на тележке и доклад (C01)");
  s = await go("up");
  check(s.view === "W4", "наверх, в зал");
  s = await verb("back", "в_вестибюль");
  check(s.view === "W2" && !s.log.slice(-2).includes("W2.pa.more"), "в вестибюль; объявление Акта III — позже, после выноса дизайна");
  await clickAt((await zone("iz")).at);
  s = await settle();
  check(lastSlot(s) === "TALK.iz.after" && !!s.choice, "Изольда: TALK.iz.after и меню разговора");
  check(!s.choice.some((c) => ["invoice", "bill", "accuse", "mirror"].includes(c.id)), "в меню нет счёта, накладной, зеркала — ещё нечего предъявить");
  s = await choose("kefir");
  check(has(s, "iz_kefir_refused") && lastSlot(s) === "TALK.iz.kefir", "кефир до счёта — личное имущество (O04)");
  s = await choose("exit");
  // тележка в зал и к лестнице
  s = await verb("trolley", "в_зал_с_тележкой");
  check(s.view === "W4" && s.pos === "hall" && has(s, "trolley_in_hall") && lastSlot(s) === "SEQ.trolley.hall", "тележка служебным коридором в зал (C02, кадр 1)");
  s = await verb("trolley", "спустить_тележку");
  check(has(s, "knows_lift_exists") && s.pos === "hall" && lastSlot(s) === "W4.stairs.trolley", "винтовая лестница тележку не пускает — был лифт (C02)");
  s = await verb("trolley", "спустить_тележку");
  check(lastSlot(s) === "W4.stairs.carry", "нести на руках — нет (W4.stairs.carry)");
  s = await look("floor");
  check(lastSlot(s) === "W4.lift.search", "мозаика с фото — только в зале (W4.lift.search)");
  await snap("a3_w4_trolley");
  s = await go("table");
  s = await look("photo");
  check(has(s, "knows_lift_in_hall") && lastSlot(s) === "DOC.photo" && s.log.includes("Z10.photo.again"), "фото «Четвергъ» и пол зала: решётка стояла здесь (C03)");
  s = await look("water");
  check(s.log.slice(-2).join(",") === "Z10.water.look,DOC.water_stand", "стойка «Наследие»: историческая вода (DOC.water_stand)");
  s = await verb("water", "взять");
  check(lastSlot(s) === "Z10.water.carry", "нести бутылку в руках — нет (Z10.water.carry)");
  s = await verb("water", "облиться");
  check(lastSlot(s) === "Z10.water.head", "историческая вода на голову — пена (Z10.water.head)");
  s = await verb("water", "на_тележку");
  check(has(s, "offering_on_trolley") && lastSlot(s) === "Z10.water.offer", "вода «Каскадъ» на тележку — проверить подношение (C08)");
  s = await back();
  // зеркало
  s = await go("mirror");
  check(s.view === "Z11", "зеркало → зум Z11");
  s = await useItem("plunger", "mirror");
  check(!has(s, "mirror_removed") && lastSlot(s) === "FB.plunger.act3", "вантуз на зеркало до порожка — держать нечего");
  s = await look("mirror");
  check(has(s, "knows_door_behind_mirror") && lastSlot(s) === "Z11.threshold.look", "под зеркалом латунный порожек (C04)");
  s = await verb("mirror", "потянуть_зеркало");
  check(has(s, "mirror_tried") && lastSlot(s) === "Z11.mirror.pull", "мыльными пальцами за стекло не ухватиться (O01)");
  s = await verb("mirror", "отклеить");
  check(lastSlot(s) === "Z11.sticker.peel", "наклейка отходит, зеркало нет (Z11.sticker.peel)");
  s = await useItem("menu_p", "mirror");
  check(lastSlot(s) === "Z11.mirror.menu", "меню за раму не просунуть (Z11.mirror.menu)");
  s = await useItem("plunger", "mirror");
  check(has(s, "mirror_removed") && has(s, "lift_gate_seen") && s.log.slice(-2).join(",") === "Z11.mirror.plunger,PA.mirror", "вантуз как присоска стекольщика: зеркало снято (C05), громкая связь");
  await snap("a3_z11_gate");
  s = await look("stencil");
  check(s.log.slice(-3).join(",") === "Z11.gate.look,DOC.stencil,DOC.post", "трафарет и пост: людей не возить");
  s = await look("cabin");
  check(has(s, "cabin_seen") && has(s, "chalk_seen") && s.log.includes("Z11.cabin.look"), "решётка открыта: склад дизайна и мел сантехника (C06)");
  s = await verb("cabin", "вкатить_тележку");
  check(lastSlot(s) === "Z11.cabin.trolley.full", "кабина забита — тележке некуда (Z11.cabin.trolley.full)");
  s = await verb("cabin", "банки");
  check(s.log.slice(-2).join(",") === "Z11.cabin.paint,DOC.paint_can", "банки: та самая краска «Наследие» (DOC.paint_can)");
  s = await verb("switch", "повернуть_рубильник");
  check(has(s, "switch_tried") && lastSlot(s) === "Z11.switch.use", "рубильник: лампа гаснет — и обратно (O03)");
  s = await verb("switch", "стереть_мел");
  check(lastSlot(s) === "Z11.chalk.wipe", "мел не стирает (Z11.chalk.wipe)");
  s = await verb("cabin", "вынести_дизайн");
  check(has(s, "junk_out") && s.log.slice(-2).join(",") === "Z11.cabin.clear,PA.cabin", "наклейки — вон, мел — на месте (C07), громкая связь");
  s = await verb("board2", "выбросить");
  check(has(s, "ramp_thrown") && lastSlot(s) === "Z11.board.throw", "доска «НАШЕ» в кучу — ошибка (O12)");
  s = await verb("cabin", "вкатить_тележку");
  check(lastSlot(s) === "Z11.cabin.trolley.step" && !has(s, "cabin_free"), "колёса упираются в порожек (Z11.cabin.trolley.step)");
  await clickAt(s.hud.hint); s = await settle();
  check(/^HINT\.ramp\./.test(lastSlot(s)), "совет: тема трапа");
  s = await back();
  await snap("a3_w4_design");
  s = await verb("design_board", "достать_доску");
  check(!has(s, "ramp_thrown") && lastSlot(s) === "Z11.board.return", "доску достал из кучи (Z11.board.return)");
  s = await go("lift");
  check(!(await hasVerb("cabin", "отправить_тележку")), "без трапа тележку не отправить");
  s = await verb("board2", "положить_трапом");
  check(has(s, "ramp_set") && has(s, "cabin_free") && lastSlot(s) === "Z11.ramp.set", "доска «НАШЕ» трапом через порожек (C07b)");
  s = await verb("cabin", "встать_в_кабину");
  check(lastSlot(s) === "Z11.lift.ride.early", "встать в кабину самому — рано (Z11.lift.ride.early)");
  s = await verb("cabin", "отправить_тележку");
  check(has(s, "test_run_done") && has(s, "has_bill") && has(s, "bill_read") && s.pos === "hall", "пробный пуск: вода уехала, тележка вернулась с почтой (C09, C10)");
  check(["SEQ.test.send", "SEQ.test.call", "DOC.note", "DOC.tray_stamp", "Z11.bill.read", "DOC.bill"].every((x) => s.log.includes(x)), "пуск, вызов, записка, поднос, счёт — по порядку");
  check(s.log.includes(has(s, "board_restored") ? "Z11.bill.plate.done" : "Z11.bill.plate.todo"), "строка счёта о табличке — по тому, восстановлена ли она");
  check(s.items.some((i) => i.id === "bill"), "счёт — в «При себе»");
  await snap("a3_bill");
  s = await verb("post", "ждать_воду");
  check(lastSlot(s) === "Z11.wait.water", "воды нет и не будет (Z11.wait.water)");
  s = await back();
  s = await verb("trolley", "за_стойку");
  check(has(s, "trolley_back_at_counter") && s.view === "W2" && s.pos === "service" && lastSlot(s) === "SEQ.bill.counter", "служебным коридором за стойку (C11)");
  // плательщик
  s = await go("counter");
  s = await look("complaints");
  check(has(s, "knows_mp_habit") && s.log.slice(-2).join(",") === "Z04.stamp.watch,DOC.complaint", "Изольда штампует жалобы, глядя только на «М.П.» (C12)");
  s = await back();
  await clickAt((await zone("iz")).at);
  s = await settle();
  s = await choose("accuse");
  check(lastSlot(s) === "TALK.iz.accuse" && !has(s, "iz_confessed"), "«это вы носили кефир» — стена");
  s = await choose("stamp");
  check(lastSlot(s) === "TALK.iz.stamp", "печать — только на документы отеля");
  s = await choose("bill");
  check(has(s, "iz_forwards_bill") && lastSlot(s) === "TALK.iz.bill", "счёт в руки — передан персоналу (O05)");
  s = await choose("exit");
  s = await go("counter");
  s = await useItem("bill", "complaints");
  check(has(s, "bill_stamped") && has(s, "iz_confessed") && has(s, "kefir_ready") && has(s, "invoice_ready"), "счёт под печать: признание и оплата (C13)");
  check(s.log.slice(-4).join(",") === "Z04.bill.under,TALK.iz.confess,SEQ.iz.payment,DOC.invoice", "печать, признание, накладная — по порядку");
  check(!s.items.some((i) => i.id === "bill"), "счёт больше не «При себе» — он с печатью на стойке");
  await snap("a3_z04_payment");
  s = await verb("kefir", "взять");
  check(has(s, "grip_refused_bottle") && lastSlot(s) === "Z04.kefir.take", "кефир мыльной рукой — чуть не лужа (O06)");
  s = await verb("kefir", "взять_накладную");
  check(s.log.slice(-2).join(",") === "Z04.invoice.take,DOC.invoice", "накладная в мыльных руках раскиснет");
  s = await back();
  check(!(await hasVerb("trolley", "подкатить")), "подкатить тележку — только когда накладная заполнена");
  await clickAt((await zone("iz")).at);
  s = await settle();
  s = await choose("carry");
  check(lastSlot(s) === "TALK.iz.carry", "отнести вниз — стойку не оставит");
  s = await choose("invoice");
  check(has(s, "invoice_filled") && s.log.slice(-2).join(",") === "TALK.iz.invoice,DOC.invoice", "доклад для накладной: 40 712, табличка восстановлена (C13b)");
  s = await choose("exit");
  s = await verb("trolley", "подкатить");
  check(has(s, "payment_loaded") && lastSlot(s) === "SEQ.load", "сухие руки Изольды ставят кефир на тележку (C14)");
  await snap("a3_w2_loaded");
  // сохранение посреди Акта III
  const before3 = (await g()).flags.filter((f) => !f.startsWith("scr_")).join(",");
  await page.reload();
  await page.waitForFunction(() => !document.getElementById("play").disabled, null, { timeout: 30000 });
  await page.click("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title" && window.__bj3.buttons().length === 4);
  const tb4 = await page.evaluate(() => window.__bj3.buttons());
  const cb4 = tb4.find((b) => b.id === "cont");
  await clickAt([cb4.x + 200, cb4.y + 36]);
  await page.waitForFunction(() => window.__bj3.scene() === "game" && window.__bj3.game());
  s = await settle();
  check(s.act === 3 && s.flags.join(",") === before3 && s.pos === "service", "сейв Акта III: те же флаги, тележка за стойкой");
  s = await verb("trolley", "в_зал_с_тележкой");
  check(has(s, "iz_reported_pa") && has(s, "payment_in_hall") && s.view === "W4" && s.pos === "hall", "Изольда докладывает по громкой связи, тележка с оплатой в зале (C15)");
  check(s.log.slice(-1)[0] === "SEQ.report", "SEQ.report");
  s = await go("stairs");
  s = await verb("door", "постучать");
  check(has(s, "door_still_closed") && lastSlot(s) === "Z12.door.payment", "пешком без тележки — не принимают (O07)");
  s = await go("up");
  s = await go("lift");
  s = await verb("cabin", "встать_в_кабину");
  check(has(s, "people_ban_read") && lastSlot(s) === "Z11.ride.standing", "встать рядом с тележкой — людей не возят (O08)");
  await clickAt(s.hud.hint); s = await settle();
  check(/^HINT\.down\./.test(lastSlot(s)), "совет: тема спуска");
  s = await verb("cabin", "искать_кнопку");
  check(lastSlot(s) === "Z11.cabin.button", "кнопок внутри нет, решётку можно закрыть изнутри (Z11.cabin.button)");
  s = await verb("cabin", "под_тележку");
  { const r0 = s.log.lastIndexOf("SEQ.ride"); check(r0 >= 0 && s.log.slice(r0, r0 + 3).join(",") === "SEQ.ride,SEQ.descent,END.act3", "под тележкой грузом вниз: спуск и конец акта (C16)"); }
  check(["in_receiving_point", "payment_delivered", "iz_reported_pa", "iz_confessed"].every((f) => has(s, f)), "цели Акта III выполнены");
  await snap("a3_end");
  if (s.act !== 4) { await page.waitForFunction(() => window.__bj3.game() && window.__bj3.game().act === 4, null, { timeout: 30000 }); }
  s = await settle();

  // ================================================================ Акт IV
  const open4 = ["OPEN.arrive", "OPEN.steps", "OPEN.anc", "SEQ.rollout", "SEQ.goods", "SEQ.debt", "SEQ.note_fix", "DOC.note_fixed", "SEQ.trolley_return", "DOC.plate_mark", "SEQ.wait"];
  const k0 = s.log.indexOf("OPEN.arrive");
  check(s.act === 4 && k0 > s.log.indexOf("END.act3"), "конец Акта III — и сразу Акт IV, без заставки");
  check(s.log.slice(k0, k0 + open4.length).join(",") === open4.join(","), "Акт IV: прибытие, шаги, приёмка груза, долг, записка, тележка на баланс, ожидание — по порядку (E01)");
  check(s.view === "W5u" && has(s, "kuh_wants_hello") && has(s, "goods_accepted") && !has(s, "lap_out"), "под тележкой у стола приёма; груз принят, ждут докладчика");
  await snap("a4_w5u");
  await clickAt(s.hud.hint); s = await settle();
  check(lastSlot(s) === "HINT.out.1", "совет Акта IV: тема «вылезти» (HINT.out.1)");
  s = await verb("kuh", "поздороваться");
  check(has(s, "under_refused") && lastSlot(s) === "TALK.kuh.under", "из-под тележки — инвентарь не докладывается (O01)");
  s = await verb("kuh", "высунуть_руку");
  check(lastSlot(s) === "W5.hand", "рука — руки не докладываются (W5.hand)");
  s = await verb("skirt", "обернуться_юбкой");
  check(has(s, "cover_tried") && lastSlot(s) === "W5.cover.skirt", "юбка не снимается (O02)");
  s = await verb("skirt", "прикрыться_меню");
  check(lastSlot(s) === "W5.cover.menu", "меню «Кефир исключён» — лучше уж голым (W5.cover.menu)");
  s = await verb("table", "ждать");
  check(lastSlot(s) === "W5.wait_more", "подождать — долг с девяносто первого ждёт (W5.wait_more)");
  s = await verb("skirt", "вылезти");
  check(has(s, "lap_out") && s.view === "W5" && lastSlot(s) === "SEQ.come_out", "вылез и встал перед тележкой: стол приёма в полный рост (E02)");
  await snap("a4_w5");
  s = await go("door");
  check(lastSlot(s) === "W5.door.early" && !has(s, "in_office"), "контора заперта до доклада (W5.door.early)");
  s = await look("sign");
  check(s.log.slice(-2).join(",") === "W5.sign.read,DOC.reception_sign", "табличка: «Доставившему — доложиться»");
  s = await verb("kuh", "доложиться");
  check(has(s, "reported") && s.log.slice(-3).join(",") === "SEQ.hello,SEQ.report_line,SEQ.doors", "здравствуйте, доклад о водоснабжении, двери открыты (E03)");
  s = await go("door");
  check(has(s, "in_office") && s.view === "W6" && lastSlot(s) === "SEQ.office", "в контору своими ногами (E04)");
  await snap("a4_w6");
  await clickAt((await zone("kuh")).at);
  s = await settle();
  check(!!s.choice && !s.choice.some((c) => c.id === "photo"), "разговор с Кухтулху; про родню — только после фотографии");
  s = await choose("kefir");
  check(lastSlot(s) === "TALK.kuh.kefir", "почему кефир — тариф 1908 года (TALK.kuh.kefir)");
  s = await choose("plate");
  check(lastSlot(s) === "TALK.kuh.plate", "про табличку (TALK.kuh.plate)");
  s = await choose("exit");
  s = await go("ledge");
  check(s.view === "Z13", "уступ с журналом → Z13");
  s = await look("photo");
  check(has(s, "family_photo_seen") && s.log.slice(-2).join(",") === "Z13.photo.look,DOC.photo_family", "семейное фото: дед (O03)");
  s = await look("ledger");
  check(s.log.slice(-2).join(",") === "Z13.ledger.look,DOC.ledger", "журнал: графа «Доложилъ» пустая");
  s = await verb("ledger", "расписаться_ручкой");
  check(has(s, "pen_slipped") && lastSlot(s) === "Z13.ledger.pen", "ручка выскальзывает (O04)");
  s = await verb("ledger", "расписаться_пальцем");
  check(has(s, "thumb_smeared") && lastSlot(s) === "Z13.ledger.thumb", "палец — мыльное пятно, отметка круглая (O05)");
  s = await verb("valve", "повернуть_маховик");
  check(has(s, "valve_refused") && !has(s, "water_restored") && lastSlot(s) === "Z13.valve.sealed", "задвижка под пломбой — пломбу снимает она (O06)");
  s = await verb("mug", "облиться");
  check(lastSlot(s) === "FB.kefir.head", "кефир на голову — нет, это оплата (FB.kefir.head)");
  s = await back();
  // кружка Изольды — наверх и обратно
  s = await go("stairs");
  check(s.view === "Z12" && lastSlot(s) === "SEQ.upstairs", "дверь конторы на лестницу открыта (SEQ.upstairs)");
  s = await go("up");
  s = await verb("back", "в_вестибюль");
  s = await go("counter");
  s = await verb("lowdrawer", "нажать_ящик");
  check(has(s, "relic_r3") && lastSlot(s) === "Z04.mug.act4", "кружка Изольды из нижнего ящика (R3)");
  s = await back();
  s = await verb("corridor", "в_зал");
  s = await go("stairs");
  s = await go("door");
  check(s.view === "W6", "обратно в контору");
  s = await go("ledge");
  check(["token", "postcard", "rmug"].every((id) => s.zones.some((z) => z.id === id)), "все три вещи на её уступе: жетон, открытка, кружка");
  s = await look("rmug");
  check(lastSlot(s) === "Z13.relics.look", "«Принято. Без накладной, как личное» (Z13.relics.look)");
  await snap("a4_z13_relics");
  s = await useItem("plunger", "ledger");
  check(has(s, "marks_exchanged") && s.log.slice(-2).join(",") === "Z13.plunger.mark,DOC.ledger", "вантуз в графу «Доложилъ» — встречный оттиск, пломба снята (E05)");
  s = await verb("valve", "повернуть_маховик");
  check(has(s, "water_restored") && ["Z13.valve.turn", "PA.final", "SEQ.finale", "EPI.3", "DOC.menu_new"].every((x) => s.log.includes(x)), "маховик: вода пошла, громкая связь тонет, финал, эпилог с тремя вещами (E06, EPI.3)");
  check(["reported", "marks_exchanged", "water_restored"].every((f) => has(s, f)), "цели Акта IV выполнены");
  check(s.ended, "после эпилога — карточка «Конец»");
  await snap("a4_end");
  // H05: сохранение после финала — после перезагрузки снова «Конец», эпилог не пересчитывается
  const fin = (await g()).flags.join(",");
  await page.reload();
  await page.waitForFunction(() => !document.getElementById("play").disabled, null, { timeout: 30000 });
  await page.click("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title" && window.__bj3.buttons().length === 4);
  const tb5 = await page.evaluate(() => window.__bj3.buttons());
  const cb5 = tb5.find((b) => b.id === "cont");
  await clickAt([cb5.x + 200, cb5.y + 36]);
  await page.waitForFunction(() => window.__bj3.scene() === "game" && window.__bj3.game());
  await page.waitForTimeout(500);
  s = await g();
  check(s.act === 4 && s.ended && s.flags.join(",") === fin && !s.dialog && !s.log.includes("EPI.3"), "H05: «Продолжить» после финала — снова «Конец», эпилог не пересчитывается");

  check(errors.length === 0, `ошибок страницы нет${errors.length ? ": " + errors.join(" | ") : ""}`);
  await browser.close();
  console.log(fails.length ? `\nAUTOPLAY FAIL: ${fails.length}` : "\nAUTOPLAY OK");
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error("AUTOPLAY FAIL:", e.message); process.exit(1); });
