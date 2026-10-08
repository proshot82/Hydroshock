"""Негатив гейта шрифтов: детектор обязан видеть отсутствующий глиф.

Запуск: python -m unittest discover -s tests -v (нужен Pillow).
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

try:
    import check_fonts as cf
except ImportError:  # нет Pillow
    cf = None

FONTS = ROOT / "assets" / "fonts"


@unittest.skipIf(cf is None, "нет Pillow: pip install pillow")
class TestCheckFonts(unittest.TestCase):
    def test_canary_detected_everywhere(self):
        for font in sorted(FONTS.glob("*.ttf")):
            self.assertIn(cf.CANARY, cf.missing(str(font), [cf.CANARY]), font.name)

    def test_required_has_prereform_letters(self):
        for ch in "ѣъі":
            self.assertIn(ch, cf.REQUIRED)

    def test_cyrillic_present(self):
        for font in sorted(FONTS.glob("*.ttf")):
            self.assertEqual(cf.missing(str(font), "Каскадъ погруженіе"), set(), font.name)

    def test_yat_in_every_font(self):
        # ASSET_SPEC §8: ѣ/і рисуются всеми шрифтами сборки (H25).
        for font in sorted(FONTS.glob("*.ttf")):
            self.assertEqual(cf.missing(str(font), "ѣѢіІъЪ«»„“—–…№"), set(), font.name)

    def test_three_roles_present(self):
        # диалоги — PT Sans, печать 1908 — Old Standard TT, рукопись — Caveat
        names = {f.name for f in FONTS.glob("*.ttf")}
        for need in ("PTSans-Regular.ttf", "OldStandard-Regular.ttf", "Caveat.ttf"):
            self.assertIn(need, names)

    def test_detector_sees_missing_yat(self):
        # Негатив гейта на живом шрифте: в выведенной из сборки Neucha нет ѣ.
        neucha = ROOT / "work" / "orig_fonts" / "Neucha.ttf"
        self.assertIn("ѣ", cf.missing(str(neucha), "ѣ"))

    def test_gate_reads_final_texts(self):
        # пока design/texts.json нет, символы берутся из итоговых текстов
        import os
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            src = cf.texts_chars()
        finally:
            os.chdir(cwd)
        self.assertIn("ѣ", src)
        self.assertIn("TEXTS_FINAL", src["ѣ"])

    def test_gate_passes(self):
        import io
        import os
        from contextlib import redirect_stdout
        cwd = os.getcwd()
        os.chdir(ROOT)
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                cf.main()
        except SystemExit as e:
            self.fail("гейт шрифтов упал: " + buf.getvalue() + str(e))
        finally:
            os.chdir(cwd)
        self.assertIn("FONT GATE PASS", buf.getvalue())

if __name__ == "__main__":
    unittest.main()
