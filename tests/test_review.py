import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from content_planner.agent import Agent, validate_request, write_result
from content_planner.audit import verify_export
from content_planner.models import CodexModel, MockModel
from content_planner.store import Store
from content_planner.tools import ROOT


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "state.sqlite3"
        self.store = Store(self.db)
        self.request = json.loads((ROOT / "examples/inputs/normal.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_transient_retries_reset_per_invocation_not_forever_blocked(self):
        first = Agent(self.store, MockModel()).run(self.request, faults={"save_plan": 2})
        self.assertEqual(first["status"], "incomplete")
        second = Agent(self.store, MockModel()).run(self.request)
        self.assertEqual(second["status"], "completed")
        self.assertEqual([t["tool"] for t in second["trace"]], ["save_plan"])

    def test_actual_sqlite_insert_failure_is_not_claimed_success(self):
        self.store.db.execute("CREATE TRIGGER reject_plan BEFORE INSERT ON plans BEGIN SELECT RAISE(ABORT, 'test insert failure'); END")
        self.store.db.commit()
        first = Agent(self.store, MockModel()).run(self.request)
        self.assertEqual(first["status"], "incomplete")
        self.assertIsNone(self.store.plan(self.request["request_id"]))
        failed = [r for r in first["trace"] if r.get("tool") == "save_plan"]
        self.assertTrue(all(r["result"]["error"] == "storage_or_tool_failure" for r in failed))
        self.store.db.execute("DROP TRIGGER reject_plan")
        self.store.db.commit()
        second = Agent(self.store, MockModel()).run(self.request)
        self.assertEqual(second["status"], "completed")
        self.assertEqual([r["tool"] for r in second["trace"]], ["save_plan"])

    def test_permanent_service_failure_uses_alternative_and_keeps_assets(self):
        result = Agent(self.store, MockModel()).run(self.request, faults={"generate_script@premium": {"count": 10, "retryable": False}})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["plan"]["script"]["service"], "standard")
        self.assertEqual(sum(t["tool"] == "search_assets" for t in result["trace"]), 1)
        failed = [r for r in result["trace"] if not r["result"]["ok"]]
        self.assertEqual(len(failed), 1)
        self.assertFalse(failed[0]["result"]["retryable"])

    def test_user_script_priority_preserved_when_feasible(self):
        self.request.update(budget=10, replan_priority="preserve_script")
        result = Agent(self.store, MockModel()).run(self.request)
        self.assertEqual(result["plan"]["estimate"]["script_service"], "premium")
        self.assertEqual(result["plan"]["estimate"]["production"], "simple")
        self.assertEqual(result["plan"]["estimate"]["total_cost"], 10)

    def test_opposite_priority_changes_actual_plan(self):
        self.request.update(budget=10, replan_priority="preserve_production")
        result = Agent(self.store, MockModel()).run(self.request)
        self.assertEqual(result["plan"]["estimate"]["production"], "polished")
        self.assertEqual(result["plan"]["estimate"]["script_service"], "standard")

    def test_deadline_replans_to_faster_services(self):
        self.request["deadline"] = "2030-01-01T10:45:00+08:00"
        result = Agent(self.store, MockModel()).run(self.request)
        self.assertEqual(result["status"], "completed")
        self.assertLessEqual(result["plan"]["estimate"]["total_minutes"], 45)
        self.assertFalse(result["trace"][1]["result"]["fits_deadline"])

    def test_wall_clock_resume_rejects_expired_deadline_and_keeps_script(self):
        self.request.pop("start_at")
        self.request["deadline"] = "2030-01-01T12:00:00+00:00"
        clock = [datetime(2030, 1, 1, 10, tzinfo=timezone.utc)]
        agent = Agent(self.store, MockModel(), now=lambda: clock[0])
        first = agent.run(self.request, max_steps=3)
        self.assertTrue(first["preserved_results"]["script_ids"])
        clock[0] += timedelta(hours=3)
        second = agent.run(self.request)
        self.assertEqual(second["status"], "incomplete")
        self.assertIsNone(second["plan"])
        self.assertTrue(second["preserved_results"]["script_ids"])
        self.assertTrue(all(not e["fits_deadline"] for e in second["preserved_results"]["estimates"]))

    def test_wall_clock_checked_again_after_model_wait_before_save(self):
        self.request.pop("start_at")
        self.request["deadline"] = "2030-01-01T12:00:00+00:00"
        clock = [datetime(2030, 1, 1, 10, tzinfo=timezone.utc)]
        Agent(self.store, MockModel(), now=lambda: clock[0]).run(self.request, max_steps=3)
        class SlowModel(MockModel):
            def decide(self, state):
                action, info = super().decide(state)
                clock[0] += timedelta(hours=3)
                return action, info
        result = Agent(self.store, SlowModel(), now=lambda: clock[0]).run(self.request, max_steps=1)
        self.assertEqual(result["status"], "incomplete")
        self.assertFalse(result["trace"][0]["result"]["ok"])
        self.assertIsNone(result["plan"])

    def test_utc_z_timestamp_supported_on_python39(self):
        self.request.update(start_at="2030-01-01T02:00:00Z", deadline="2030-01-01T10:00:00Z")
        self.assertEqual(validate_request(self.request), [])
        self.assertEqual(Agent(self.store, MockModel()).run(self.request)["status"], "completed")

    def test_large_integer_budget_does_not_overflow_validation(self):
        self.request["budget"] = 10 ** 1000
        self.assertEqual(validate_request(self.request), [])

    def test_invalid_catalog_negative_cost_rejected_before_execution(self):
        catalog = json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))
        catalog["script_services"]["premium"]["cost"] = -1
        path = Path(self.tmp.name) / "bad-catalog.json"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaises(ValueError):
            Agent(self.store, MockModel(), path)

    def test_missing_inputs_do_not_require_installed_codex(self):
        model = CodexModel(executable="/nonexistent/codex")
        result = Agent(self.store, model).run({"topic": "活动"})
        self.assertEqual(result["status"], "needs_input")
        self.assertFalse(result["real_model_used"])

    def test_export_integrity_and_observation_to_action_chain(self):
        result = Agent(self.store, MockModel()).run(self.request)
        out = Path(self.tmp.name) / "evidence"
        write_result(result, out)
        self.assertEqual(verify_export(out), [])
        for entry in result["decision_inputs"]:
            self.assertNotIn("faults_remaining", entry["context"])
        path = out / "trace.jsonl"
        path.write_text(path.read_text(encoding="utf-8").replace('"total_cost": 12', '"total_cost": 1'), encoding="utf-8")
        self.assertTrue(verify_export(out))

    def test_resume_from_distinct_cli_processes_only_saves(self):
        self.store.close()
        first_out, second_out = Path(self.tmp.name) / "first", Path(self.tmp.name) / "second"
        common = [sys.executable, str(ROOT / "run.py"), str(ROOT / "examples/inputs/normal.json"), "--db", str(self.db), "--mode", "mock"]
        first = subprocess.run(common + ["--out", str(first_out), "--max-steps", "4", "--fail", "save_plan:1"], capture_output=True, text=True)
        second = subprocess.run(common + ["--out", str(second_out)], capture_output=True, text=True)
        self.store = Store(self.db)
        self.assertEqual((first.returncode, second.returncode), (2, 0))
        before = json.loads((first_out / "output.json").read_text(encoding="utf-8"))
        after = json.loads((second_out / "output.json").read_text(encoding="utf-8"))
        self.assertNotEqual(before["run_metadata"]["process_id"], after["run_metadata"]["process_id"])
        trace = [json.loads(line) for line in (second_out / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([t["tool"] for t in trace], ["save_plan"])
        self.assertEqual(verify_export(first_out), [])
        self.assertEqual(verify_export(second_out), [])


if __name__ == "__main__":
    unittest.main()
