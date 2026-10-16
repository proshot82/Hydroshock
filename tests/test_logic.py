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


class Act2LogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = G.build(2)

    def run_check(self, data):
        errors, _ = CL.check_data(data, seed=2, walks=300)
        return errors

    def test_clean(self):
        errors, stats = CL.check_data(copy.deepcopy(self.data), seed=2)
        self.assertEqual(errors, [])
        self.assertGreater(stats["состояний"], 1000)
        self.assertIn("INV.plunger.look", self.data["borrowed"])     # осмотр вантуза — из Акта I

    def test_cascade_needs_scope(self):
        # без области экранный флаг гаснет при любой смене вида: каскад включили на стойке (Z04),
        # а к витрине (Z05) он уже не горит — витрину не открыть (B08)
        d = copy.deepcopy(self.data)
        d["screen_scopes"] = {}
        errors = self.run_check(d)
        self.assertTrue(any("B08_open_vitrine ни разу не срабатывает" in e for e in errors), errors)

    def test_missing_duty_makes_dead_end(self):
        d = copy.deepcopy(self.data)
        d["menus"]["talk"] = [it for it in d["menus"]["talk"] if it["id"] != "duty"]   # ключа не получить
        errors = self.run_check(d)
        self.assertTrue(any("тупиков" in e for e in errors), errors)
        self.assertTrue(any("B14_present_model" in e for e in errors), errors)

    def test_view_condition(self):
        import logic as L
        t = L.parse_cond("(вид=W4 ∨ вид=Z10) ∧ ¬shown(FB.films.1)")
        st = {"flags": set(), "pos": None, "n": {}, "c": {}, "view": "Z10"}
        self.assertTrue(L.evaluate(t, st))
        st["view"] = "W2"
        self.assertFalse(L.evaluate(t, st))


class Act3LogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = G.build(3)

    def run_check(self, data):
        errors, _ = CL.check_data(data, seed=3, walks=200)
        return errors

    def test_clean(self):
        errors, stats = CL.check_data(copy.deepcopy(self.data), seed=3, walks=300)
        self.assertEqual(errors, [])
        self.assertGreater(stats["состояний"], 1000)
        self.assertIn("Z04.pump.use", self.data["borrowed"])     # витрина «если не сделано в Акте II»

    def test_board_thrown_needs_return(self):
        # доску «НАШЕ» выбросили в кучу, а достать её нельзя — трапа нет, тележка в кабину не въезжает
        d = copy.deepcopy(self.data)
        del d["rules"]["W4.design_board"]["достать_доску"]
        errors = self.run_check(d)
        self.assertTrue(any("тупиков" in e for e in errors), errors)

    def test_earlier_act_flag_in_condition(self):
        # условие может читать флаг Акта II (кольцо на пломбе), ставить его — нет
        lay = [l for l in self.data["views"]["Z05"]["layers"] if l["name"] == "st_z05_ring"]
        self.assertEqual(lay[0]["when"], {"f": "seal_is_mark"})


class Act4LogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = G.build(4)

    def test_clean(self):
        errors, stats = CL.check_data(copy.deepcopy(self.data), seed=4, walks=300)
        self.assertEqual(errors, [])

    def test_sent_alone_start_checked(self):
        # оплата уехала одна в Акте III (флаг приходит из прошлого акта): приёмка «принято ранее»
        # должна быть в переборе — иначе её реплики «нигде не звучат»
        errors, _ = CL.check_data(copy.deepcopy(self.data), seed=4, walks=50)
        self.assertFalse(any("SEQ.goods.prior" in e for e in errors), errors)

    def test_line_sound(self):
        import logic as L
        self.assertEqual(L.parse_effects("sfx_fin_cascade@2, звук:sfx_knock@3, sfx_stamp"),
                         [{"sfx": "sfx_fin_cascade", "line": 2}, {"sfx": "sfx_knock", "line": 3}, {"sfx": "sfx_stamp"}])


if __name__ == "__main__":
    unittest.main()
