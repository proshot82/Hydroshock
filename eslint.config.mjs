// Линтер кода движка и браузерных тестов: только правила про ошибки (неизвестное имя, неиспользуемая
// переменная, недостижимый код, сравнение без типа…), без вкусовых. Запуск — из tools/check_all.py
// (группа static) или руками:  eslint game/js tools/web
// Нужен ESLint 9 или новее:  npm install -g eslint
const browser = ["window", "document", "navigator", "location", "history", "screen", "localStorage", "performance",
  "fetch", "Image", "console", "setTimeout", "clearTimeout", "setInterval", "requestAnimationFrame",
  "Element", "HTMLMediaElement"];
const node = ["require", "process", "__dirname", "module", "Buffer", "globalThis", "URL"];
const ro = (names) => Object.fromEntries(names.map((k) => [k, "readonly"]));
const rules = {
  "no-undef": "error",
  "no-unused-vars": ["error", { args: "none", caughtErrors: "none" }],
  "no-unreachable": "error",
  "no-dupe-keys": "error",
  "no-dupe-args": "error",
  "no-dupe-else-if": "error",
  "no-const-assign": "error",
  "no-redeclare": "error",
  "no-self-assign": "error",
  "no-fallthrough": "error",
  "no-cond-assign": "error",
  "no-unsafe-negation": "error",
  "no-unsafe-finally": "error",
  "no-useless-catch": "error",
  "no-loss-of-precision": "error",
  "no-shadow-restricted-names": "error",
  "no-constant-binary-expression": "error",
  "use-isnan": "error",
  "valid-typeof": "error",
  eqeqeq: ["error", "smart"],
};

export default [
  { files: ["game/js/**/*.js"], languageOptions: { ecmaVersion: 2022, sourceType: "module", globals: ro(browser) }, rules },
  // тесты на Playwright: код Node, а внутри page.evaluate — код страницы
  { files: ["tools/web/**/*.js"], languageOptions: { ecmaVersion: 2022, sourceType: "commonjs", globals: ro([...browser, ...node]) }, rules },
  { files: ["tools/web/**/*.mjs", "eslint.config.mjs"], languageOptions: { ecmaVersion: 2022, sourceType: "module", globals: ro([...browser, ...node]) }, rules },
];
