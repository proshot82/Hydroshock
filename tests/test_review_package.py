"""Тесты пакета для ревью: облегчённый пакет не теряет главного, полный — кладёт всё,
все файлы из списка существуют."""

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "review"))

import build_package as bp  # noqa: E402


class PackageTest(unittest.TestCase):
    def build(self, *flags):
        d = tempfile.mkdtemp()
        out = Path(d) / "пакет ревью.zip"
        self.assertEqual(bp.main([str(out), *flags]), 0)
        with zipfile.ZipFile(out) as z:
            names = z.namelist()
            text = z.read("REVIEW_PACKAGE.md").decode("utf-8")
        self.assertEqual(out.with_suffix(".md").read_text(encoding="utf-8"), text)
        return names, text

    def test_all_listed_files_exist(self):
        self.assertEqual([r for _, r in bp.FILES if not (ROOT / r).is_file()], [])
        self.assertTrue(bp.FULL_ONLY <= {r for _, r in bp.FILES})

    def test_lite_keeps_core_and_drops_duplicates(self):
        names, text = self.build()
        self.assertEqual(names[0], "00_BRIEF_FULL_REVIEW.md")
        for must in ("TEXT_LAYER.md", "ACT4_SUBMISSION.md", "BJ3_CANON_V2_2.md", "ACT4_graph.json"):
            self.assertTrue(any(n.endswith(must) for n in names), must)
        for dropped in ("BRIEF_ACT1_TEXTS.md", "PROJECT_STATUS_HYDROUDAR.md"):
            self.assertFalse(any(n.endswith(dropped) for n in names), dropped)
        self.assertIn("облегчённый", text)
        self.assertNotIn("ACT4_graph.json =====", text)   # JSON — только в ZIP

    def test_full_has_everything(self):
        names, text = self.build("--full")
        self.assertEqual(len(names), len(bp.FILES) + 1)
        self.assertIn("пакет полный", text)
        self.assertGreater(len(text), len(self.build()[1]))


if __name__ == "__main__":
    unittest.main()
