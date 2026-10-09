"""Проверка docs/BJ3_ASSET_SPEC.md: позитив на живой спеке и по негативу на каждое правило.

Запуск: python -m unittest discover -s tests -v
"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_asset_spec as cas  # noqa: E402

SPEC = (ROOT / "docs" / "BJ3_ASSET_SPEC.md").read_text(encoding="utf-8")


def run(text):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "spec.md"
        p.write_text(text, encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cas.main([str(p)])
    return code, buf.getvalue()


class TestAssetSpec(unittest.TestCase):
    def assertFails(self, text, needle):
        code, out = run(text)
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)

    def test_live_spec_clean(self):
        code, out = run(SPEC)
        self.assertEqual(code, 0, out)
        self.assertIn("кадров слотов 73", out)
        self.assertIn("документов 41", out)
        self.assertIn("эмоций 28", out)

    def test_duplicate_name(self):
        row = next(l for l in SPEC.splitlines() if l.startswith("| `ic_mug.png` |"))
        self.assertFails(SPEC.replace(row, row + "\n" + row), "определён дважды")

    def test_bad_name(self):
        self.assertFails(SPEC.replace("`ic_mug.png` | 128×128", "`Mug-Icon.png` | 128×128"),
                         "не подходит ни под один шаблон")

    def test_bad_size(self):
        self.assertFails(SPEC.replace("`ic_mug.png` | 128×128", "`ic_mug.png` | 256×256"), "размер 256×256")

    def test_unknown_flag(self):
        self.assertFails(SPEC.replace("| ¬`has_menu_card` |", "| ¬`has_menu_kard` |", 1), "флага `has_menu_kard` нет")

    def test_unknown_slot(self):
        self.assertFails(SPEC.replace("`shown(PROBE.juice)` |", "`shown(PROBE.juise)` |", 1), "слота `PROBE.juise` нет")

    def test_state_without_base(self):
        self.assertFails(SPEC.replace("`st_w3_cabinet_open.png`", "`st_w9_cabinet_open.png`"), "нет базы")

    def test_missing_frame_slot(self):
        lines = [l for l in SPEC.splitlines() if not l.startswith("| `SEQ.debt` |")]
        self.assertFails("\n".join(lines), "нет кадра для `SEQ.debt`")

    def test_frame_refers_undefined(self):
        self.assertFails(SPEC.replace("| `SEQ.peek.2_lift` | I | `fr_a1_lift_panel.png` |",
                                      "| `SEQ.peek.2_lift` | I | `fr_a1_lift_panel2.png` |"), "неопределённый `fr_a1_lift_panel2.png`")

    def test_missing_portrait(self):
        lines = [l for l in SPEC.splitlines() if not l.startswith("| `port_kuh_nostalgic.png`")]
        self.assertFails("\n".join(lines), "нет портрета `port_kuh_nostalgic.png`")

    def test_missing_foam_variant(self):
        lines = [l for l in SPEC.splitlines() if not l.startswith("| `port_lap_soap_panic_cap.png`")]
        self.assertFails("\n".join(lines), "нет варианта пены `port_lap_soap_panic_cap.png`")

    def test_missing_document(self):
        lines = [l for l in SPEC.splitlines() if not l.startswith("| `DOC.ledger` |")]
        self.assertFails("\n".join(lines), "нет строки для документа `DOC.ledger`")

    def test_missing_sound_slot(self):
        self.assertFails(SPEC.replace("| `Z09.paint.scrape` |\n", "| — |\n"), "нет звука для `Z09.paint.scrape`")

    def test_font_not_described(self):
        lines = [l for l in SPEC.splitlines() if not l.startswith("| `Caveat.ttf`")]
        self.assertFails("\n".join(lines), "`Caveat.ttf` лежит в assets/fonts")

    def test_totals_line(self):
        import re
        bad = re.sub(r"графика \d+", "графика 1", SPEC, count=1)
        self.assertFails(bad, "§0: в итоге графика 1")


if __name__ == "__main__":
    unittest.main()
