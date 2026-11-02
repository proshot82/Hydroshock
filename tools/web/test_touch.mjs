// Юнит-тест распознавателя касаний game/js/touch.js — перенос tools/test_touch.lua (BJ2 р.25).
// Края, до которых автопрохождение не дотянется: дрожь пальца, потерянное отпускание,
// отпускание далеко без событий сдвига, кольцо удержания. Время идёт кадрами по 1/60 с.
//
//   node tools/web/test_touch.mjs        → TOUCH TEST PASS, код 0
import * as touch from "../../game/js/touch.js";

const log = [];
let n = 0;
let fails = 0;
touch.init((x, y, b) => log.push({ x, y, b }));

const reset = () => { log.length = 0; touch.cancel(); };
function check(ok, name) {
  n++;
  if (!ok) fails++;
  console.log(`${ok ? "[OK  ]" : "[FAIL]"} ${name}`);
}
function run(sec) {
  let t = 0;
  while (t < sec - 1e-9) {
    const d = Math.min(1 / 60, sec - t);
    touch.update(d);
    t += d;
  }
}
const only = (b, x, y) => log.length === 1 && log[0].b === b && (x === undefined || (log[0].x === x && log[0].y === y));

// 1. короткое касание: левый щелчок на отпускании, в точке касания
reset(); touch.pressed(100, 200); run(0.1);
check(log.length === 0, "касание: пока палец на экране — щелчков нет");
touch.released(103, 202);
check(only(0, 100, 200), "касание → один левый щелчок в точке касания");

// 2. медленное касание (короче порога) — всё ещё левый
reset(); touch.pressed(10, 10); run(0.3); touch.released(10, 10);
check(only(0), "медленное касание 0,3 с → левый щелчок");

// 3. удержание: правый по порогу, пока палец лежит; отпускание ничего не добавляет
reset(); touch.pressed(50, 60); run(touch.HOLD - 0.03);
check(log.length === 0, "до порога удержания — тишина");
run(0.05);
check(only(2, 50, 60), "удержание → правый щелчок сразу по порогу, палец ещё на экране");
run(1.0);
check(log.length === 1, "держать дольше — второго правого нет");
touch.released(50, 60);
check(log.length === 1, "отпускание после удержания — без лишнего левого");

// 4. палец уехал дальше SLOP — жест отменён целиком
reset(); touch.pressed(0, 0); touch.moved(touch.SLOP + 5, 0); run(1.0); touch.released(touch.SLOP + 5, 0);
check(log.length === 0, "сдвиг дальше SLOP → ни левого, ни правого");

// 5. дрожь в пределах SLOP не мешает ни касанию, ни удержанию
reset(); touch.pressed(0, 0); touch.moved(touch.SLOP - 3, 0); touch.released(touch.SLOP - 3, 0);
check(only(0, 0, 0), "дрожь пальца → касание");
reset(); touch.pressed(0, 0); touch.moved(0, touch.SLOP - 3); run(touch.HOLD + 0.05);
check(only(2, 0, 0), "дрожь пальца → удержание");
touch.released(0, 0);

// 6. уехал и вернулся — всё равно отмена
reset(); touch.pressed(0, 0); touch.moved(60, 0); touch.moved(0, 0); touch.released(0, 0);
check(log.length === 0, "уехал и вернулся → отмена");

// 7. отпускание далеко, а событий сдвига не было
reset(); touch.pressed(0, 0); touch.released(200, 0);
check(log.length === 0, "отпускание далеко без сдвигов → отмена");

// 8. отпускание и сдвиг без касания
reset(); touch.released(5, 5); touch.moved(9, 9); run(1.0);
check(log.length === 0, "отпускание/сдвиг без касания → тишина");

// 9. новое касание вместо потерянного отпускания
reset(); touch.pressed(1, 1); run(0.1); touch.pressed(300, 300); touch.released(300, 300);
check(only(0, 300, 300), "новое касание вместо потерянного → левый по новому");

// 10. отмена (второй палец, системный жест) — без щелчков и без кольца
reset(); touch.pressed(1, 1); run(0.3); touch.cancel(); run(1.0); touch.released(1, 1);
check(log.length === 0 && touch.ring() === null, "отмена жеста → тишина");

// 11. кольцо удержания
reset(); touch.pressed(5, 7);
check(touch.ring() === null, "кольцо не появляется сразу");
run(touch.RING_DELAY + 0.05);
let r = touch.ring();
check(r && r.x === 5 && r.y === 7 && r.p > 0 && r.p < 1, "кольцо растёт вокруг точки касания");
run(touch.HOLD);
r = touch.ring();
check(r && r.p === 1, "после удержания кольцо замкнуто, пока палец на экране");
touch.released(5, 7);
check(touch.ring() === null, "после отпускания кольца нет");
reset(); touch.pressed(0, 0); run(touch.RING_DELAY + 0.05); touch.moved(80, 0);
check(touch.ring() === null, "жест отменён сдвигом — кольца нет");
touch.released(80, 0);

// 12. пороги в «человеческом» коридоре
check(touch.HOLD >= 0.35 && touch.HOLD <= 0.6, "порог удержания ~0,45 с");
check(touch.SLOP >= 8 && touch.SLOP <= 32, "допуск сдвига 8..32 точек");
check(touch.RING_DELAY < touch.HOLD, "кольцо успевает показаться до удержания");

if (fails) {
  console.log(`TOUCH TEST FAIL (${fails} из ${n})`);
  process.exit(1);
}
console.log(`TOUCH TEST PASS (${n} проверок)`);
