#!/usr/bin/env python3
"""运行测试并把真实测试输出保存到 examples/。"""
import io
import json
import platform
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from content_planner.evidence import source_identity


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    output = stream.getvalue()
    print(output, end="")
    (ROOT / "examples/test-results.txt").write_text(output, encoding="utf-8")
    metadata = {"generated_at": datetime.now(timezone.utc).isoformat(), "tests": result.testsRun,
                "python": platform.python_version(), **source_identity(),
                "failures": len(result.failures), "errors": len(result.errors), "passed": result.wasSuccessful(),
                "command": "python3 scripts/test_report.py", "scope": "工程单元测试；模型为测试替身"}
    (ROOT / "examples/test-summary.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
