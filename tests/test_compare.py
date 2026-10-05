"""Тесты импорта чужой версии и сборки слепого сравнения.

Импорт обязан менять только разметку; сборка — давать одну и ту же
раскладку A/B при каждом запуске и выносить нарушения ТЗ из голосования.
"""

import datetime
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "texts"))

import build_compare as bc  # noqa: E402
import build_read as br  # noqa: E402
import check_texts as ct  # noqa: E402
import import_texts as it  # noqa: E402

ACT = ROOT / "texts" / "act1"


class ImportTest(unittest.TestCase):
    def test_raw_converts_to_committed_file(self):
        raw = (ACT / "ACT1_TEXTS_OTHER_raw.md").read_text(encoding="utf-8")
        res = it.convert(raw, ct.parse_brief(ct.DEFAULT_BRIEF))
        self.assertEqual(it.skeleton(raw), it.skeleton(res))
        self.assertEqual(res, (ACT / "ACT1_TEXTS_OTHER.md").read_text(encoding="utf-8"))

    def test_escapes_bold_and_plaintext(self):
        raw = ("### **Z03.cup.look**\n\nlap | lap\\_soap\\_neutral | CLUE | Чашка\\! Где\\-то.  \n\n"
               "### **DOC.plate**\n\nPlaintext  \nСТРОКА 1  \nСТРОКА 2\n")
        res = it.convert(raw, ct.parse_brief(ct.DEFAULT_BRIEF))
        self.assertIn("### Z03.cup.look\n", res)
        self.assertIn("lap | lap_soap_neutral | CLUE | Чашка! Где-то.\n", res)
        self.assertIn("### DOC.plate\n```text\nСТРОКА 1\nСТРОКА 2\n```", res)

    def test_text_change_is_refused(self):
        self.assertNotEqual(it.skeleton("Чашка на блюдце."), it.skeleton("Чашка на блюдце!"))


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = (ct.DEFAULT_BRIEF, ACT / "ACT1_TEXTS_CLAUDE.md", ACT / "ACT1_TEXTS_OTHER.md")
        cls.data = bc.build(*cls.args)

    def test_layout_is_stable(self):
        self.assertEqual(bc.build(*self.args)["k"], self.data["k"])

    def test_all_slots_and_sections(self):
        self.assertEqual(len(self.data["slots"]), 154)
        self.assertTrue(all(s["sec"] for s in self.data["slots"]))

    def test_rule_breaks_leave_the_vote(self):
        auto = {s["id"]: [a["who"] for a in s["auto"]] for s in self.data["slots"] if s["auto"]}
        self.assertEqual(set(auto), {"SEQ.peek.3_lobby", "CHOICE.pass", "CHOICE.wait"})
        self.assertTrue(all(w == ["other"] for w in auto.values()))

    def test_blind_typography(self):
        self.assertEqual(bc.blind('Ещё "путёвка" - и всё...'), "Еще «путевка» — и все…")


class BuildAct2Test(unittest.TestCase):
    def test_act_and_title_from_brief(self):
        brief = ROOT / "texts" / "act2" / "BRIEF_ACT2_TEXTS.md"
        self.assertEqual(ct.detect_act(brief), 2)
        self.assertEqual(bc.act_title(brief), "Старший по воде")


class MergeTest(unittest.TestCase):
    """Итоговая версия — генерируемый файл: она обязана совпадать со сборкой
    из голосов и правок и проходить проверку по ТЗ."""

    import merge_texts as mt  # noqa: E402

    def build(self):
        blocks, report = self.mt.merge(ct.DEFAULT_BRIEF, ACT / "ACT1_TEXTS_CLAUDE.md",
                                       ACT / "ACT1_TEXTS_OTHER.md", ACT / "ACT1_VOTES.json",
                                       ACT / "ACT1_TEXTS_EDITS.md")
        return self.mt.HEADER + "\n" + "\n\n".join(blocks) + "\n\nКОНЕЦ АКТА I\n", report

    def test_final_is_generated(self):
        text, _ = self.build()
        self.assertEqual(text, (ACT / "ACT1_TEXTS_FINAL.md").read_text(encoding="utf-8"),
                         "ACT1_TEXTS_FINAL.md правили руками — правки вносятся в ACT1_TEXTS_EDITS.md")

    def test_final_passes_brief(self):
        brief = ct.parse_brief(ct.DEFAULT_BRIEF)
        texts, fmt = ct.parse_texts(ACT / "ACT1_TEXTS_FINAL.md")
        errs, _, stats = ct.check(brief, texts, fmt)
        self.assertEqual(errs, [])
        self.assertEqual(stats["slots"], 154)

    def test_sources(self):
        _, report = self.build()
        self.assertEqual(sorted(report["rule"]), ["CHOICE.pass", "CHOICE.wait", "SEQ.peek.3_lobby"])
        self.assertIn("OPEN.2_shower", report["edit"])
        self.assertEqual(sum(len(v) for v in report.values()), 154)


if __name__ == "__main__":
    unittest.main()


class ReadTest(unittest.TestCase):
    """Страница чтения: все слоты, тексты без изменений, не прошедший ТЗ файл не берётся."""

    @classmethod
    def setUpClass(cls):
        t = ROOT / "texts"
        cls.pairs = [(t / "act2" / "ACT2_TEXTS_FINAL.md", t / "act2" / "BRIEF_ACT2_TEXTS.md"),
                     (t / "act3" / "ACT3_TEXTS_FINAL.md", t / "act3" / "BRIEF_ACT3_TEXTS.md")]
        cls.data = br.build(cls.pairs, datetime.date(2026, 10, 5))

    def test_acts_slots_and_status(self):
        acts = self.data["acts"]
        self.assertEqual(self.data["built"], "05.10.2026")
        self.assertEqual([a["act"] for a in acts], ["II", "III"])
        self.assertEqual([len(a["slots"]) for a in acts], [164, 110])
        self.assertEqual([a["status"] for a in acts], ["заморожен автором", "ждёт чтения автора"])
        self.assertTrue(all(s["sec"] for a in acts for s in a["slots"]))

    def test_texts_verbatim(self):
        for (final, _), act in zip(self.pairs, self.data["acts"]):
            texts, _ = ct.parse_texts(final)
            for s in act["slots"]:
                src = texts[s["id"]]
                self.assertEqual([l["t"] for l in s["lines"]], [l["text"] for l in src["lines"]])
                if src["doc"] is not None:
                    self.assertEqual(s["doc"], src["doc"][:len(s["doc"])])
        note = next(s for s in self.data["acts"][1]["slots"] if s["id"] == "DOC.note")
        self.assertIn("Платить МНѢ водой??? Да я васъ всѣхъ въ канализацію смою!", note["doc"])

    def test_render_keeps_scripts_closed(self):
        html = br.render(self.data)
        self.assertNotIn("__DATA__", html)
        self.assertEqual(html.count("</script>"), 2)

    def test_broken_final_is_refused(self):
        final, brief = self.pairs[1]
        text = final.read_text(encoding="utf-8").replace("МНѢ водой", "мне водой")
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "ACT3_TEXTS_FINAL.md"
            bad.write_text(text, encoding="utf-8")
            with self.assertRaises(ValueError):
                br.build_act(bad, brief)
