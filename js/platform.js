// Где запущена игра и что умеет это место: компьютер, телефон в браузере, Telegram Mini App.
// Опыт BJ2 (web/index.html, р.25–27; docs/LESSONS.md №8) — перенесён под свой движок.
//
// Telegram. Параметры запуска Telegram кладёт в адрес после «#» (tgWebAppData, tgWebAppVersion,
// tgWebAppPlatform) — по ним и узнаём, что открыты внутри Telegram. Только тогда грузится его SDK:
// остальным игрокам незачем ходить на telegram.org. Внутри Telegram: весь экран (Bot API 8.0+),
// свайп вниз не сворачивает игру (7.7+), рамка чёрная, ориентация фиксируется, как только экран
// горизонтальный (lockOrientation держит ТЕКУЩУЮ ориентацию — вертикальный телефон закрывает кадр
// «лёжа»); «Назад» Telegram (и системный «назад» Android) — как Esc в игре; закрыть игру — с
// вопросом; сохранение дублируется в облако Telegram (cloud.js) — партия продолжается и с
// другого телефона или компьютера. Отступы под вырез и кнопки Telegram — CSS-переменные
// --tg-safe-area-inset-* и --tg-content-safe-area-inset-* (их ставит SDK), см. game.css.
//
// Браузер телефона. «Играть» открывает весь экран и просит альбомную ориентацию (Android Chrome);
// iPhone не умеет ни того, ни другого — там «ВО ВЕСЬ ЭКРАН» объясняет, как добавить игру на экран
// «Домой» (оттуда она открывается без строки браузера, manifest.webmanifest). «Назад» браузера
// (жест Android) — как Esc в игре, пока в игре есть куда возвращаться.

const mm = (q) => !!(window.matchMedia && window.matchMedia(q).matches);

export const TOUCH = mm("(hover: none) and (pointer: coarse)");
export const IOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
  (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
export const STANDALONE = mm("(display-mode: standalone)") || mm("(display-mode: fullscreen)") ||
  navigator.standalone === true;
const TG_LAUNCH = /(^|[#&?])tgWebApp(Data|Platform|Version)=/.test(String(location.hash || ""));
const TG_SDK = "https://telegram.org/js/telegram-web-app.js?59";

let tg = null;

export function telegram() {
  return tg;
}

export function tgAt(v) {
  try { return !!tg && tg.isVersionAtLeast(v); } catch (e) { return false; }
}

function tgCall(fn) {
  try { fn(); } catch (e) { /* старый клиент Telegram — без этой возможности */ }
}

function tgFullscreen() {
  if (tgAt("8.0") && !tg.isFullscreen) tgCall(() => tg.requestFullscreen());
}

// Фиксация горизонтали: только когда экран уже горизонтальный (держит текущую). Размер окна в
// событии resize на iOS неверен (WebKit 170595) — поэтому опрос, а не событие.
function tgLock() {
  if (!tgAt("8.0") || tg.isOrientationLocked) return;
  if (window.innerWidth > window.innerHeight) tgCall(() => tg.lockOrientation());
}

function tgInit() {
  tg = (window.Telegram && window.Telegram.WebApp) || null;
  if (!tg) return;
  tgCall(() => { tg.ready(); tg.expand(); });
  if (tgAt("6.1")) tgCall(() => { tg.setHeaderColor("#000000"); tg.setBackgroundColor("#000000"); });
  if (tgAt("7.10")) tgCall(() => tg.setBottomBarColor("#000000"));
  if (tgAt("7.7")) tgCall(() => tg.disableVerticalSwipes());
  if (tgAt("6.1")) tgCall(() => tg.BackButton.onClick(() => { if (backFn) backFn(); }));
  tgFullscreen();
  tgLock();
  setInterval(tgLock, 300);
  document.documentElement.classList.add("tg");
}

// SDK Telegram — только при запуске из Telegram; не загрузился за 5 с — играем без него.
export function init() {
  if (!TG_LAUNCH) return Promise.resolve(null);
  return new Promise((resolve) => {
    const s = document.createElement("script");
    const done = () => { resolve(tg); };
    const timer = setTimeout(done, 5000);
    s.src = TG_SDK;
    s.onload = () => { clearTimeout(timer); tgInit(); done(); };
    s.onerror = () => { clearTimeout(timer); console.warn("SDK Telegram не загрузился — играем без него"); done(); };
    document.head.appendChild(s);
  });
}

// ---------------------------------------------------------------- весь экран

function browserFsApi() {
  const d = document.documentElement;
  return !!(d.requestFullscreen || d.webkitRequestFullscreen);
}

export function fsAvailable() {
  if (tg) return tgAt("8.0");
  return browserFsApi();
}

export function fsActive() {
  if (tg) return !!tg.isFullscreen;
  return !!(document.fullscreenElement || document.webkitFullscreenElement) || STANDALONE;
}

// iPhone в Safari: весь экран — только с экрана «Домой».
export function homeScreenTip() {
  return IOS && !tg && !STANDALONE && !browserFsApi();
}

function lockLandscape() {
  try {
    const o = screen.orientation;
    if (o && o.lock) { const q = o.lock("landscape"); if (q && q.catch) q.catch(() => {}); }
  } catch (e) { /* браузер не умеет — держит кадр «лёжа» */ }
}

function browserFullscreen(landscape) {
  const d = document.documentElement;
  const rq = d.requestFullscreen || d.webkitRequestFullscreen;
  if (!rq) return;
  try {
    const p = rq.call(d);
    if (p && p.then) p.then(landscape ? lockLandscape : null, () => {});
    else if (landscape) lockLandscape();
  } catch (e) { /* без полного экрана */ }
}

export function fsToggle() {
  if (tg) {
    if (!tgAt("8.0")) return;
    tgCall(() => (tg.isFullscreen ? tg.exitFullscreen() : tg.requestFullscreen()));
    return;
  }
  if (document.fullscreenElement || document.webkitFullscreenElement) {
    (document.exitFullscreen || document.webkitExitFullscreen).call(document);
  } else browserFullscreen(TOUCH);
}

// «Играть»: в Telegram — его весь экран, на телефоне — весь экран и альбом; на компьютере — как было.
export function onPlay() {
  if (tg) tgFullscreen();
  else if (TOUCH && !STANDALONE) browserFullscreen(true);
  playing = true;
  keepAwake();
}

// ---------------------------------------------------------------- «назад»

let backFn = null;       // () => true, если игра что-то закрыла или вернулась
let canBack = false;
let pushed = false;
let skipPop = 0;

// Игра сообщает в каждом кадре, есть ли куда возвращаться, и чем возвращаться.
export function setBack(can, fn) {
  backFn = fn;
  can = !!can;
  if (can === canBack) return;
  canBack = can;
  if (tg) {
    if (tgAt("6.1")) tgCall(() => (can ? tg.BackButton.show() : tg.BackButton.hide()));
    return;
  }
  if (can && !pushed) {
    history.pushState({ bj3: 1 }, "");
    pushed = true;
  } else if (!can && pushed) {
    pushed = false;
    skipPop++;
    history.back();
  }
}

window.addEventListener("popstate", () => {
  if (skipPop) { skipPop--; return; }
  if (!pushed) return;
  pushed = false;
  canBack = false;   // в следующем кадре игра скажет снова — и запись вернётся, если ещё есть куда
  if (backFn) backFn();
});

// В партии закрыть Telegram — с вопросом (сохранение уже записано, но свайп бывает случайным).
let inGame = false;
export function setInGame(v) {
  if (v === inGame) return;
  inGame = v;
  if (tg && tgAt("6.2")) tgCall(() => (v ? tg.enableClosingConfirmation() : tg.disableClosingConfirmation()));
}

// Отдача удержания пальцем (долгое касание сработало).
export function haptic() {
  if (tg && tgAt("6.1")) tgCall(() => tg.HapticFeedback.impactOccurred("light"));
}

// ---------------------------------------------------------------- экран не гаснет

let wake = null;
function keepAwake() {
  if (!navigator.wakeLock || wake) return;
  navigator.wakeLock.request("screen").then((w) => {
    wake = w;
    w.addEventListener("release", () => { wake = null; });
  }).catch(() => {});
}
let playing = false;
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && playing) keepAwake();
});
