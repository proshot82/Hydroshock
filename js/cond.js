// Условия из файлов логики (дерево собирает tools/data/logic.py → act*.json).
// Тот же смысл, что у evaluate() в logic.py: проверка логики и движок считают одинаково.

export function evaluate(tree, st) {
  if (tree == null) return true;
  if (tree.f !== undefined) return st.flags.has(tree.f);
  if (tree.not !== undefined) return !evaluate(tree.not, st);
  if (tree.and) return tree.and.every((e) => evaluate(e, st));
  if (tree.or) return tree.or.some((e) => evaluate(e, st));
  if (tree.shown !== undefined) return (st.n[tree.shown] || 0) > 0;
  if (tree.pos !== undefined) return st.pos === tree.pos;
  if (tree.view !== undefined) return st.view === tree.view;
  if (tree.cmp !== undefined) {
    let v;
    if (tree.cmp.startsWith("n:")) v = st.n[tree.cmp.slice(2)] || 0;
    else if (tree.cmp === "act") v = st.act;
    else v = st.c[tree.cmp] || 0;
    const x = tree.v;
    switch (tree.op) {
      case ">=": return v >= x;
      case "<=": return v <= x;
      case "=": return v === x;
      case ">": return v > x;
      case "<": return v < x;
      default: break;
    }
  }
  throw new Error("неизвестный узел условия: " + JSON.stringify(tree));
}

// Первое правило с истинным условием.
export function first(rules, st) {
  if (!rules) return null;
  for (const r of rules) if (evaluate(r.when, st)) return r;
  return null;
}
