// Запись игры изнутри страницы (для видеопрохождения, tools/web/record_full.js): вставляется в
// страницу до загрузки игры (addInitScript). Звук: всё, что движок подаёт на выход Web Audio,
// заодно уходит в MediaStreamDestination. Картинка: отдельный холст 1920×1080, на нём каждый кадр —
// холст игры и курсор (курсор игры — CSS, в холст не попадает; рисуем его картинку по позиции мыши,
// горячая точка — из того же CSS). MediaRecorder пишет WebM кусками раз в секунду и отдаёт их в
// Node через window.__recChunk (exposeFunction).
(() => {
  const orig = AudioNode.prototype.connect;
  AudioNode.prototype.connect = function (target, ...rest) {
    const r = orig.call(this, target, ...rest);
    if (typeof AudioDestinationNode !== "undefined" && target instanceof AudioDestinationNode) {
      const ac = this.context;
      if (!ac.__recDest) ac.__recDest = ac.createMediaStreamDestination();
      orig.call(this, ac.__recDest);
      window.__recAudioCtx = ac;
    }
    return r;
  };
  let mx = -100;
  let my = -100;
  window.addEventListener("pointermove", (e) => { mx = e.clientX; my = e.clientY; }, true);
  window.addEventListener("pointerdown", (e) => { mx = e.clientX; my = e.clientY; }, true);
  const cursors = new Map();
  function cursorImage(css) {
    const m = /url\("?([^")]+)"?\)\s+(\d+)\s+(\d+)/.exec(css || "");
    if (!m) return null;
    let c = cursors.get(m[1]);
    if (!c) {
      const img = new Image();
      img.src = m[1];
      c = { img, hx: +m[2], hy: +m[3] };
      cursors.set(m[1], c);
    }
    return c;
  }
  let caption = null;
  window.__recCaption = (t) => { caption = t || null; };
  window.__recStart = (fps, vbps) => {
    const game = document.getElementById("game");
    const out = document.createElement("canvas");
    out.width = 1920;
    out.height = 1080;
    const o = out.getContext("2d", { alpha: false });
    let running = true;
    function frame() {
      if (!running) return;
      o.fillStyle = "#000";
      o.fillRect(0, 0, 1920, 1080);
      o.drawImage(game, 0, 0, 1920, 1080);
      const r = game.getBoundingClientRect();
      const sx = 1920 / r.width;
      const sy = 1080 / r.height;
      const cur = cursorImage(game.style.cursor || 'url("assets/gfx/cursors/cursor_normal.png") 14 6');
      if (cur && cur.img.complete && mx >= 0) {
        o.drawImage(cur.img, (mx - r.left) * sx - cur.hx, (my - r.top) * sy - cur.hy, 64, 64);
      }
      if (caption) {
        o.font = '600 34px "PT Sans", sans-serif';
        const w = o.measureText(caption).width + 60;
        o.fillStyle = "rgba(13, 15, 23, 0.9)";
        o.fillRect((1920 - w) / 2, 96, w, 64);
        o.strokeStyle = "#8cb3db";
        o.lineWidth = 3;
        o.strokeRect((1920 - w) / 2, 96, w, 64);
        o.fillStyle = "#d6e6f5";
        o.textAlign = "center";
        o.textBaseline = "middle";
        o.fillText(caption, 960, 129);
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    const stream = out.captureStream(fps);
    const ac = window.__recAudioCtx;
    if (ac && ac.__recDest) ac.__recDest.stream.getAudioTracks().forEach((t) => stream.addTrack(t));
    const mime = ["video/webm;codecs=vp8,opus", "video/webm"].find((m) => MediaRecorder.isTypeSupported(m));
    const rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: vbps, audioBitsPerSecond: 160000 });
    let pending = Promise.resolve();
    rec.ondataavailable = (e) => {
      if (!e.data || !e.data.size) return;
      pending = pending.then(async () => {
        const buf = new Uint8Array(await e.data.arrayBuffer());
        let s = "";
        for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
        await window.__recChunk(btoa(s));
      });
    };
    rec.start(1000);
    window.__recStop = () => new Promise((resolve) => {
      rec.onstop = () => { running = false; pending.then(resolve); };
      rec.stop();
    });
    return { mime, audio: !!(ac && ac.__recDest) };
  };
})();
