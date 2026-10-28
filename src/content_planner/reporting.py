"""从实际结果生成可读报告和完整性清单，不编写预设成功轨迹。"""
import hashlib
import json
import os
import tempfile
from pathlib import Path

from .evidence import sha256


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def atomic_write(path, content):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=str(path.parent), delete=False) as tmp:
        tmp.write(content)
        temporary = Path(tmp.name)
    try:
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists():
            temporary.unlink()


def result_markdown(result):
    request, plan = result["request"], result.get("plan")
    lines = ["# 内容活动方案", "", "状态：**" + result["status"] + "**", "", result["message"], ""]
    if isinstance(request, dict):
        lines += ["- 主题：" + str(request.get("topic", "未提供")), "- 预算：" + str(request.get("budget", "未提供")),
                  "- 截止时间：" + str(request.get("deadline", "未提供")), ""]
    if plan:
        estimate = plan["estimate"]
        lines += ["方案 ID：" + plan["plan_id"], "", "预计总价：**%s 个模拟单位**；串行计划耗时：**%s 分钟**；预计结束：%s。" %
                  (estimate["total_cost"], estimate["total_minutes"], estimate["finish_at"]), "",
                  "| 费用项目 | 模拟费用 | 分钟 |", "|---|---:|---:|"]
        lines += ["| %s | %s | %s |" % (i["name"], i["cost"], i["minutes"]) for i in estimate["line_items"]]
        lines += ["", "| 任务 | 依赖 | 分钟 | 状态 |", "|---|---|---:|---|"]
        lines += ["| %s | %s | %s | %s |" % (s["step"], "、".join(s["depends_on"]) or "无", s["minutes"], s.get("status", "见工具记录")) for s in plan["execution_plan"]]
        lines += ["", "## 可编辑脚本", "", "标题：" + plan["script"]["title"], ""]
        lines += ["%s. %s；旁白：%s（来源 %s）" % (s["order"], s["visual"], s["voiceover"], s["source_id"]) for s in plan["script"]["shots"]]
        lines += ["", "方案已保存；内容制作仍待执行。费用和资料均为合成数据。", ""]
    lines += ["## 实际工具步骤", "", "| 工具 | 最新状态 | 尝试次数 | 成功次数 |", "|---|---|---:|---:|"]
    lines += ["| %s | %s | %s | %s |" % (s["tool"], s["status"], s["attempts"], s["successes"]) for s in result.get("steps", [])]
    if not plan:
        lines += ["", "已保留成果：", "", "```json", json_text(result.get("preserved_results", {})).strip(), "```", ""]
    return "\n".join(lines) + "\n"


def trace_markdown(result):
    lines = ["# 实际运行记录", "", "- 模式：" + result["mode"], "- 状态：" + result["status"],
             "- 说明：" + result["message"], "", "| 步骤 | 工具及参数 | 实际返回摘要 | 行动依据 | 后续动作 |", "|---|---|---|---|---|"]
    trace = result["trace"]
    for index, record in enumerate(trace):
        next_action = trace[index + 1].get("tool", "模型错误") if index + 1 < len(trace) else "结束：" + result["status"]
        if "tool" not in record:
            row = [str(record["step"]), "模型调用错误", record["message"], "—", next_action]
        else:
            summary = {k: v for k, v in record["result"].items() if k in ("ok", "error", "retryable", "count", "total_cost", "total_minutes", "fits_budget", "fits_deadline", "budget_gap", "minutes_gap", "plan_id", "script_id", "status", "message")}
            row = [str(record["step"]), record["tool"] + " " + json.dumps(record["arguments"], ensure_ascii=False), json.dumps(summary, ensure_ascii=False), record["reason"], next_action]
        lines.append("| " + " | ".join(s.replace("|", "/").replace("\n", " ") for s in row) + " |")
    lines += ["", "完整参数和结果见 trace.jsonl；每次模型实际收到的公开观察见 decision-inputs.jsonl。manifest.json 记录源代码、资料与输出哈希；哈希用于完整性校验，不是模型服务方签名。", ""]
    return "\n".join(lines)


def write_result(result, directory):
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    files = {
        "input.json": json_text(result["request"]),
        "catalog.json": json_text(result["catalog"]),
        "output.json": json_text({k: v for k, v in result.items() if k not in ("trace", "decision_inputs", "catalog")}),
        "trace.jsonl": "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in result["trace"]),
        "decision-inputs.jsonl": "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in result.get("decision_inputs", [])),
        "trace.md": trace_markdown(result), "result.md": result_markdown(result),
    }
    for name, body in files.items():
        atomic_write(path / name, body)
    manifest = {"schema_version": 2, **result["run_metadata"], "request_sha256": sha256(result["request"]),
                "files": {name: hashlib.sha256((path / name).read_bytes()).hexdigest() for name in files}}
    atomic_write(path / "manifest.json", json_text(manifest))
    return manifest
