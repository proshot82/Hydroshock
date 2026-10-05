"""Тесты текстового слоя: слой собирается из итоговых файлов без потерь,
режется обратно на акты, а строки автора проверяются по списку."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "texts"))

import build_layer as bl  # noqa: E402
import check_texts as ct  # noqa: E402

T = ROOT / "texts"
PAIRS = [(T / "act1" / "ACT1_TEXTS_FINAL.md", T / "act1" / "BRIEF_ACT1_TEXTS.md"),
         (T / "act2" / "ACT2_TEXTS_FINAL.md", T / "act2" / "BRIEF_ACT2_TEXTS.md"),
         (T / "act3" / "ACT3_TEXTS_FINAL.md", T / "act3" / "BRIEF_ACT3_TEXTS.md")]


def parse(text):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "акт.md"
        p.write_text(text, encoding="utf-8")
        return ct.parse_texts(p)


def lines(slot):
    return [(l["speaker"], l["emotion"], l["funcs"], l["text"]) for l in slot["lines"]]


def doc(slot):
    return [l for l in (slot["doc"] or []) if l.strip()]


class LayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text, cls.acts = bl.build(PAIRS)
        cls.parts = bl.split_acts(cls.text)

    def test_committed_layer_is_generated(self):
        self.assertEqual((T / "TEXT_LAYER.md").read_text(encoding="utf-8"), self.text)

    def test_split_gives_three_acts(self):
        self.assertEqual(sorted(self.parts), ["I", "II", "III"])

    def test_round_trip_keeps_every_line(self):
        for (final, brief), roman in zip(PAIRS, ["I", "II", "III"]):
            src, _ = ct.parse_texts(final)
            got, fmt = parse(self.parts[roman])
            self.assertEqual(fmt, [])
            self.assertEqual(list(got), list(src))
            for sid in src:
                self.assertEqual(lines(got[sid]), lines(src[sid]), sid)
                self.assertEqual(doc(got[sid]), doc(src[sid]), sid)
            errs, _, _ = ct.check(ct.parse_brief(brief), got, fmt, ct.detect_act(brief))
            self.assertEqual(errs, [], roman)

    def test_context_and_locks_present(self):
        self.assertIn("> 🔒 Строка автора — перенести дословно: «Хороший Лапидус — чистый Лапидус.»", self.text)
        self.assertIn("> Обязательно (реплика iz): строка «Я держала стремянку.» отдельной репликой", self.text)
        self.assertIn("«Ваш комфорт — наша концепция.» / «Управляющий»", self.text)
        self.assertNotIn("§6.8 — две строки", self.text)

    def test_locks_catch_changed_author_line(self):
        part = self.parts["II"].replace("Я, в первую очередь, инженер.", "Я инженер.")
        texts, _ = parse(part)
        self.assertTrue(any("нет строки автора" in m for _, m in bl.check_locks("II", texts)))
        part = self.parts["I"].replace(" Не хватает корицы.", "")
        texts, _ = parse(part)
        self.assertEqual([s for s, _ in bl.check_locks("I", texts)], ["PROBE.coffee"])

    def test_split_survives_broken_answer(self):
        raw = ("Вот ответ.\n**# АКТ II «Старший по воде»**\n### OPEN.counter\nlap | lap_soap_neutral | PLOT | Раз.\n"
               "ПРОДОЛЖЕНИЕ СЛЕДУЕТ\n# АКТ II\n### OPEN.requests\nlap | lap_soap_neutral | PLOT | Два.\n"
               "КОНЕЦ АКТА II\nПослесловие.\n")
        parts = bl.split_acts(raw)
        self.assertEqual(list(parts), ["II"])
        self.assertNotIn("Вот ответ", parts["II"])
        self.assertNotIn("Послесловие", parts["II"])
        texts, _ = parse(parts["II"])
        self.assertEqual(list(texts), ["OPEN.counter", "OPEN.requests"])


if __name__ == "__main__":
    unittest.main()
