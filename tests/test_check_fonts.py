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

    def test_yat_missing_in_neucha(self):
        # Известная дыра (статус проекта): ѣ нет в Neucha, есть в PT Sans.
        # Тест упадёт, когда шрифт заменят, — тогда его надо обновить.
        self.assertIn("ѣ", cf.missing(str(FONTS / "Neucha.ttf"), "ѣ"))
        self.assertEqual(cf.missing(str(FONTS / "PTSans-Regular.ttf"), "ѣ"), set())


if __name__ == "__main__":
    unittest.main()
