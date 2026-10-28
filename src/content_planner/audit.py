"""独立核对实际证据：完整性、观察→动作关联和最终业务约束。"""
import hashlib
import json
from pathlib import Path

from .evidence import sha256, source_identity
from .validation import parse_time, validate_catalog


def verify_export(directory, current_source=True):
    root, errors = Path(directory), []
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if manifest["schema_version"] != 2:
            errors.append("不支持的证据版本。")
        for name, expected_hash in manifest["files"].items():
            if Path(name).name != name or hashlib.sha256((root / name).read_bytes()).hexdigest() != expected_hash:
                errors.append("文件内容与清单不一致：" + name)
        if current_source and manifest["source_sha256"] != source_identity()["source_sha256"]:
            errors.append("证据对应的实现与当前 src/run.py 不一致，须重新验证或明确标为历史记录。")
        request = json.loads((root / "input.json").read_text(encoding="utf-8"))
        output = json.loads((root / "output.json").read_text(encoding="utf-8"))
        catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
        validate_catalog(catalog)
        if sha256(request) != manifest["request_sha256"] or sha256(catalog) != manifest["catalog_sha256"]:
            errors.append("输入或资料语义哈希不一致。")
        trace = [json.loads(line) for line in (root / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
        contexts = [json.loads(line) for line in (root / "decision-inputs.jsonl").read_text(encoding="utf-8").splitlines()]
        if len(trace) != len(contexts):
            errors.append("动作与模型观察数量不一致。")
        for index, (record, entry) in enumerate(zip(trace, contexts)):
            context = entry["context"]
            if "faults_remaining" in context:
                errors.append("故障注入配置泄露给模型。")
            if sha256(context) != record["decision_input_sha256"]:
                errors.append("第 %s 步观察哈希不一致。" % record["step"])
            if "tool" in record:
                if entry.get("action") != {k: record[k] for k in ("tool", "arguments", "reason")}:
                    errors.append("第 %s 步模型动作与执行记录不一致。" % record["step"])
                if record["mode"] == "codex" and (record["model"].get("provider") != "codex-cli" or not record["model"].get("usage")):
                    errors.append("真实模型动作缺少 CLI 元数据或使用量。")
            if index and "tool" in trace[index - 1]:
                previous = context["calls"][-1] if context.get("calls") else {}
                if previous.get("result") != trace[index - 1]["result"] or previous.get("step") != trace[index - 1]["step"]:
                    errors.append("下一步模型输入未包含上一步实际返回。")
        real_used = any(t.get("mode") == "codex" and "tool" in t for t in trace)
        if output["real_model_used"] != real_used:
            errors.append("真实模型使用标志与本次 Trace 不一致。")
        if output["status"] == "completed":
            plan, estimate = output["plan"], output["plan"]["estimate"]
            assets = {a["id"]: a for a in catalog["assets"]}
            selected = [assets[a] for a in estimate["asset_ids"]]
            script_rate = catalog["script_services"][estimate["script_service"]]
            production_rate = catalog["production_services"][estimate["production"]]
            total = sum(a["cost"] for a in selected) + script_rate["cost"] + production_rate["cost"]
            minutes = sum(a["minutes"] for a in selected) + script_rate["minutes"] + production_rate["minutes"]
            if total != estimate["total_cost"] or total != sum(i["cost"] for i in estimate["line_items"]) or total > request["budget"]:
                errors.append("最终费用无法由资料逐项复算或超过预算。")
            if minutes != estimate["total_minutes"] or sum(s["minutes"] for s in plan["execution_plan"]) != minutes:
                errors.append("任务计划耗时与费用/耗时表不一致。")
            if parse_time(estimate["finish_at"]) > parse_time(request["deadline"]):
                errors.append("最终方案超过截止时间。")
            if not set(request.get("required_asset_ids", [])).issubset(estimate["asset_ids"]):
                errors.append("最终方案移除了必需素材。")
            if plan["save_status"] != "saved" or plan["activity_executed"] is not False:
                errors.append("保存或活动执行状态不正确。")
            for shot in plan["script"]["shots"]:
                if shot["source_id"] not in estimate["asset_ids"] or shot["voiceover"] not in assets[shot["source_id"]]["facts"]:
                    errors.append("脚本存在资料不支持的事实。")
            seen = set()
            for step in plan["execution_plan"]:
                if not set(step["depends_on"]).issubset(seen):
                    errors.append("计划依赖顺序不正确。")
                seen.add(step["step"])
            saved = any(t.get("tool") == "save_plan" and t["result"].get("ok") for t in trace)
            if not saved and output.get("stop_reason") != "existing_saved_plan":
                errors.append("没有本次实际保存成功或重复读取依据。")
        elif output.get("plan") is not None:
            errors.append("未完成却携带已保存方案。")
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        errors.append("证据结构或文件无效：" + str(exc))
    return errors
