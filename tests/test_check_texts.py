"""Тесты проверки текстов акта (tools/texts/check_texts.py).

Позитив: ТЗ разбирается, версия Claude проходит без ошибок.
Негатив: каждая порча эталонного файла ловится своей ошибкой.
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "texts"))

import check_texts as ct  # noqa: E402

BRIEF = ROOT / "texts" / "act1" / "BRIEF_ACT1_TEXTS.md"
CLAUDE = ROOT / "texts" / "act1" / "ACT1_TEXTS_CLAUDE.md"


def run_check(text):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "тексты акта.md"
        p.write_text(text, encoding="utf-8")
        brief = ct.parse_brief(BRIEF)
        texts, fmt = ct.parse_texts(p)
        return ct.check(brief, texts, fmt)


def messages(errs):
    return "\n".join("%s: %s" % (sid, msg) for sid, msg in errs)


class BriefTest(unittest.TestCase):
    def test_brief_parsed(self):
        b = ct.parse_brief(BRIEF)
        self.assertEqual(len(b), 154)
        self.assertEqual(b["Z03.stars.look"]["min"], 2)
        self.assertEqual(b["Z03.stars.look"]["max"], 2)
        self.assertEqual(b["DOC.menu"]["kind"], "doc")
        self.assertEqual(b["DOC.menu"]["doc_max"], 16)
        self.assertEqual(b["CHOICE.pass"]["kind"], "choice")
        self.assertEqual(b["Z03.stars.fold"]["speakers"], {"cap"})
        self.assertTrue(b["PROBE.coffee"]["star"])

    def test_range_parse(self):
        self.assertEqual(ct.parse_range("1–3")["max"], 3)
        self.assertEqual(ct.parse_range("метка + 2–5")["kind"], "choice")
        self.assertEqual(ct.parse_range("док ≤4")["doc_max"], 4)
        with self.assertRaises(ValueError):
            ct.parse_range("много")


class NormTest(unittest.TestCase):
    def test_quotes_and_dashes(self):
        self.assertEqual(ct.norm_typo('Он сказал "привет" - и ушёл...'),
                         "Он сказал «привет» — и ушёл…")
        self.assertEqual(ct.norm_typo("«Отель „Каскад“ — четыре звезды»"),
                         "«Отель „Каскад“ — четыре звезды»")

    def test_same_line_ignores_final_punct_and_yo(self):
        self.assertTrue(ct.same_line("Осторожно, горячее", "Осторожно, горячее!"))
        self.assertTrue(ct.same_line("Воды нет во всем здании.",
                                     "Воды нет во всём здании"))


class ClaudeVersionTest(unittest.TestCase):
    def test_claude_version_passes(self):
        errs, warns, stats = run_check(CLAUDE.read_text(encoding="utf-8"))
        self.assertEqual(errs, [], messages(errs))
        self.assertEqual(stats["slots"], 154)


class NegativeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = CLAUDE.read_text(encoding="utf-8")

    def spoil(self, old, new):
        self.assertIn(old, self.base)
        return self.base.replace(old, new, 1)

    def assertCaught(self, text, fragment):
        errs, _, _ = run_check(text)
        self.assertIn(fragment, messages(errs))

    def assertWarned(self, text, fragment):
        """Правила тона — предупреждение, не ошибка (решение автора 04.10.2026)."""
        errs, warns, _ = run_check(text)
        self.assertIn(fragment, messages(warns))
        self.assertNotIn(fragment, messages(errs))

    def test_missing_slot(self):
        text = self.spoil("### UI.inventory\nui | none | STATE | ПРИ СЕБЕ\n", "")
        self.assertCaught(text, "UI.inventory: слот отсутствует")

    def test_unknown_slot(self):
        text = self.base + "\n### W9.ghost.look\nlap | lap_soap_neutral | CLUE | Призрак.\n"
        self.assertCaught(text, "лишний слот")

    def test_owner_line_changed(self):
        text = self.spoil("это МИНУС четыре звезды.", "это минус четыре звезды.")
        self.assertCaught(text, "нет owner-canon реплики")

    def test_answering_machine_changed(self):
        text = self.spoil("ans | none | STATE,JOKE | Спасибо! Ваше мнение очень важно для нас, оставайтесь на линии.",
                          "ans | none | STATE,JOKE | Спасибо! Ваше мнение важно для нас.")
        self.assertCaught(text, "нет строки автоответчика")

    def test_joke_only_line(self):
        text = self.spoil("lap | lap_soap_neutral | CLUE,JOKE | Матрас без простыни.",
                          "lap | lap_soap_neutral | JOKE | Матрас без простыни.")
        self.assertCaught(text, "только с JOKE")

    def test_wrong_emotion(self):
        text = self.spoil("lap | lap_soap_neutral | CLUE,JOKE | Матрас без простыни.",
                          "lap | lap_happy | CLUE,JOKE | Матрас без простыни.")
        self.assertCaught(text, "не из реестра lap")

    def test_speaker_not_allowed(self):
        text = self.spoil("### W1.bed\nlap |", "### W1.bed\niz |")
        self.assertCaught(text, "не разрешён")

    def test_isolde_first_person(self):
        text = self.spoil("Это обслуживание.", "Я считаю, это обслуживание.")
        self.assertCaught(text, "нет «я»")

    def test_isolde_simultaneously(self):
        text = self.spoil("Воды нет во всём здании.", "Воды нет во всём здании одновременно.")
        self.assertCaught(text, "«одновременно»")

    def test_banned_tech_word(self):
        text = self.spoil("Труба пуста до самого низа.", "Стояк пуст до самого низа.")
        self.assertCaught(text, "«стояк»")

    def test_eto_ne_eto(self):
        text = self.spoil("Ни надеть, ни вытереться.", "Это не юбка, это дверца.")
        self.assertCaught(text, "«это не …, это …»")

    def test_kefir_outside(self):
        text = self.spoil("Ни одной бутылки без концепции.", "Кефира нет.")
        self.assertCaught(text, "«кефир» вне разрешённых слотов")

    def test_mat_limit_and_speaker(self):
        text = self.spoil("Не по адресу.", "Бля, не по адресу.")
        text = text.replace("Можно. Но зачем?", "Бля. Бля. Зачем?", 1)
        self.assertWarned(text, "мат: 3 случаев")
        text = self.spoil("guestf | none | CHAR | Не толкайтесь", "guestf | none | CHAR | Бля, не толкайтесь")
        self.assertWarned(text, "мат у guestf")

    def test_fourth_wall_is_an_error(self):
        text = self.spoil("Не по адресу.", "Не по адресу, дорогой игрок.")
        self.assertCaught(text, "четвёртая стена")

    def test_doc_too_long(self):
        text = self.spoil("1908 годъ\n", "1908 годъ\nлишняя строка\n")
        self.assertCaught(text, "документ длиннее 4 строк")

    def test_waiter_free_text(self):
        text = self.spoil("waiter | none | CLUE | Осторожно, горячее!",
                          "waiter | none | CLUE | Посторонитесь!")
        self.assertCaught(text, "официант говорит только")

    def test_silence_where_lines_required(self):
        text = self.spoil("### W1.hooks\nlap | lap_soap_neutral | CLUE,CHAR | Крючки для халата и полотенца. Крепёж надёжный. Висеть на нём нечему.",
                          "### W1.hooks\nsilence")
        self.assertCaught(text, "тишина недопустима")

    def test_hint_level_emotion(self):
        text = self.spoil("anc | anc_calm | CLUE | Тележка шире двери.",
                          "anc | anc_smug | CLUE | Тележка шире двери.")
        self.assertCaught(text, "ступень подсказки требует anc_calm")

    def test_line_too_long(self):
        long = "Очень " * 40
        text = self.spoil("Не по адресу.", long.strip())
        self.assertCaught(text, "предел для lap")

    def test_bad_format_line(self):
        text = self.spoil("### FB.generic.2\n", "### FB.generic.2\nпросто текст без разметки\n")
        self.assertCaught(text, "не по формату")


if __name__ == "__main__":
    unittest.main()


# --- Акт II -----------------------------------------------------------------

BRIEF2 = ROOT / "texts" / "act2" / "BRIEF_ACT2_TEXTS.md"
CLAUDE2 = ROOT / "texts" / "act2" / "ACT2_TEXTS_CLAUDE.md"


def run_check2(text):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "тексты акта 2.md"
        p.write_text(text, encoding="utf-8")
        brief = ct.parse_brief(BRIEF2)
        texts, fmt = ct.parse_texts(p)
        return ct.check(brief, texts, fmt, act=2)


class Act2Test(unittest.TestCase):
    def setUp(self):
        self.base = CLAUDE2.read_text(encoding="utf-8")

    def test_detect_act(self):
        self.assertEqual(ct.detect_act(BRIEF), 1)
        self.assertEqual(ct.detect_act(BRIEF2), 2)

    def test_claude_version_clean(self):
        errs, _, stats = run_check2(self.base)
        self.assertEqual(errs, [], messages(errs))
        self.assertEqual(stats["slots"], 164)  # редакция 2: слот Z12.point.look снят (решение автора 05.10.2026)

    def spoil(self, old, new):
        self.assertIn(old, self.base)
        errs, _, _ = run_check2(self.base.replace(old, new, 1))
        return messages(errs)

    def test_reading_outside_end(self):
        msg = self.spoil("Три эпохи, одна труба.", "Три эпохи, одна оплата.")
        self.assertIn("только в END.act2", msg)

    def test_end_needs_both_readings(self):
        msg = self.spoil("Подношение это или оплата", "Это или то")
        self.assertIn("два прочтения", msg)

    def test_owner_canon_ladder_banned(self):
        msg = self.spoil("Три эпохи, одна труба.", "Я держала стремянку.")
        self.assertIn("owner-canon Акта III", msg)

    def test_isolde_no_first_person(self):
        msg = self.spoil("iz | iz_formal | CHAR | Табличка не соответствовала дизайн-коду.",
                         "iz | iz_formal | CHAR | Мне табличка не нравилась.")
        self.assertIn("нет «я»", msg)

    def test_manager_signature(self):
        msg = self.spoil("за ненадобностью.\nВаш комфорт — наша концепция.",
                         "за ненадобностью.\nС уважением.")
        self.assertIn("подписи управляющего", msg)

    def test_fixed_plate(self):
        msg = self.spoil("Старший по воде — тов. К.\n```", "Старший по воде — тов. Ка.\n```")
        self.assertIn("Старший по воде — тов. К.", msg)

    def test_pa_three_services(self):
        msg = self.spoil("и «текстильная забота» приносят", "приносят")
        self.assertIn("текстильная забота", msg)

    def test_no_english(self):
        msg = self.spoil("Три эпохи, одна труба.", "Три эпохи, одна труба, wellness.")
        self.assertIn("английское слово", msg)

    def test_debt_banned(self):
        msg = self.spoil("Три эпохи, одна труба.", "Три эпохи, один долг.")
        self.assertIn("«долг»", msg)


class Act2FinalTest(unittest.TestCase):
    def test_final_passes_brief(self):
        brief = ct.parse_brief(BRIEF2)
        texts, fmt = ct.parse_texts(ROOT / "texts" / "act2" / "ACT2_TEXTS_FINAL.md")
        errs, _, stats = ct.check(brief, texts, fmt, act=2)
        self.assertEqual(errs, [], messages(errs))
        self.assertEqual(stats["slots"], 164)  # редакция 2: слот Z12.point.look снят (решение автора 05.10.2026)


BRIEF3 = ROOT / "texts" / "act3" / "BRIEF_ACT3_TEXTS.md"
CLAUDE3 = ROOT / "texts" / "act3" / "ACT3_TEXTS_CLAUDE.md"


def run_check3(text):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "тексты акта 3.md"
        p.write_text(text, encoding="utf-8")
        brief = ct.parse_brief(BRIEF3)
        texts, fmt = ct.parse_texts(p)
        return ct.check(brief, texts, fmt, act=3)


class Act3Test(unittest.TestCase):
    def setUp(self):
        self.base = CLAUDE3.read_text(encoding="utf-8")

    def test_detect_act(self):
        self.assertEqual(ct.detect_act(BRIEF3), 3)

    def test_claude_version_clean(self):
        errs, warns, stats = run_check3(self.base)
        self.assertEqual(errs, [], messages(errs))
        self.assertEqual(warns, [], messages(warns))
        self.assertEqual(stats["slots"], 110)

    def spoil(self, old, new):
        self.assertIn(old, self.base)
        errs, _, _ = run_check3(self.base.replace(old, new, 1))
        return messages(errs)

    def test_name_before_bill(self):
        msg = self.spoil("Вернулась. С почтой.", "Вернулась. С почтой от Кухтулху.")
        self.assertIn("только после счёта", msg)

    def test_name_allowed_after_bill(self):
        errs, _, _ = run_check3(self.base.replace(
            "Людей не впускают. Обоз — впускают.",
            "Людей Кухтулху не впускает. Обоз — впускает.", 1))
        self.assertEqual(errs, [], messages(errs))

    def test_isolde_first_person_before_confession(self):
        msg = self.spoil("iz | iz_formal | CHAR | Печать ставится на документы отеля.",
                         "iz | iz_formal | CHAR | Мою печать не дам.")
        self.assertIn("до признания", msg)

    def test_stepladder_required(self):
        msg = self.spoil("iz | iz_confess | CHAR,PLOT | Я держала стремянку.",
                         "iz | iz_confess | CHAR,PLOT | Стремянку держала.")
        self.assertIn("Я держала стремянку", msg)

    def test_stepladder_only_in_confession(self):
        msg = self.spoil("Груз доставлен. Груз молчит.", "Я держала стремянку.")
        self.assertIn("только в TALK.iz.confess", msg)

    def test_author_note_exact(self):
        msg = self.spoil("Платить МНѢ водой??? Да я васъ всѣхъ въ канализацію смою!",
                         "Платить мне водой? Да я вас всех смою!")
        self.assertIn("Платить МНѢ водой", msg)

    def test_bill_needs_payer_mp(self):
        msg = self.spoil("М.П. плательщика ________", "Плательщик ________")
        self.assertIn("м.п. плательщика", msg)

    def test_report_needs_name(self):
        msg = self.spoil("Старшему по воде Кухтулху. Это Изольда", "Старшему по воде. Это Изольда")
        self.assertIn("кухтулху", msg)

    def test_ride_needs_staff(self):
        msg = self.spoil("тот, по словам Изольды, обслуживающий персонал.",
                         "тот, по словам Изольды, груз.")
        self.assertIn("обслуживающим персоналом", msg)

    def test_pa_third_stage(self):
        msg = self.spoil("начинает третий этап плановых улучшений", "начинает плановые улучшения")
        self.assertIn("третий этап плановых улучшений", msg)

    def test_act4_owner_canon_banned(self):
        msg = self.spoil("Груз доставлен. Груз молчит.", "Меня не увольняли. Меня благоустроили.")
        self.assertIn("owner-canon Акта IV", msg)

    def test_tentacles_banned(self):
        msg = self.spoil("Груз доставлен. Груз молчит.", "Груз доставлен. Где-то щупальца.")
        self.assertIn("«щупальца»", msg)

    def test_water_stand_signature(self):
        msg = self.spoil("Комплимент от заведения\nВаш комфорт — наша концепция.",
                         "Комплимент от заведения\nС уважением.")
        self.assertIn("подписи управляющего", msg)

    def test_new_emotions_only_in_act3(self):
        text2 = CLAUDE2.read_text(encoding="utf-8").replace(
            "iz | iz_formal | CHAR | Табличка не соответствовала дизайн-коду.",
            "iz | iz_confess | CHAR | Табличка не соответствовала дизайн-коду.", 1)
        errs, _, _ = run_check2(text2)
        self.assertIn("не из реестра", messages(errs))


class Act3FinalTest(unittest.TestCase):
    def test_final_passes_brief(self):
        brief = ct.parse_brief(BRIEF3)
        texts, fmt = ct.parse_texts(ROOT / "texts" / "act3" / "ACT3_TEXTS_FINAL.md")
        errs, _, stats = ct.check(brief, texts, fmt, act=3)
        self.assertEqual(errs, [], messages(errs))
        self.assertEqual(stats["slots"], 110)

    def test_final_body_equals_claude(self):
        claude = CLAUDE3.read_text(encoding="utf-8")
        final = (ROOT / "texts" / "act3" / "ACT3_TEXTS_FINAL.md").read_text(encoding="utf-8")
        key = "### OPEN.door"
        self.assertEqual(final[final.index(key):], claude[claude.index(key):])
