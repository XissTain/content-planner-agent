import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .agent import Agent, write_result
from .models import CodexModel, MockModel, ModelError
from .store import Store


def main(argv=None):
    parser = argparse.ArgumentParser(description="内容任务规划 Agent（题 2）")
    parser.add_argument("input", type=Path, help="请求 JSON 路径")
    parser.add_argument("--mode", choices=["mock", "codex"], default="mock")
    parser.add_argument("--db", default=".runtime/state.sqlite3")
    parser.add_argument("--out", default=".runtime/latest")
    parser.add_argument("--catalog", type=Path, help="可替换的合成素材与成本表")
    parser.add_argument("--max-steps", type=int, default=12, help="本次执行上限；相同请求可续跑")
    parser.add_argument("--model", help="可选 GPT 模型名；默认沿用 Codex CLI 配置")
    parser.add_argument("--model-timeout", type=int, default=90)
    parser.add_argument("--reasoning-effort", choices=["low", "medium", "high"], default="low")
    parser.add_argument("--fail", action="append", default=[], metavar="TOOL:COUNT", help="注入工具失败，只在请求首次创建时生效")
    parser.add_argument("--fail-permanent", action="append", default=[], metavar="TOOL@SERVICE:COUNT", help="注入不可原样重试的服务故障，如 generate_script@premium:10")
    args = parser.parse_args(argv)
    store = None
    try:
        def reject_constant(value):
            raise ValueError("JSON 不接受 " + value)
        request = json.loads(args.input.read_text(encoding="utf-8"), parse_constant=reject_constant)
        faults = {}
        for retryable, failures in ((True, args.fail), (False, args.fail_permanent)):
            for failure in failures:
                target, count = failure.split(":")
                tool_name, _, service = target.partition("@")
                if tool_name not in ("search_assets", "estimate_plan", "generate_script", "save_plan") or int(count) < 1:
                    raise ValueError("故障配置须为已知业务工具名:正整数。")
                if service and (tool_name != "generate_script" or service not in ("premium", "standard", "template")):
                    raise ValueError("按服务注入仅支持 generate_script@premium|standard|template。")
                if target in faults:
                    raise ValueError("同一故障目标不能重复配置。")
                faults[target] = {"count": int(count), "retryable": retryable}
        model = MockModel() if args.mode == "mock" else CodexModel(model=args.model, timeout=args.model_timeout, reasoning_effort=args.reasoning_effort)
        store = Store(args.db)
        result = Agent(store, model, args.catalog).run(request, args.max_steps, faults)
        write_result(result, args.out)
        print(json.dumps({k: result[k] for k in ("status", "message", "stop_reason", "mode", "real_model_used", "steps_this_run")}, ensure_ascii=False, indent=2))
        if result["plan"]:
            estimate = result["plan"]["estimate"]
            print("方案费用：%s；预计时长：%s 分钟；保存状态：saved" % (estimate["total_cost"], estimate["total_minutes"]))
        print("运行记录：" + str(Path(args.out).resolve()))
        return 0 if result["status"] == "completed" else 2
    except (ValueError, OSError, ModelError, sqlite3.Error) as exc:
        print("错误：" + str(exc), file=sys.stderr)
        return 1
    finally:
        if store:
            store.close()
