"""Единая команда проверок (tools/check_all.py): провал и нехватка зависимости не выдаются за успех.

Негативы по культуре гейтов (DESIGN_BIBLE §16): гейт, зелёный на сломанном входе, — украшение.
"""
import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_all as A  # noqa: E402


def quiet(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = fn(*args)
    return out, buf.getvalue()


class CheckAllTest(unittest.TestCase):
    def setUp(self):
        A.LOGS.mkdir(parents=True, exist_ok=True)

    def test_every_script_exists(self):
        """Каждая проверка зовёт файл, который есть в репозитории (удалили инструмент — узнаем здесь)."""
        for s in A.steps():
            for part in s.cmd or []:
                if part.startswith("tools/") or part.startswith("texts/"):
                    self.assertTrue((ROOT / part).is_file(), f"{s.name}: нет файла {part}")

    def test_groups_cover_all_steps(self):
        names = [s.name for s in A.steps()]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(s.group in A.GROUPS for s in A.steps()))
        self.assertEqual({s.group for s in A.steps()}, set(A.GROUPS))

    def test_failing_command_is_fail(self):
        step = A.Step("selftest_fail", "static", "проверка, которая падает", [A.PY, "-c", "print('сломано'); raise SystemExit(3)"])
        ok, out = quiet(A.run_step, step, A.Web())
        self.assertFalse(ok)
        self.assertIn("FAIL", out)
        self.assertIn("сломано", out)

    def test_passing_command_is_ok(self):
        step = A.Step("selftest_ok", "static", "проверка, которая проходит", [A.PY, "-c", "print('ок')"])
        ok, out = quiet(A.run_step, step, A.Web())
        self.assertTrue(ok)
        self.assertIn("OK", out)

    def test_missing_library_is_named_not_failed_silently(self):
        """Урок 10.11.2026: без pyloudnorm матрица показывала ложный провал H21."""
        step = A.Step("selftest_dep", "static", "проверка с несуществующей библиотекой",
                      [A.PY, "-c", "print('не должна запускаться')"], py=("bj3_no_such_library",))
        ok, out = quiet(A.run_step, step, A.Web())
        self.assertFalse(ok)
        self.assertIn("НЕТ ЗАВИСИМОСТИ", out)
        self.assertIn("bj3_no_such_library", out)
        self.assertIn("requirements-dev.txt", out)
        self.assertNotIn("не должна запускаться", out)

    def test_missing_program_is_named(self):
        """Урок 11.11.2026: на GitHub без ffprobe проверка звука упала, будто звук сломан."""
        step = A.Step("selftest_tool", "static", "проверка с несуществующей программой",
                      [A.PY, "-c", "print('не должна запускаться')"], tools=("bj3-no-such-program",))
        ok, out = quiet(A.run_step, step, A.Web())
        self.assertFalse(ok)
        self.assertIn("НЕТ ЗАВИСИМОСТИ", out)
        self.assertIn("bj3-no-such-program", out)
        self.assertNotIn("не должна запускаться", out)

    def test_audio_checks_declare_ffmpeg(self):
        by = {s.name: s for s in A.steps()}
        for name in ("audio", "matrix"):
            self.assertTrue(set(A.FFMPEG) <= set(by[name].tools), name)

    def test_timeout_is_fail(self):
        step = A.Step("selftest_slow", "static", "проверка, которая зависла", [A.PY, "-c", "import time; time.sleep(30)"], timeout=1)
        ok, out = quiet(A.run_step, step, A.Web())
        self.assertFalse(ok)
        self.assertIn("не уложилась", out)

    def test_generated_drift_is_detected(self):
        """Ручная правка генерируемого документа ловится: сравнение идёт с выводом генератора."""
        target = ROOT / "texts" / "TEXT_LAYER.md"
        orig = target.read_bytes()
        try:
            target.write_bytes(orig + "\nправка руками\n".encode("utf-8"))
            log = io.StringIO()
            self.assertEqual(A.run_generated(log), 1)
            self.assertIn("TEXT_LAYER.md", log.getvalue())
        finally:
            target.write_bytes(orig)
        self.assertEqual(A.run_generated(io.StringIO()), 0)


if __name__ == "__main__":
    unittest.main()
