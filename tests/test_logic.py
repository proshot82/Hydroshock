"""Проверка логики актов (tools/data/check_logic.py): чистые данные проходят, испорченные — падают.

Негативы по культуре гейтов (DESIGN_BIBLE §16): гейт, зелёный на сломанном входе, — украшение.
"""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "data"))
import check_logic as CL  # noqa: E402
import gen_design as G  # noqa: E402


class Act1LogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = G.build(1)

    def run_check(self, data):
        errors, _ = CL.check_data(data, seed=1, walks=400)
        return errors

    def test_clean(self):
        errors, stats = CL.check_data(copy.deepcopy(self.data), seed=1)
        self.assertEqual(errors, [])
        self.assertGreater(stats["состояний"], 1000)

    def test_missing_rule_makes_dead_end(self):
        d = copy.deepcopy(self.data)
        del d["rules"]["Z02.phone"]["позвонить"]          # звонок на стойку (A03) пропал
        errors = self.run_check(d)
        self.assertTrue(any("тупиков" in e for e in errors), errors)
        self.assertTrue(any("A03_call_reception" in e for e in errors), errors)

    def test_weak_condition_breaks_requires(self):
        d = copy.deepcopy(self.data)
        for z in d["views"]["Z01"]["zones"]:
            if z["id"] == "plunger":
                z["when"] = None                            # зона вантуза видна и после снятия
        for r in d["rules"]["Z01.plunger"]["предмет:menu"]:
            r["when"] = None                                # снять вантуз «всегда», даже снятый
        errors = self.run_check(d)
        self.assertTrue(any("N01_free_plunger срабатывает без" in e for e in errors), errors)

    def test_lost_effect_breaks_graph(self):
        d = copy.deepcopy(self.data)
        for r in d["rules"]["Z03.stars"]["сложить"]:
            r["effects"] = [e for e in r["effects"] if e.get("add") != "stars_folded"]
        errors = self.run_check(d)
        self.assertTrue(any("A06_fold_stars: правила не ставят" in e for e in errors), errors)

    def test_silent_slot_found(self):
        d = copy.deepcopy(self.data)
        d["rules"]["W1.bed"]["осмотр"][0]["slot"] = "W1.hooks"   # кровать говорит чужой репликой
        errors = self.run_check(d)
        self.assertTrue(any("нигде не звучат" in e and "W1.bed" in e for e in errors), errors)

    def test_bad_reference_rejected(self):
        import logic as L
        with self.assertRaises(ValueError):
            L.parse_cond("plunger_on_panel ∧ ∧ has_menu_card")
        with self.assertRaises(ValueError):
            L.parse_effects("+флаг_по_русски")


if __name__ == "__main__":
    unittest.main()
