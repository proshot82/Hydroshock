// Видеопрохождение на 100 %: проигрывает план tools/web/plan_full.py через настоящий интерфейс
// (мышь двигается и щёлкает, как у игрока) и пишет видео со звуком изнутри страницы (rec_page.js).
// Реплики не проматываются: каждая допечатывается и стоит на экране время на чтение.
// Ответвления плана (другой порядок действий — реплики, которых нет на основном пути): перед ним
// снимок сохранения, после — «Сохранить и выйти», на титуле снимок возвращается, «Продолжить».
//
//   NODE_PATH=$(npm root -g) node tools/web/record_full.js http://127.0.0.1:8766/ work/fullrun/plan.json work/fullrun [АКТЫ]
//
// Пишет ПАПКА/actN.webm (по файлу на акт) и ПАПКА/record_log.json: что показано, расхождения с планом.

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const URL = process.argv[2] || "http://127.0.0.1:8766/";
const PLAN = JSON.parse(fs.readFileSync(process.argv[3] || "work/fullrun/plan.json", "utf8")).plan;
const OUT = process.argv[4] || "work/fullrun";
const ONLY = process.argv[5] ? new Set(process.argv[5].split(",").map(Number)) : null;
fs.mkdirSync(OUT, { recursive: true });

const CPS = 40;                         // скорость печати реплик в движке (dialog.js)
const readTime = (n) => 900 + n * 28;   // мс на чтение строки после допечатки
const docTime = (n) => 2500 + n * 22;   // мс на бумагу

const report = { mismatches: [], shown: [], errors: [] };

(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await ctx.newPage();
  if (process.env.FAST) {   // проверка плана без записи пауз: все ожидания — не дольше 20 мс
    const wt = page.waitForTimeout.bind(page);
    page.waitForTimeout = (t) => wt(Math.min(t, 20));
  }
  let outFd = null;
  await page.exposeFunction("__recChunk", (b64) => { if (outFd !== null) fs.writeSync(outFd, Buffer.from(b64, "base64")); });
  await page.addInitScript({ path: path.join(__dirname, "rec_page.js") });
  page.on("pageerror", (e) => report.errors.push(String(e)));

  const g = () => page.evaluate(() => window.__bj3.game());
  const docs = {};
  const toClient = (x, y) => page.evaluate(([x, y]) => {
    const r = document.getElementById("game").getBoundingClientRect();
    const s = Math.min(r.width / 1920, r.height / 1080);
    return { x: r.left + (r.width - 1920 * s) / 2 + x * s, y: r.top + (r.height - 1080 * s) / 2 + y * s };
  }, [x, y]);
  let mouse = { x: 960, y: 540 };
  async function moveTo([x, y]) {
    const c = await toClient(x, y);
    const d = Math.hypot(c.x - mouse.x, c.y - mouse.y);
    await page.mouse.move(c.x, c.y, { steps: Math.max(4, Math.min(30, Math.round(d / 40))) });
    mouse = c;
  }
  async function clickAt(p, button = "left", pause = 350) {
    await moveTo(p);
    await page.waitForTimeout(pause);
    await page.mouse.click(mouse.x, mouse.y, { button });
    await page.waitForTimeout(80);
  }
  async function caption(t) {
    await page.evaluate((t) => window.__recCaption && window.__recCaption(t), t);
  }

  // реплики и бумаги — с паузой на чтение; дождаться, пока игра освободится
  let curAct = 0;
  async function settle() {
    let lastKey = null;
    for (let i = 0; i < 20000; i++) {
      const s = await g();
      if (!s) { await page.waitForTimeout(100); continue; }
      if (s.ended) return s;
      if (curAct && s.act !== curAct) return s;   // начался следующий акт — его запишет свой файл
      if (s.reader) {
        const n = (docs[s.reader] || "").length;
        await page.waitForTimeout(docTime(n));
        await clickAt([960, 1000], "left", 200);
        continue;
      }
      if (s.dialog) {
        const key = `${s.log.length}|${s.dialog.i}|${s.dialog.t}`;
        if (key !== lastKey) {
          lastKey = key;
          const n = [...s.dialog.t].length;
          await page.waitForTimeout((n / CPS) * 1000 + readTime(n));
          await clickAt([1500, 960], "left", 120);
          continue;
        }
        // та же строка: щелчок лишь допечатал её — ещё щелчок
        await page.waitForTimeout(300);
        await clickAt([1500, 960], "left", 60);
        continue;
      }
      if (!s.busy) return s;
      await page.waitForTimeout(50);
    }
    throw new Error("игра не освободилась");
  }
  async function zone(id) {
    let s = await g();
    for (let i = 0; i < 40 && s.zones.some((v) => v.id === id && !v.at); i++) {
      await page.waitForTimeout(100);
      s = await g();
    }
    const z = s.zones.find((v) => v.id === id);
    if (!z) throw new Error(`на виде ${s.view} нет зоны ${id}; есть: ${s.zones.map((v) => v.id).join(", ")}`);
    if (!z.at) throw new Error(`зону ${s.view}.${id} перекрыли`);
    return z;
  }
  async function item(id) {
    const s = await g();
    const it = s.items.find((v) => v.id === id);
    if (!it) throw new Error(`предмета ${id} нет при себе`);
    return it;
  }

  async function doMove(mv) {
    const m = mv.move;
    let r;
    if (m === "совет") { const s = await g(); await clickAt(s.hud.hint); return; }
    if (m === "назад") { const s = await g(); await clickAt(s.hud.back); return; }
    if (m === "закрыть меню") { await page.waitForTimeout(400); await page.keyboard.press("Escape"); return; }
    if ((r = /^меню (\S+)\.(\S+)$/.exec(m))) {
      let s = await g();
      for (let i = 0; i < 40 && !s.choice; i++) { await page.waitForTimeout(100); s = await g(); }
      const it = s.menuItems && s.menuItems.find((x) => x.id === r[2]);
      if (!it) throw new Error(`в меню нет пункта ${r[2]}`);
      await page.waitForTimeout(500);
      await clickAt(it.at, "left", 500);
      return;
    }
    if ((r = /^осмотр (\S+)$/.exec(m))) { await clickAt((await item(r[1])).at, "right"); return; }
    if ((r = /^(\S+) \+ (\S+)$/.exec(m))) {
      await clickAt((await item(r[1])).at);
      await clickAt((await item(r[2])).at);
      return;
    }
    if ((r = /^(\S+)\.(\S+) ← (\S+)/.exec(m))) {
      await clickAt((await item(r[3])).at);
      await clickAt((await zone(r[2])).at);
      return;
    }
    if ((r = /^(\S+)\.(\S+) (\S+)$/.exec(m))) {
      const z = await zone(r[2]);
      const verb = r[3];
      if (verb === "осмотр") { await clickAt(z.at, "right"); return; }
      await clickAt(z.at);
      if (verb === "клик") return;
      let s = await g();
      if (!s.menuItems) {
        // у зоны одно действие без меню — движок выполнил его сразу
        return;
      }
      const it = s.menuItems.find((x) => x.verb === verb);
      if (!it) throw new Error(`у зоны ${r[2]} нет действия «${verb}»`);
      await page.waitForTimeout(450);
      await clickAt(it.at, "left", 300);
      return;
    }
    throw new Error(`непонятный ход «${m}»`);
  }

  async function runMove(mv, where) {
    const before = (await g()).log.length;
    await doMove(mv);
    const s = await settle();
    await page.waitForTimeout(250);
    const got = s.log.slice(before);
    report.shown.push(...got);
    const want = mv.slots || [];
    if ([...got].sort().join(",") !== [...want].sort().join(",")) {
      report.mismatches.push({ where, move: mv.move, want, got });
      console.log(`РАСХОЖДЕНИЕ ${where} «${mv.move}»: план ${want.join(",")} — игра ${got.join(",")}`);
    }
  }

  async function saveSnapshot() {
    return page.evaluate(() => {
      const o = {};
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k.startsWith("bj3.save")) o[k] = localStorage.getItem(k);
      }
      return o;
    });
  }
  // Выйти на титул: из игры — «Меню» → «Сохранить и выйти»; после концовки — «На титул».
  async function toTitle() {
    let s = await g();
    if (s && s.ended) await clickAt(s.hud.end, "left", 1500);
    else {
      await clickAt([1250 + 67, 12 + 26], "left", 500);   // HUD.menu
      await page.waitForTimeout(700);
      await clickAt([960, 330 + 4 * 84 + 35], "left", 500);   // pauseRects: quit — пятый пункт
    }
    await page.waitForFunction(() => window.__bj3.scene() === "title");
  }
  // На титуле положить сохранение (снимок, при нужде со снятыми флагами) и «Продолжить».
  async function continueFrom(snap, remove) {
    await page.evaluate(([snap, remove]) => {
      for (const k of Object.keys(localStorage)) if (k.startsWith("bj3.save")) localStorage.removeItem(k);
      for (const [k, v] of Object.entries(snap)) {
        if (remove && remove.length && v) {
          const o = JSON.parse(v);
          if (o && o.flags) o.flags = o.flags.filter((f) => !remove.includes(f));
          localStorage.setItem(k, JSON.stringify(o));
        } else localStorage.setItem(k, v);
      }
    }, [snap, remove || null]);
    await page.waitForTimeout(500);
    const tb = await page.evaluate(() => window.__bj3.buttons());
    const cont = tb.find((b) => b.id === "cont") || tb[1];
    await clickAt([cont.x + 200, cont.y + 36], "left", 600);
    await page.waitForFunction(() => window.__bj3.scene() === "game" && window.__bj3.game() && !window.__bj3.game().busy);
    await page.waitForTimeout(800);
    return g();
  }
  async function restoreSnapshot(snap) {
    await toTitle();
    return continueFrom(snap, null);
  }

  function startFile(name) {
    outFd = fs.openSync(path.join(OUT, name), "w");
  }
  async function stopFile() {
    await page.evaluate(() => window.__recStop());
    fs.closeSync(outFd);
    outFd = null;
  }

  // ---------------------------------------------------------------- старт
  await page.goto(URL);
  await page.waitForFunction(() => !document.getElementById("play").disabled, null, { timeout: 60000 });
  for (const n of [1, 2, 3, 4]) {
    const d = await (await page.request.get(new globalThis.URL(`data/act${n}.json`, URL).href)).json();
    for (const [k, v] of Object.entries(d.docs)) docs[k] = (v.lines || []).join(" ");
  }
  await page.click("#play");
  await page.waitForFunction(() => window.__bj3.scene() === "title" && window.__bj3.buttons().length === 4);
  let recording = false;
  for (const act of PLAN) {
    if (ONLY && !ONLY.has(act.act)) continue;
    console.log(`=== акт ${act.act}`);
    curAct = act.act;
    startFile(`act${act.act}.webm`);
    await page.evaluate(() => window.__recStart(30, 6000000));
    recording = true;
    if (act.act === PLAN[0].act) {
      await page.waitForTimeout(1500);
      const tb = await page.evaluate(() => window.__bj3.buttons());
      await clickAt([tb[0].x + 200, tb[0].y + 36], "left", 800);
      await page.waitForFunction(() => window.__bj3.scene() === "game" && window.__bj3.game());
    }
    let k = 0;
    for (const mv of act.moves) {
      k += 1;
      const where = `акт ${act.act}, ход ${k}`;
      try {
        if (mv.branch) {
          const snap = await saveSnapshot();
          await caption(mv.caption || "Другой порядок действий: то, чего нет на основном пути");
          await page.waitForTimeout(3000);
          if (mv.edit) {
            await toTitle();
            await continueFrom(snap, mv.edit.remove);
          }
          await caption(null);
          let j = 0;
          for (const bm of mv.branch) {
            j += 1;
            const lastCross = mv.cross && j === mv.branch.length;
            if (lastCross) {
              // ход кончает акт: следом — вступление следующего акта (у этого пути своё)
              const before = (await g()).log.length;
              await doMove(bm);
              let s2 = await settle();
              await page.waitForFunction((n) => { const x = window.__bj3.game(); return x && (x.act !== n || x.ended); }, act.act, { timeout: 120000 });
              s2 = await g();
              if (!s2.ended) {
                const keep = curAct;
                curAct = s2.act;
                s2 = await settle();
                curAct = keep;
              }
              report.shown.push(...s2.log.slice(before));
              continue;
            }
            await runMove(bm, `${where}, ответвление ${j}`);
          }
          await page.waitForTimeout(1500);
          await caption("Назад к сохранению — дальше по основному пути");
          await restoreSnapshot(snap);
          await page.waitForTimeout(1500);
          await caption(null);
          continue;
        }
        if (mv.move === "начало акта") {
          const s0 = (await g()) || { log: [] };
          const before = act.act === PLAN[0].act ? 0 : s0.log.length;
          const s = await settle();
          const got = s.log.slice(before);
          report.shown.push(...got);
          continue;
        }
        await runMove(mv, where);
      } catch (e) {
        report.errors.push(`${where} «${mv.move || "ответвление"}»: ${e.message}`);
        console.log(`ОШИБКА ${where}: ${e.message}`);
        await page.screenshot({ path: path.join(OUT, `error_${act.act}_${k}.png`) });
        throw e;
      }
    }
    // конец акта: дождаться следующего акта (или карточки «Конец»)
    await page.waitForTimeout(1500);
    if (act.act !== PLAN[PLAN.length - 1].act) {
      await stopFile();
      recording = false;
      await page.waitForFunction((n) => { const s = window.__bj3.game(); return s && s.act === n; }, act.act + 1, { timeout: 120000 });
    } else {
      await page.waitForTimeout(6000);
    }
  }
  if (recording) await stopFile();
  fs.writeFileSync(path.join(OUT, "record_log.json"), JSON.stringify(report, null, 1));
  console.log(`готово: расхождений ${report.mismatches.length}, ошибок ${report.errors.length}`);
  await browser.close();
})().catch((e) => {
  fs.writeFileSync(path.join(OUT, "record_log.json"), JSON.stringify(report, null, 1));
  console.error(e);
  process.exit(1);
});
