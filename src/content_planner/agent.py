import copy
import os
import platform
import time
import uuid
from datetime import datetime, timezone

from .models import ModelError
from .evidence import sha256, source_identity, visible_state
from .store import digest
from .tools import Tools
from .validation import parse_time, valid_number


def validate_request(request):
    errors = []
    if not isinstance(request, dict):
        return ["输入必须是 JSON 对象。"]
    for key in ("request_id", "topic", "deadline"):
        if not isinstance(request.get(key), str) or not request[key].strip():
            errors.append("请提供 " + key)
    budget = request.get("budget")
    if not valid_number(budget):
        errors.append("请提供非负、有限的数字 budget；0 是有效预算。")
    for key in ("deadline", "start_at"):
        if key in request:
            try:
                parse_time(request[key])
            except (ValueError, TypeError):
                errors.append(key + " 必须是带时区的 ISO 8601 时间。")
    ids = request.get("required_asset_ids", [])
    if not isinstance(ids, list) or any(not isinstance(x, str) or not x.strip() for x in ids) or len(ids) != len(set(ids)):
        errors.append("required_asset_ids 必须是不重复的素材 ID 数组。")
    for key, allowed in (("preferred_script_service", ("premium", "standard", "template")), ("preferred_production", ("polished", "simple"))):
        if key in request and request[key] not in allowed:
            errors.append(key + " 不在允许范围内。")
    if "replan_priority" in request and request["replan_priority"] not in ("preserve_script", "preserve_production"):
        errors.append("replan_priority 必须为 preserve_script 或 preserve_production。")
    allowed_fields = {"request_id", "topic", "budget", "deadline", "start_at", "required_asset_ids", "preferred_script_service", "preferred_production", "replan_priority"}
    if set(request) - allowed_fields:
        errors.append("存在未支持的字段：" + ", ".join(sorted(set(request) - allowed_fields)))
    return errors


class Agent:
    def __init__(self, store, model, catalog_path=None, now=None):
        self.store, self.model = store, model
        self.tools = Tools(store, catalog_path, now)

    def run(self, request, max_steps=12, faults=None):
        self.run_info = {"run_id": uuid.uuid4().hex, "started_at": datetime.now(timezone.utc).isoformat(),
                         "python": platform.python_version(), "process_id": os.getpid(), "mode": self.model.mode,
                         "max_steps": max_steps, "fault_injection": copy.deepcopy(faults or {}),
                         "catalog_sha256": sha256(self.tools.catalog), **source_identity()}
        errors = validate_request(request)
        if errors:
            return {"status": "needs_input", "message": "；".join(errors), "mode": self.model.mode,
                    "real_model_used": False, "evidence_modes": [], "steps_this_run": 0,
                    "steps": [], "plan": None, "preserved_results": {}, "trace": [], "request": request,
                    "stop_reason": "input_missing", "decision_inputs": [], "run_metadata": self.run_info,
                    "catalog": self.tools.catalog}
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
            raise ValueError("max_steps 必须大于 0。")
        fingerprint = digest({"request": request, "catalog": self.tools.catalog})
        state = self.store.load(request["request_id"], fingerprint)
        resumed = state is not None
        if state is None:
            state = {"request": copy.deepcopy(request), "planning_clock": request.get("start_at") or self.tools.now().isoformat(),
                     "assets": {}, "estimates": {}, "scripts": {}, "saved_plan": None,
                     "search_count": 0, "calls": [], "status": "running", "message": "",
                     "faults_remaining": dict(faults or {}), "catalog_version": self.tools.catalog["version"]}
        # 保存与 checkpoint 之间崩溃，也以 SQLite 中真实方案为准恢复。
        saved = self.store.plan(request["request_id"])
        if saved:
            state["saved_plan"] = saved
            state["status"], state["message"] = "completed", "已保存方案；重复执行复用现有结果。"
            state["stop_reason"] = "existing_saved_plan"
            return self.result(state, [], resumed)
        state["status"], state["message"] = "running", ""
        state["clock_mode"] = "simulation" if request.get("start_at") else "wall_clock"
        state["call_offset"] = len(state["calls"])
        state["stop_reason"] = "running"
        self.store.checkpoint(state, fingerprint)
        trace, decision_inputs = [], []
        for index in range(max_steps):
            self.tools.refresh_estimates(state)
            state["remaining_steps"] = max_steps - index
            context = visible_state(state)
            observed_hash = sha256(context)
            started = time.monotonic()
            try:
                action, model_info = self.model.decide(copy.deepcopy(state))
                if not isinstance(action, dict) or not isinstance(action.get("reason"), str) or not action["reason"].strip():
                    raise ModelError("模型动作缺少简短依据。")
                name, args = action.get("tool"), action.get("arguments")
                if not isinstance(name, str):
                    raise ModelError("模型未指定工具。")
            except (ModelError, OSError, ValueError, TypeError) as exc:
                state["status"], state["message"] = "incomplete", str(exc)
                state["stop_reason"] = "model_error"
                trace.append({"step": len(state["calls"]) + 1, "event": "model_error", "message": str(exc), "mode": self.model.mode,
                              "decision_input_sha256": observed_hash})
                decision_inputs.append({"step": len(state["calls"]) + 1, "context": context, "model_error": str(exc)})
                break
            observed = self.tools.execute(name, args, state)
            record = {"step": len(state["calls"]) + 1, "mode": self.model.mode, "model": model_info,
                      "tool": name, "arguments": args, "reason": action["reason"], "result": copy.deepcopy(observed),
                      "decision_input_sha256": observed_hash, "observed_at": datetime.now(timezone.utc).isoformat(),
                      "latency_ms": round((time.monotonic() - started) * 1000)}
            decision_inputs.append({"step": record["step"], "context": context, "action": copy.deepcopy(action)})
            state["calls"].append(copy.deepcopy(record))
            trace.append(record)
            if state["saved_plan"]:
                state["status"], state["message"] = "completed", "方案已实际保存；活动制作仍为计划。"
                state["stop_reason"] = "saved"
            self.store.checkpoint(state, fingerprint)
            if state["status"] != "running":
                break
        if state["status"] == "running":
            state["status"], state["message"] = "incomplete", "达到本次工具调用上限 %s；成功步骤已保留，可用相同输入续跑。" % max_steps
            state["stop_reason"] = "step_limit"
        elif state["stop_reason"] == "running":
            state["stop_reason"] = "model_stopped"
        self.store.checkpoint(state, fingerprint)
        return self.result(state, trace, resumed, decision_inputs)

    def result(self, state, trace, resumed, decision_inputs=None):
        names = ("search_assets", "estimate_plan", "generate_script", "save_plan")
        steps = []
        for name in names:
            calls = [c for c in state["calls"] if c["tool"] == name]
            successful = [c for c in calls if c["result"]["ok"]]
            # 最新一次失败不能被该工具更早的成功掩盖；旧成果单独保存在 preserved_results。
            steps.append({"tool": name, "status": ("succeeded" if calls[-1]["result"]["ok"] else "failed") if calls else "pending",
                          "attempts": len(calls), "successes": len(successful)})
        estimates = list(state["estimates"].values())
        self.run_info["finished_at"] = datetime.now(timezone.utc).isoformat()
        return {"status": state["status"], "message": state["message"], "mode": self.model.mode,
                "stop_reason": state["stop_reason"], "clock_mode": state.get("clock_mode", "simulation" if state["request"].get("start_at") else "wall_clock"),
                "run_metadata": copy.deepcopy(self.run_info), "catalog": self.tools.catalog,
                "real_model_used": any(c["mode"] == "codex" for c in trace if "tool" in c),
                "evidence_modes": sorted({c["mode"] for c in state["calls"]}),
                "request": state["request"], "planning_clock": state["planning_clock"],
                "resumed": resumed, "steps_this_run": len([c for c in trace if "tool" in c]),
                "steps": steps, "plan": state["saved_plan"], "preserved_results": {
                    "asset_ids": list(state["assets"]), "estimates": estimates,
                    "script_ids": [s["script_id"] for s in state["scripts"].values()], "scripts": list(state["scripts"].values())},
                "constraint_summary": {"scope": "evaluated_candidates_only", "checked_candidates": len(estimates),
                    "feasible_candidate_ids": [e["candidate_id"] for e in estimates if e["fits_budget"] and e["fits_deadline"]],
                    "minimum_checked_budget_gap": min((e["budget_gap"] for e in estimates), default=None),
                    "minimum_checked_minutes_gap": min((e["minutes_gap"] for e in estimates), default=None)},
                "trace": trace, "decision_inputs": decision_inputs or []}


from .reporting import write_result  # 保留原有导入入口；渲染与循环分离。
