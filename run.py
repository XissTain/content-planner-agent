#!/usr/bin/env python3
"""无需安装依赖的本地入口。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from content_planner.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
