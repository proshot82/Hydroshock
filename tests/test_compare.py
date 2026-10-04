"""Тесты импорта чужой версии и сборки слепого сравнения.

Импорт обязан менять только разметку; сборка — давать одну и ту же
раскладку A/B при каждом запуске и выносить нарушения ТЗ из голосования.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "texts"))

import build_compare as bc  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
