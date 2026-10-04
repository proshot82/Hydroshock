"""Тесты солвера графов A: позитив и по негативу на каждую проверку.

Запуск: python -m unittest discover -s tests -v
"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "solver"))

import solve_graph as sg  # noqa: E402

TOY = json.loads((ROOT / "tools" / "solver" / "examples" / "toy_act.json").read_text(encoding="utf-8"))


def run(data):
    report = sg.Report(act="test")
    graph = sg.parse_graph(copy.deepcopy(data), report)
    if graph is not None and not report.errors:
        sg.analyse(graph, report)
    return report, graph


def act(aid, requires, adds, removes=(), optional=False, room="W1", type_="use"):
    return {"id": aid, "name": aid, "room": room, "type": type_, "requires": list(requires),
            "adds": list(adds), "removes": list(removes), "optional": optional}


def joined(report):
    return "\n".join(report.errors)


class TestPositive(unittest.TestCase):
    def test_toy_accepted(self):
        report, _ = run(TOY)
        self.assertTrue(report.ok, joined(report))
        self.assertEqual(len(report.info["shortest_path"]), 5)
        self.assertEqual(report.info["free_pairs"], [("A01_take_cup", "A02_read_note")])
        self.assertEqual(report.info["removes_actions"], ["A04_water_plant"])
        self.assertEqual(report.info["removes_unsafe"], [])

    def test_cli_exit_codes(self):
        self.assertEqual(sg.main([str(ROOT / "tools/solver/examples/toy_act.json")]), 0)
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{не json", encoding="utf-8")
            self.assertEqual(sg.main([str(bad)]), 2)
            broken = copy.deepcopy(TOY)
            broken["act_goal_flags"] = ["nonexistent"]
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(sg.main([str(path)]), 1)

    def test_cyrillic_path_with_spaces(self):
        # Грабли BJ2: кириллица и пробелы в пути.
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "Янычар папка" / "акт I"
            folder.mkdir(parents=True)
            path = folder / "граф акта.json"
            path.write_text(json.dumps(TOY, ensure_ascii=False), encoding="utf-8")
            out = folder / "отчёт.json"
            self.assertEqual(sg.main([str(path), "--json", str(out)]), 0)
            self.assertTrue(json.loads(out.read_text(encoding="utf-8"))["ok"])


class TestSchemaNegatives(unittest.TestCase):
    def test_missing_key(self):
        data = copy.deepcopy(TOY)
        del data["flags_glossary"]
        report, graph = run(data)
        self.assertIsNone(graph)
        self.assertIn("flags_glossary", joined(report))

    def test_unknown_flag(self):
        data = copy.deepcopy(TOY)
        data["actions"][0]["adds"].append("ghost_flag")
        report, _ = run(data)
        self.assertIn("ghost_flag нет в глоссарии", joined(report))

    def test_duplicate_id(self):
        data = copy.deepcopy(TOY)
        data["actions"].append(copy.deepcopy(data["actions"][0]))
        report, _ = run(data)
        self.assertIn("id повторяется", joined(report))

    def test_bad_type(self):
        data = copy.deepcopy(TOY)
        data["actions"][0]["type"] = "classify"
        report, _ = run(data)
        self.assertIn("«classify»", joined(report))

    def test_unknown_room(self):
        data = copy.deepcopy(TOY)
        data["actions"][0]["room"] = "W9"
        report, _ = run(data)
        self.assertIn("W9", joined(report))

    def test_noop_action(self):
        data = copy.deepcopy(TOY)
        data["actions"].append(act("A99_noop", ["at_start"], []))
        report, _ = run(data)
        self.assertIn("не меняет ни одного флага", joined(report))

    def test_goal_already_true(self):
        data = copy.deepcopy(TOY)
        data["start_flags"].append("door_open")
        report, _ = run(data)
        self.assertIn("истинна уже на старте", joined(report))

    def test_unused_glossary_flag_warns(self):
        data = copy.deepcopy(TOY)
        data["flags_glossary"]["orphan"] = "никому не нужен"
        report, _ = run(data)
        self.assertTrue(report.ok)
        self.assertTrue(any("orphan" in w for w in report.warnings))


class TestAnalysisNegatives(unittest.TestCase):
    def test_goal_unreachable(self):
        data = copy.deepcopy(TOY)
        data["actions"][4]["requires"].append("has_water_twice")
        data["flags_glossary"]["has_water_twice"] = "никогда не бывает"
        report, _ = run(data)
        self.assertIn("недостижима из start_flags", joined(report))

    def test_softlock_via_removes(self):
        # Записку можно сжечь — и знание о кране пропадает навсегда.
        data = copy.deepcopy(TOY)
        # Записка читается один раз (лежит на столе, пока не прочитана).
        data["flags_glossary"]["note_on_table"] = "записка на столе"
        data["start_flags"].append("note_on_table")
        data["actions"][1]["requires"] = ["note_on_table"]
        data["actions"][1]["removes"] = ["note_on_table"]
        data["actions"].append(act("A06_burn_note", ["has_note"], ["note_burned"],
                                   removes=["has_note", "knows_tap"], optional=True))
        data["flags_glossary"]["note_burned"] = "записка сожжена"
        report, _ = run(data)
        text = joined(report)
        self.assertIn("СОФТЛОК", text)
        self.assertIn("removes действия A06_burn_note", text)
        self.assertEqual(report.info["removes_unsafe"], ["A06_burn_note"])

    def test_softlock_without_removes(self):
        # Тупик без removes: ветка, где нужное действие запрещено флагом-ловушкой,
        # моделируется как недостижимость; здесь — альтернативный финал без выхода.
        data = copy.deepcopy(TOY)
        data["actions"].append(act("A06_wrong_way", ["at_start"], ["trapped"], removes=["at_start"]))
        data["flags_glossary"]["trapped"] = "герой в чулане"
        report, _ = run(data)
        self.assertIn("СОФТЛОК", joined(report))

    def test_optional_actually_required(self):
        data = copy.deepcopy(TOY)
        data["actions"][1]["optional"] = True
        report, _ = run(data)
        text = joined(report)
        self.assertIn("без optional-действий цель недостижима", text)
        self.assertIn("A02_read_note помечено optional", text)

    def test_dead_action_warns(self):
        data = copy.deepcopy(TOY)
        data["flags_glossary"]["never"] = "никогда"
        data["flags_glossary"]["bonus"] = "бонус"
        data["actions"].append(act("A07_dead", ["never"], ["bonus"], optional=True))
        report, _ = run(data)
        self.assertTrue(report.ok, joined(report))
        self.assertIn("A07_dead", report.info["never_enabled"])

    def test_state_cap_is_error(self):
        report = sg.Report(act="test")
        graph = sg.parse_graph(copy.deepcopy(TOY), report)
        sg.analyse(graph, report, max_states=3)
        self.assertIn("анализ неполон", joined(report))


class TestChain(unittest.TestCase):
    def _next_act(self, start):
        return {
            "act": "TOY2", "start_flags": start,
            "flags_glossary": {"door_open": "дверь открыта", "has_cup": "чашка",
                               "has_water": "вода", "out": "вышел"},
            "actions": [act("B01_exit", ["door_open"], ["out"])],
            "rooms": ["W1 — коридор"], "act_goal_flags": ["out"],
        }

    def _chain(self, start):
        prev, _ = run(TOY)
        report, graph = run(self._next_act(start))
        sg.check_chain(prev, graph, report)
        return report

    def test_chain_ok(self):
        report = self._chain(["door_open", "has_cup"])
        self.assertTrue(report.ok, joined(report))

    def test_chain_flag_not_guaranteed(self):
        # has_water в финале TOY бывает (если долить после полива), но не гарантирован.
        report = self._chain(["door_open", "has_water"])
        self.assertIn("has_water", joined(report))


if __name__ == "__main__":
    unittest.main()
