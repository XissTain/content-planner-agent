#!/usr/bin/env python3
"""打包可交付文件；遵守 .gitignore，不复制状态数据库或登录文件。"""
import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / ".runtime/content-planner-submission.zip")
    args = parser.parse_args()
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=str(ROOT), capture_output=True, check=True)
    files = sorted(set(name.decode("utf-8") for name in result.stdout.split(b"\0") if name))
    files = [name for name in files if (ROOT / name).is_file() and (ROOT / name).resolve() != args.out.resolve()
             and not {".git", ".runtime", "__pycache__"}.intersection(Path(name).parts)
             and Path(name).name not in (".env", "auth.json", "id_rsa", "id_ed25519")
             and not name.endswith((".sqlite3", ".pyc"))]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True, text=True)
    manifest = {"question": 2, "generated_at": datetime.now(timezone.utc).isoformat(),
                "local_commit": commit.stdout.strip() if commit.returncode == 0 else None,
                "note": "ZIP 为本地交付快照。正式提交仍需 GitHub URL、远程最终 commit SHA 和评审访问权限。",
                "files": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            archive.write(ROOT / name, "content-planner-agent/" + name)
        archive.writestr("content-planner-agent/PACKAGE-MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"archive": str(args.out.resolve()), "files": len(files),
                      "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
