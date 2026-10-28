"""业务工具允许 Mock；预算、依赖、来源、保存状态由代码校验。"""
import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .store import digest
from .validation import parse_time, validate_catalog

ROOT = Path(__file__).resolve().parents[2]


def tool(name, description, properties, required):
    return {"name": name, "description": description, "parameters": {
        "type": "object", "properties": properties, "required": required, "additionalProperties": False}}


TEXT = {"type": "string", "minLength": 1}
TOOL_SPECS = [
    tool("search_assets", "检索合成素材。无结果可改写 query 后再次检索，或说明资料不足。", {"query": TEXT}, ["query"]),
    tool("estimate_plan", "按价目表测算一个候选方案的预算和完成时间。生成脚本前必须有可行测算。", {
        "asset_ids": {"type": "array", "items": TEXT, "minItems": 1},
        "script_service": {"type": "string", "enum": ["premium", "standard", "template"]},
        "production": {"type": "string", "enum": ["polished", "simple"]},
    }, ["asset_ids", "script_service", "production"]),
    tool("generate_script", "根据可行候选方案生成合成脚本。成功结果可复用；失败不会清空测算和素材。", {"candidate_id": TEXT}, ["candidate_id"]),
    tool("save_plan", "校验候选方案可行且脚本已成功后保存，按 request_id 幂等。只保存方案，不执行活动。", {"candidate_id": TEXT}, ["candidate_id"]),
    tool("finish", "仅在缺信息或不能继续时结束。成功必须实际调用 save_plan。", {
        "status": {"type": "string", "enum": ["needs_input", "incomplete"]}, "message": TEXT,
    }, ["status", "message"]),
]


def validate_args(name, args):
    specs = {s["name"]: s["parameters"] for s in TOOL_SPECS}
    if name not in specs or not isinstance(args, dict):
        raise ValueError("未知工具或工具参数不是对象。")
    schema = specs[name]
    if set(args) != set(schema["required"]):
        raise ValueError("工具参数缺失或包含未声明字段。")
    for key, value in args.items():
        rule = schema["properties"][key]
        if rule["type"] == "string" and (not isinstance(value, str) or not value.strip()):
            raise ValueError(key + " 必须是非空字符串。")
        if rule["type"] == "array" and (not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value)):
            raise ValueError(key + " 必须是非空字符串数组。")
        if "enum" in rule and value not in rule["enum"]:
            raise ValueError(key + " 不在允许范围内。")


class Tools:
    def __init__(self, store, catalog_path=None, now=None):
        self.store = store
        self.catalog = json.loads(Path(catalog_path or ROOT / "data/catalog.json").read_text(encoding="utf-8"))
        validate_catalog(self.catalog)
        self.now = now or (lambda: datetime.now(timezone.utc))

    def refresh_clock(self, state):
        if not state["request"].get("start_at"):
            state["planning_clock"] = self.now().isoformat()

    def refresh_estimates(self, state):
        self.refresh_clock(state)
        for candidate_id, old in list(state["estimates"].items()):
            state["estimates"][candidate_id] = self.timing(state, old)

    @staticmethod
    def timing(state, estimate):
        end = parse_time(state["planning_clock"]) + timedelta(minutes=estimate["total_minutes"])
        deadline = parse_time(state["request"]["deadline"])
        return {**estimate, "finish_at": end.isoformat(), "fits_deadline": end <= deadline,
                "minutes_gap": max(0, math.ceil((end - deadline).total_seconds() / 60)),
                "checked_at": state["planning_clock"]}

    def execute(self, name, args, state):
        try:
            validate_args(name, args)
            # 故障注入持久化，续跑时不会重新注入已经消耗的故障。
            service = state["estimates"].get(args.get("candidate_id"), {}).get("script_service")
            fault_key = name + "@" + service if service and name + "@" + service in state["faults_remaining"] else name
            rule = state["faults_remaining"].get(fault_key, 0)
            rule = {"count": rule, "retryable": True} if isinstance(rule, int) else dict(rule)
            if rule.get("count", 0) > 0:
                rule["count"] -= 1
                state["faults_remaining"][fault_key] = rule
                retryable = rule.get("retryable", True)
                return {"ok": False, "error": "injected_tool_failure", "retryable": retryable,
                        "service": service, "message": name + (" 模拟临时故障，可由模型决定是否重试。" if retryable else " 服务不可用，不应原样重试；可选择替代服务或停止。")}
            return getattr(self, name)(state, **args)
        except (ValueError, KeyError, TypeError) as exc:
            return {"ok": False, "error": "invalid_tool_request", "retryable": False, "message": str(exc)}
        except (sqlite3.Error, OSError):
            return {"ok": False, "error": "storage_or_tool_failure", "retryable": True,
                    "message": name + " 实际执行失败，没有确认保存成功；已有成果保留。"}

    def search_assets(self, state, query):
        query = query.strip().lower()
        found = [asset for asset in self.catalog["assets"] if
                 query in (asset["title"] + " ".join(asset["tags"])).lower()
                 or any(tag.lower() in query for tag in asset["tags"])]
        for asset in found:
            state["assets"][asset["id"]] = asset
        state["search_count"] += 1
        return {"ok": True, "assets": found, "count": len(found), "catalog_version": self.catalog["version"]}

    def estimate_plan(self, state, asset_ids, script_service, production):
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError("素材 ID 不可重复。")
        if not set(state["request"].get("required_asset_ids", [])).issubset(asset_ids):
            raise ValueError("不能移除用户要求的素材。")
        assets = [state["assets"][asset_id] for asset_id in asset_ids]
        script = self.catalog["script_services"][script_service]
        output = self.catalog["production_services"][production]
        items = [{"name": a["id"], "cost": a["cost"], "minutes": a["minutes"]} for a in assets]
        items += [{"name": "script:" + script_service, **script}, {"name": "production:" + production, **output}]
        total = sum(i["cost"] for i in items)
        minutes = sum(i["minutes"] for i in items)
        self.refresh_clock(state)
        candidate = {"asset_ids": asset_ids, "script_service": script_service, "production": production}
        candidate_id = digest({**candidate, "catalog_version": self.catalog["version"]})
        result = {"ok": True, "candidate_id": candidate_id, **candidate, "line_items": items,
                  "total_cost": total, "total_minutes": minutes,
                  "fits_budget": total <= state["request"]["budget"],
                  "budget_gap": max(0, total - state["request"]["budget"]),
                  "catalog_version": self.catalog["version"]}
        result = self.timing(state, result)
        state["estimates"][candidate_id] = result
        return result

    def feasible(self, state, candidate_id):
        self.refresh_clock(state)
        estimate = self.timing(state, state["estimates"][candidate_id])
        state["estimates"][candidate_id] = estimate
        if not (estimate["fits_budget"] and estimate["fits_deadline"]):
            raise ValueError("方案超预算或超截止时间，不能生成或保存。先重新测算。")
        return estimate

    @staticmethod
    def script_key(estimate):
        return digest({"assets": estimate["asset_ids"], "service": estimate["script_service"]})

    def generate_script(self, state, candidate_id):
        estimate = self.feasible(state, candidate_id)
        key = self.script_key(estimate)
        if key in state["scripts"]:
            return {"ok": True, "cache_hit": True, **state["scripts"][key]}
        facts = [(a, fact) for a in estimate["asset_ids"] for fact in state["assets"][a]["facts"]]
        script = {"script_id": "S-" + key, "service": estimate["script_service"],
                  "title": state["request"]["topic"], "source_ids": estimate["asset_ids"],
                  "shots": [{"order": i + 1, "visual": "展示素材 " + asset,
                             "voiceover": fact, "source_id": asset} for i, (asset, fact) in enumerate(facts)],
                  "generator": "local-synthetic-template"}
        state["scripts"][key] = script
        return {"ok": True, "cache_hit": False, **script}

    def save_plan(self, state, candidate_id):
        estimate = self.feasible(state, candidate_id)
        script = state["scripts"].get(self.script_key(estimate))
        if not script:
            raise ValueError("脚本步骤尚未成功，不能保存方案。")
        request_id = state["request"]["request_id"]
        existing = self.store.plan(request_id)
        plan = {"plan_id": "P-" + digest(request_id), "request_id": request_id,
                "topic": state["request"]["topic"], "deadline": state["request"]["deadline"],
                "budget": state["request"]["budget"], "estimate": estimate, "script": script,
                "execution_plan": [
                    {"step": "准备素材", "status": "prepared", "depends_on": [], "minutes": sum(state["assets"][a]["minutes"] for a in estimate["asset_ids"])},
                    {"step": "生成脚本", "status": "generated", "depends_on": ["准备素材"], "minutes": self.catalog["script_services"][estimate["script_service"]]["minutes"]},
                    {"step": "内容制作（仅规划，尚未实际制作）", "status": "planned", "depends_on": ["生成脚本"], "minutes": self.catalog["production_services"][estimate["production"]]["minutes"]}],
                "save_status": "saved", "activity_executed": False}
        saved = self.store.save_plan(request_id, plan)
        state["saved_plan"] = saved
        return {"ok": True, "plan_id": saved["plan_id"], "save_status": "saved", "deduplicated": bool(existing)}

    def finish(self, state, status, message):
        state["status"] = status
        state["message"] = message
        return {"ok": True, "status": status, "message": message}
