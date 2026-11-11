"""Достижимость реплик (tools/data/check_reach.py): слот, который игрок может услышать, не объявляется
немым, а недостижимый — объявляется.

Негативы по культуре гейтов (DESIGN_BIBLE §16): гейт, зелёный на сломанном входе, — украшение.
"""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "data"))
import check_reach as R  # noqa: E402
import gen_design as G  # noqa: E402


class Act4ReachTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = G.build(4)

    def test_variants_are_found_not_silent(self):
        r = R.analyze(4, copy.deepcopy(self.data))
        self.assertEqual(r["silent"], [])
        self.assertEqual(r["dead"], [])
        # вариант от выбора в Акте III: оплату отправили одну
        for slot in ("SEQ.rollout.empty", "SEQ.goods.prior"):
            self.assertIn("payment_sent_alone", r["found"][slot])
            self.assertIn("наследство Акта III", r["found"][slot])
        # пункт разговора после необязательного осмотра фотографии
        self.assertIn("family_photo_seen", r["found"]["TALK.kuh.photo"])

    def test_main_path_slot_is_played_directly(self):
        r = R.analyze(4, copy.deepcopy(self.data))
        self.assertIn("SEQ.goods", r["played"])
        self.assertNotIn("SEQ.goods", r["found"])

    def test_unreachable_menu_item_is_silent(self):
        data = copy.deepcopy(self.data)
        item = next(it for it in data["menus"]["kuh"] if it["id"] == "photo")
        item["rules"][0]["when"] = {"f": "flag_nobody_sets"}
        r = R.analyze(4, data)
        self.assertEqual(r["silent"], ["TALK.kuh.photo"])

    def test_flag_no_act_sets_is_not_inheritance(self):
        """Флаг, которого не ставит ни один акт, наследством не считается: вариант остаётся немым."""
        data = copy.deepcopy(self.data)
        for r_ in data["chains"]["rollout"]:
            t = r_["when"]
            if t and "payment_sent_alone" in str(t):
                r_["when"] = {"f": "flag_nobody_sets"}
        r = R.analyze(4, data)
        self.assertIn("SEQ.rollout.empty", r["silent"])

    def test_strict_exit_code(self):
        self.assertEqual(R.main(["4", "--strict"]), 0)


if __name__ == "__main__":
    unittest.main()
