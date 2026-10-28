import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from content_planner.agent import Agent, validate_request
from content_planner.models import MockModel, ModelError
from content_planner.store import Store
from content_planner.tools import ROOT, validate_args


class ConstantModel:
    mode = "mock"

    def __init__(self, action):
        self.action = action

    def decide(self, state):
        return copy.deepcopy(self.action), {"provider": "adversarial-test-double"}


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "state.sqlite3")
        self.agent = Agent(self.store, MockModel())
        self.request = json.loads((ROOT / "examples/inputs/normal.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_normal_save_is_real_and_budget_sum_is_correct(self):
        out = self.agent.run(self.request)
        self.assertEqual(out["status"], "completed")
        estimate = out["plan"]["estimate"]
        self.assertEqual(estimate["total_cost"], 12)
        self.assertEqual(sum(x["cost"] for x in estimate["line_items"]), 12)
        self.assertEqual(estimate["total_minutes"], 80)
        self.assertEqual(out["plan"], self.store.plan(self.request["request_id"]))
        self.assertFalse(out["plan"]["activity_executed"])

    def test_over_budget_replans_after_observation(self):
        self.request["budget"] = 10
        out = self.agent.run(self.request)
        estimates = [t["result"] for t in out["trace"] if t["tool"] == "estimate_plan"]
        self.assertEqual([e["total_cost"] for e in estimates], [12, 8])
        self.assertFalse(estimates[0]["fits_budget"])
        self.assertTrue(estimates[1]["fits_budget"])
        self.assertEqual(out["status"], "completed")

    def test_missing_budget_and_deadline_no_tools_run(self):
        for field in ("budget", "deadline"):
            with self.subTest(field=field):
                request = {k: v for k, v in self.request.items() if k != field}
                out = self.agent.run(request)
                self.assertEqual(out["status"], "needs_input")
                self.assertEqual(out["trace"], [])
                self.assertIsNone(self.store.plan(request["request_id"]))

    def test_zero_budget_is_not_treated_as_missing(self):
        self.request["budget"] = 0
        out = self.agent.run(self.request)
        self.assertEqual(out["status"], "incomplete")
        self.assertGreater(out["steps_this_run"], 0)

    def test_invalid_budgets(self):
        for value in (True, -1, float("nan"), float("inf"), "10"):
            with self.subTest(value=value):
                self.assertTrue(validate_request({**self.request, "budget": value}))

    def test_invalid_or_naive_deadline(self):
        for value in ("tomorrow", "2030-01-01T18:00:00", 2):
            self.assertTrue(validate_request({**self.request, "deadline": value}))

    def test_deadline_infeasible_cannot_save(self):
        self.request["deadline"] = "2030-01-01T10:10:00+08:00"
        out = self.agent.run(self.request)
        self.assertEqual(out["status"], "incomplete")
        self.assertIsNone(out["plan"])
        self.assertTrue(all(not e["fits_deadline"] for e in out["preserved_results"]["estimates"]))

    def test_tool_failure_keeps_successful_steps(self):
        out = self.agent.run(self.request, faults={"generate_script": 1})
        self.assertEqual(out["status"], "completed")
        names = [t["tool"] for t in out["trace"]]
        self.assertEqual(names.count("search_assets"), 1)
        self.assertEqual(names.count("estimate_plan"), 1)
        calls = [t for t in out["trace"] if t["tool"] == "generate_script"]
        self.assertEqual([t["result"]["ok"] for t in calls], [False, True])

    def test_save_failure_does_not_claim_completion(self):
        out = self.agent.run(self.request, faults={"save_plan": 100})
        self.assertEqual(out["status"], "incomplete")
        self.assertIsNone(out["plan"])
        self.assertEqual(out["steps"][-1]["status"], "failed")
        self.assertTrue(out["preserved_results"]["script_ids"])
        self.assertIsNone(self.store.plan(self.request["request_id"]))

    def test_repeat_has_one_plan_and_no_new_model_or_tool_calls(self):
        first = self.agent.run(self.request)
        second = self.agent.run(self.request)
        self.assertEqual(first["plan"]["plan_id"], second["plan"]["plan_id"])
        self.assertEqual(second["steps_this_run"], 0)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM plans").fetchone()[0], 1)
        self.assertTrue(second["resumed"])

    def test_same_id_with_different_request_rejected(self):
        self.agent.run(self.request)
        with self.assertRaises(ValueError):
            self.agent.run({**self.request, "budget": 9})

    def test_step_limit_is_incomplete_and_resume_skips_successes(self):
        first = self.agent.run(self.request, max_steps=3, faults={"generate_script": 1})
        self.assertEqual(first["status"], "incomplete")
        self.assertEqual(first["steps_this_run"], 3)
        # 模拟重启进程：重新打开数据库、重建 Agent。
        self.store.close()
        self.store = Store(Path(self.tmp.name) / "state.sqlite3")
        second = Agent(self.store, MockModel()).run(self.request)
        self.assertEqual(second["status"], "completed")
        self.assertEqual([t["tool"] for t in second["trace"]], ["generate_script", "save_plan"])

    def test_save_crash_before_checkpoint_recovers_from_database(self):
        first = self.agent.run(self.request)
        row = self.store.db.execute("SELECT state FROM runs").fetchone()
        state = json.loads(row[0])
        state["saved_plan"] = None
        state["status"] = "running"
        self.store.db.execute("UPDATE runs SET state=?", (json.dumps(state),))
        self.store.db.commit()
        out = self.agent.run(self.request)
        self.assertEqual(out["status"], "completed")
        self.assertEqual(out["plan"], first["plan"])
        self.assertEqual(out["steps_this_run"], 0)

    def test_insufficient_budget_reports_gap(self):
        self.request["budget"] = 1
        out = self.agent.run(self.request)
        self.assertEqual(out["status"], "incomplete")
        self.assertIn("4", out["message"])
        self.assertFalse(any(t["tool"] == "generate_script" for t in out["trace"]))

    def test_no_assets_requests_input(self):
        self.request["topic"] = "深海潜艇科普"
        out = self.agent.run(self.request)
        self.assertEqual(out["status"], "needs_input")
        self.assertIsNone(out["plan"])

    def test_required_assets_cannot_be_silently_removed(self):
        self.request["required_asset_ids"] = ["A99"]
        out = self.agent.run(self.request)
        self.assertEqual(out["status"], "needs_input")
        self.assertIsNone(out["plan"])

    def test_invalid_save_cannot_bypass_dependencies(self):
        model = ConstantModel({"tool": "save_plan", "arguments": {"candidate_id": "invented"}, "reason": "测试越过依赖"})
        out = Agent(self.store, model).run(self.request, max_steps=2)
        self.assertEqual(out["status"], "incomplete")
        self.assertTrue(all(not t["result"]["ok"] for t in out["trace"]))

    def test_model_cannot_claim_completed_using_finish(self):
        model = ConstantModel({"tool": "finish", "arguments": {"status": "completed", "message": "伪报成功"}, "reason": "边界测试"})
        out = Agent(self.store, model).run(self.request, max_steps=1)
        self.assertEqual(out["status"], "incomplete")
        self.assertIsNone(out["plan"])

    def test_unknown_tool_rejected(self):
        model = ConstantModel({"tool": "publish", "arguments": {}, "reason": "边界测试"})
        out = Agent(self.store, model).run(self.request, max_steps=1)
        self.assertFalse(out["trace"][0]["result"]["ok"])

    def test_extra_tool_arguments_rejected(self):
        with self.assertRaises(ValueError):
            validate_args("search_assets", {"query": "剪辑", "budget": 100})

    def test_mock_trace_never_claims_real_model(self):
        out = self.agent.run(self.request)
        self.assertFalse(out["real_model_used"])
        self.assertEqual(out["evidence_modes"], ["mock"])
        self.assertTrue(all("MOCK" in t["reason"] for t in out["trace"]))

    def test_changed_catalog_does_not_reuse_stale_plan(self):
        self.agent.run(self.request)
        catalog = copy.deepcopy(self.agent.tools.catalog)
        catalog["script_services"]["premium"]["cost"] = 100
        path = Path(self.tmp.name) / "catalog.json"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaises(ValueError):
            Agent(self.store, MockModel(), path).run(self.request)

    def test_model_error_preserves_checkpoint(self):
        class BrokenModel:
            mode = "mock"

            def decide(self, state):
                raise ModelError("模拟模型断线")
        out = Agent(self.store, BrokenModel()).run(self.request)
        self.assertEqual(out["status"], "incomplete")
        self.assertEqual(out["trace"][0]["event"], "model_error")
        resumed = self.agent.run(self.request)
        self.assertEqual(resumed["status"], "completed")

    def test_over_budget_candidate_cannot_generate_or_save(self):
        class BadPlanner:
            mode = "mock"

            def decide(self, state):
                if not state["assets"]:
                    action = {"tool": "search_assets", "arguments": {"query": "剪辑"}}
                elif not state["estimates"]:
                    action = {"tool": "estimate_plan", "arguments": {"asset_ids": ["A01"], "script_service": "premium", "production": "polished"}}
                else:
                    candidate = next(iter(state["estimates"]))
                    action = {"tool": "generate_script" if len(state["calls"]) == 2 else "save_plan", "arguments": {"candidate_id": candidate}}
                return {**action, "reason": "测试恶意越过预算检查"}, {}
        self.request["budget"] = 10
        out = Agent(self.store, BadPlanner()).run(self.request, max_steps=4)
        self.assertEqual(out["status"], "incomplete")
        self.assertEqual([t["result"]["ok"] for t in out["trace"]], [True, True, False, False])
        self.assertEqual(out["preserved_results"]["script_ids"], [])
        self.assertIsNone(out["plan"])

    def test_later_failure_is_not_masked_by_earlier_success(self):
        class MixedPlanner:
            mode = "mock"

            def decide(self, state):
                index = len(state["calls"])
                if index == 0:
                    name, args = "search_assets", {"query": "剪辑"}
                elif index == 1:
                    name, args = "estimate_plan", {"asset_ids": ["A01"], "script_service": "premium", "production": "polished"}
                else:
                    name = "generate_script"
                    args = {"candidate_id": next(iter(state["estimates"])) if index == 2 else "invalid-new-candidate"}
                return {"tool": name, "arguments": args, "reason": "测试历史成功不能掩盖最新失败"}, {}
        out = Agent(self.store, MixedPlanner()).run(self.request, max_steps=4)
        step = next(s for s in out["steps"] if s["tool"] == "generate_script")
        self.assertEqual(step["status"], "failed")
        self.assertEqual(step["successes"], 1)
        self.assertTrue(out["preserved_results"]["script_ids"])


if __name__ == "__main__":
    unittest.main()
