#!/usr/bin/env python3
"""从全新数据库执行验收；保存实际产物，并独立复算约束、验证观察链。"""
import argparse
import json
import subprocess
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from content_planner.agent import Agent, write_result
from content_planner.audit import verify_export
from content_planner.models import CodexModel, MockModel
from content_planner.store import Store

CASES = ["normal", "replan", "user-priority", "opposite-priority", "missing", "missing-budget", "missing-deadline", "tool-failure", "service-fallback", "save-failure", "impossible", "deadline", "deadline-replan", "no-assets", "resume"]
COMPLETED = {"normal", "replan", "user-priority", "opposite-priority", "tool-failure", "service-fallback", "deadline-replan", "resume"}
NEEDS_INPUT = {"missing", "missing-budget", "missing-deadline", "no-assets"}


def load_export(path):
    output = json.loads((path / "output.json").read_text(encoding="utf-8"))
    output["trace"] = [json.loads(line) for line in (path / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
    return output


def execute_case(name, mode, out_root, model_name, timeout=120):
    print(json.dumps({"case": name, "event": "started", "mode": mode}), flush=True)
    source = {"tool-failure": "normal", "service-fallback": "normal", "save-failure": "normal", "resume": "normal", "opposite-priority": "user-priority", "deadline-replan": "deadline-tight"}.get(name, name)
    request = json.loads((ROOT / "examples/inputs" / (source + ".json")).read_text(encoding="utf-8"))
    request["request_id"] = "eval-" + name
    if name == "opposite-priority":
        request["replan_priority"] = "preserve_production"
    expected = "completed" if name in COMPLETED else "needs_input" if name in NEEDS_INPUT else "incomplete"
    checks, directories = {}, [out_root / name]
    with tempfile.TemporaryDirectory(prefix="content-planner-eval-") as tmp:
        db = Path(tmp) / "state.sqlite3"
        if name == "resume":
            input_file = Path(tmp) / "request.json"
            input_file.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            common = [sys.executable, str(ROOT / "run.py"), str(input_file), "--mode", mode, "--db", str(db), "--model-timeout", str(timeout)]
            if model_name:
                common += ["--model", model_name]
            first_process = subprocess.run(common + ["--max-steps", "4", "--fail", "save_plan:1", "--out", str(directories[0])], capture_output=True, text=True, cwd=str(ROOT))
            second_dir = out_root / "resume-continued"
            directories.append(second_dir)
            second_process = subprocess.run(common + ["--out", str(second_dir)], capture_output=True, text=True, cwd=str(ROOT))
            first, output = load_export(directories[0]), load_export(second_dir)
            checks["distinct_processes"] = first["run_metadata"]["process_id"] != output["run_metadata"]["process_id"]
            checks["exit_codes"] = (first_process.returncode, second_process.returncode) == (2, 0)
            checks["initial_incomplete_with_script_preserved"] = first["status"] == "incomplete" and bool(first["preserved_results"]["script_ids"])
            checks["continued_only_failed_save"] = [t.get("tool") for t in output["trace"]] == ["save_plan"]
            checks["same_script_reused"] = first["preserved_results"]["script_ids"] == output["preserved_results"]["script_ids"]
        else:
            model = MockModel() if mode == "mock" else CodexModel(model=model_name, timeout=timeout)
            store = Store(db)
            try:
                faults = {"generate_script": 1} if name == "tool-failure" else {"save_plan": 100} if name == "save-failure" else {"generate_script@premium": {"count": 100, "retryable": False}} if name == "service-fallback" else {}
                agent = Agent(store, model)
                first = output = agent.run(request, faults=faults)
                write_result(output, directories[0])
                if name == "normal":
                    repeated = agent.run(request)
                    repeated_dir = out_root / "repeat"
                    write_result(repeated, repeated_dir)
                    directories.append(repeated_dir)
                    checks["repeat_deduplicated"] = repeated["steps_this_run"] == 0 and store.db.execute("SELECT COUNT(*) FROM plans").fetchone()[0] == 1
            finally:
                store.close()
        checks["expected_status"] = output["status"] == expected
        checks["no_unexpected_model_failure"] = output.get("stop_reason") != "model_error"
        if name in ("impossible", "deadline"):
            checks["stopped_on_business_constraints"] = output.get("stop_reason") == "model_stopped" and output["constraint_summary"]["checked_candidates"] > 0
        if name in ("replan", "user-priority", "opposite-priority"):
            estimates = [t["result"] for t in first["trace"] if t.get("tool") == "estimate_plan" and t["result"].get("ok")]
            checks["budget_observation_changed_plan"] = bool(len(estimates) >= 2 and not estimates[0]["fits_budget"] and estimates[-1]["fits_budget"])
        if name == "user-priority":
            estimate = (output.get("plan") or {}).get("estimate", {})
            checks["respects_confirmed_user_priority"] = estimate.get("script_service") == "premium" and estimate.get("production") == "simple"
        if name == "opposite-priority":
            estimate = (output.get("plan") or {}).get("estimate", {})
            checks["counterfactual_changes_plan"] = estimate.get("production") == "polished" and estimate.get("script_service") != "premium"
        if name == "deadline-replan":
            estimates = [t["result"] for t in first["trace"] if t.get("tool") == "estimate_plan" and t["result"].get("ok")]
            checks["deadline_observation_changed_plan"] = bool(len(estimates) >= 2 and not estimates[0]["fits_deadline"] and estimates[-1]["fits_deadline"])
        if name in ("tool-failure", "save-failure", "service-fallback"):
            checks["failure_really_observed"] = any(t.get("result", {}).get("error") == "injected_tool_failure" for t in first["trace"])
            checks["successful_search_reused"] = sum(t.get("tool") == "search_assets" and t["result"]["ok"] for t in first["trace"]) == 1
        if name == "service-fallback":
            failed = [t for t in first["trace"] if t.get("tool") == "generate_script" and not t["result"]["ok"]]
            checks["permanent_failure_not_retried_unchanged"] = len(failed) == 1 and failed[0]["result"].get("retryable") is False
            checks["alternative_service_saved"] = bool(output.get("plan") and output["plan"]["script"]["service"] != "premium")
        if name == "save-failure":
            checks["successful_script_not_regenerated"] = sum(t.get("tool") == "generate_script" for t in first["trace"]) == 1
            checks["not_falsely_saved"] = output["plan"] is None
        if name in ("missing", "missing-budget", "missing-deadline"):
            checks["no_model_or_tool_calls"] = output["steps_this_run"] == 0 and not output["real_model_used"]
        errors = {p.name: verify_export(p) for p in directories}
        checks["independent_evidence_verification"] = not any(errors.values())
        report = {"case": name, "expected": expected, "actual": output["status"], "passed": all(checks.values()), "checks": checks,
                  "directories": [str(p.relative_to(out_root)) for p in directories], "evidence_errors": errors,
                  "model_actions": sum(t.get("mode") == "codex" and "tool" in t for t in first["trace"]) + (sum(t.get("mode") == "codex" and "tool" in t for t in output["trace"]) if name == "resume" else 0)}
        print(json.dumps(report, ensure_ascii=False), flush=True)
        return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("mock", "codex"), default="mock")
    parser.add_argument("--case", choices=CASES, action="append")
    parser.add_argument("--out", type=Path, help="输出根目录；默认写入 .runtime/evaluations 下的新目录，不覆盖提交证据")
    parser.add_argument("--model", help="真实验证可明确指定目标模型，记录客户端请求的型号")
    parser.add_argument("--model-timeout", type=int, default=120)
    parser.add_argument("--jobs", type=int, choices=(1, 2), default=1, help="不同用例使用独立数据库，可并行运行")
    args = parser.parse_args()
    cases = args.case or CASES
    if len(set(cases)) != len(cases):
        parser.error("--case 不能重复。")
    run_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    out_root = (args.out or ROOT / ".runtime/evaluations" / run_name) / args.mode
    if out_root.exists():
        parser.error("输出目录已存在，拒绝覆盖证据；请选择新 --out。")
    out_root.mkdir(parents=True)
    def run_case(name):
        try:
            return execute_case(name, args.mode, out_root, args.model, args.model_timeout)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            report = {"case": name, "passed": False, "actual": "evaluation_error", "error": str(exc), "model_actions": 0, "directories": []}
            print(json.dumps(report, ensure_ascii=False), flush=True)
            return report
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        reports = list(executor.map(run_case, cases))
    report = {"schema_version": 2, "mode": args.mode, "generated_at": datetime.now(timezone.utc).isoformat(), "cases": reports,
              "all_passed": all(r["passed"] for r in reports), "model_actions": sum(r["model_actions"] for r in reports),
              "scope": "真实模型小样本行为验证；缺信息和重复请求不调用模型" if args.mode == "codex" else "确定性流程测试，不证明真实模型效果"}
    (out_root / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("评估结果：" + str(out_root.resolve()))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
