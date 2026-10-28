#!/usr/bin/env python3
"""提交前检查：技术证据与 GitHub 正式提交状态分别报告。"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from content_planner.audit import verify_export
from content_planner.evidence import source_identity
from evaluate import CASES


def git(*args):
    result = subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True,
                            timeout=25, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    return result.stdout.strip() if result.returncode == 0 else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--published", action="store_true", help="同时要求有 GitHub 远程、干净 commit 和远程对应版本")
    parser.add_argument("--out", type=Path, default=ROOT / ".runtime/submission-check.json")
    args = parser.parse_args()
    issues, publication_issues, evidence = [], [], {}
    required = ["README.md", "requirements.txt", ".env.example", "src/content_planner/agent.py", "tests/test_agent.py", "data/catalog.json"]
    required += ["docs/" + name for name in ("01-requirements.md", "02-solution.md", "03-evaluation.md", "04-ai-usage.md", "05-retrospective.md")]
    issues += ["缺少必需文件：" + name for name in required if not (ROOT / name).is_file()]
    for file in [ROOT / "README.md", *ROOT.joinpath("docs").glob("*.md")]:
        for ref in re.findall(r"\]\(([^)]+)\)", file.read_text(encoding="utf-8")):
            if "://" not in ref and not ref.startswith("#") and not (file.parent / ref.split("#")[0]).exists():
                issues.append("文档链接失效：%s → %s" % (file.name, ref))
    try:
        test = json.loads((ROOT / "examples/test-summary.json").read_text(encoding="utf-8"))
        if not test["passed"] or test["source_sha256"] != source_identity()["source_sha256"]:
            issues.append("工程测试失败或测试对应的实现已改变。")
    except (OSError, ValueError, KeyError):
        issues.append("没有当前版本的实际工程测试摘要。")
        test = {}
    for mode in ("mock", "codex"):
        selected = {}
        for path in sorted(ROOT.glob("examples/verified*/" + mode + "/evaluation.json")):
            report = json.loads(path.read_text(encoding="utf-8"))
            for case in report["cases"]:
                # 取单个用例实际完成时间，不能让较晚结束的整批报告盖过后做的单项复验。
                finished = []
                for relative in case.get("directories", []):
                    manifest_path = path.parent / relative / "manifest.json"
                    if manifest_path.exists():
                        run = json.loads(manifest_path.read_text(encoding="utf-8"))
                        finished.append(run.get("finished_at", run["started_at"]))
                actual_time = max(finished, default=report["generated_at"])
                previous = selected.get(case["case"])
                if not previous or actual_time > previous[0]:
                    selected[case["case"]] = (actual_time, case, path.parent)
        for name in CASES:
            if name not in selected:
                issues.append(mode + " 缺少用例：" + name)
                continue
            _, case, directory = selected[name]
            if not case["passed"]:
                issues.append(mode + " 最新实际验收未通过：" + name)
            for relative in case["directories"]:
                issues += [mode + "/" + relative + "：" + e for e in verify_export(directory / relative)]
        evidence[mode] = {name: {"passed": item[1]["passed"], "report": str((item[2] / "evaluation.json").relative_to(ROOT))} for name, item in selected.items()}
    # 仅扫描将交付的源文件和证据，不读取机器上的认证目录。
    secret_pattern = re.compile(r"sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----")
    for folder in ("src", "docs", "examples", "data", "tests", "scripts", ".github"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and path.suffix in (".py", ".md", ".json", ".jsonl", ".txt") and secret_pattern.search(path.read_text(encoding="utf-8")):
                issues.append("发现疑似真实凭据：" + str(path.relative_to(ROOT)))
    contributions = json.loads((ROOT / "docs/contributions.json").read_text(encoding="utf-8"))
    if not contributions["candidate_completed"]:
        issues.append("缺少可追溯的候选人实际参与记录。")
    commit, remote, dirty = git("rev-parse", "HEAD"), git("remote", "get-url", "origin"), git("status", "--porcelain")
    if not commit:
        publication_issues.append("尚无最终 commit SHA。")
    if not remote or not re.match(r"(?:https://github\.com/|git@github\.com:)[^/]+/[^/]+", remote):
        publication_issues.append("尚未配置 GitHub 仓库 URL。")
    if dirty:
        publication_issues.append("仍有未提交文件或改动。")
    if args.published and remote and commit:
        remote_head = git("ls-remote", "origin", "HEAD")
        if not remote_head or remote_head.split()[0] != commit:
            publication_issues.append("远程默认分支尚未对应本地最终 commit。")
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "question": 2,
              "technical_ready": not issues, "github_submission_ready": not issues and not publication_issues,
              "tests": test.get("tests"), "issues": issues, "publication_issues": publication_issues,
              "commit": commit, "github_url": remote, "evidence": evidence,
              "candidate_participation_recorded": bool(contributions["candidate_completed"]),
              "candidate_self_run_reported": contributions["candidate_self_run"] is not None,
              "reviewer_access": "若仓库私有，需另行确认评审账号可读；本工具不能代替账号访问确认。"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not issues and (not args.published or not publication_issues) else 2


if __name__ == "__main__":
    raise SystemExit(main())
