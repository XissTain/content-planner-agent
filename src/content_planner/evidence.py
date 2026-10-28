"""可审计的公开观察，不存储 CLI 凭据或模型内部推理。"""
import copy
import hashlib
import json
from pathlib import Path


def sha256(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def visible_state(state):
    keys = ("request", "planning_clock", "clock_mode", "assets", "estimates", "scripts", "saved_plan", "search_count", "status", "message", "call_offset", "remaining_steps")
    result = {k: copy.deepcopy(state[k]) for k in keys if k in state}
    result["calls"] = [{k: copy.deepcopy(call[k]) for k in ("step", "tool", "arguments", "reason", "result") if k in call} for call in state["calls"]]
    return result


def source_identity():
    root = Path(__file__).resolve().parents[2]
    files = sorted([root / "run.py", *root.joinpath("src").rglob("*.py")])
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    return {"source_sha256": sha256(hashes), "source_files": hashes}
