#!/usr/bin/env python
"""
J-GOD Git AutoSync System (終極版)

自動偵測改動、add、commit、push 一鍵完成。

Usage:
    python scripts/git_auto_sync.py
    python scripts/git_auto_sync.py --msg "Path E stable"
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from typing import Optional


def parse_args() -> argparse.Namespace:
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="J-GOD Git AutoSync System - 自動 git add/commit/push"
    )
    parser.add_argument(
        "--msg",
        type=str,
        default="",
        help="額外的 commit message（可選）",
    )
    return parser.parse_args()


def run_git_command(cmd: list[str], check: bool = True) -> tuple[int, str, str]:
    """
    執行 git 命令
    
    Args:
        cmd: git 命令列表，例如 ['git', 'status', '--porcelain']
        check: 是否在失敗時拋出異常
    
    Returns:
        (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout.strip() if hasattr(e, 'stdout') else "", e.stderr.strip() if hasattr(e, 'stderr') else ""


def has_changes() -> bool:
    """檢查是否有未提交的變更"""
    returncode, stdout, stderr = run_git_command(["git", "status", "--porcelain"], check=False)
    if returncode != 0:
        print(f"[AutoSync][ERROR] git status failed: {stderr}")
        sys.exit(1)
    return bool(stdout)


def generate_commit_message(msg: Optional[str] = None) -> str:
    """
    產生 commit message
    
    格式：chore: auto-sync {YYYY-MM-DD HH:MM:SS} +0800 - {msg}
    """
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %z")
    if not timestamp.endswith("+0800"):
        # 如果沒有時區，手動加上
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S") + " +0800"
    
    base_msg = f"chore: auto-sync {timestamp}"
    
    if msg:
        return f"{base_msg} - {msg}"
    return base_msg


def git_add() -> bool:
    """執行 git add ."""
    print("[AutoSync] Running: git add .")
    returncode, stdout, stderr = run_git_command(["git", "add", "."], check=False)
    if returncode != 0:
        print(f"[AutoSync][ERROR] git add failed:")
        print(f"  stdout: {stdout}")
        print(f"  stderr: {stderr}")
        return False
    return True


def git_commit(message: str) -> bool:
    """執行 git commit"""
    print(f"[AutoSync] Running: git commit -m \"{message}\"")
    returncode, stdout, stderr = run_git_command(
        ["git", "commit", "-m", message],
        check=False
    )
    if returncode != 0:
        print(f"[AutoSync][ERROR] git commit failed:")
        print(f"  stdout: {stdout}")
        print(f"  stderr: {stderr}")
        return False
    print(f"[AutoSync] Commit successful: {message}")
    return True


def git_push() -> bool:
    """執行 git push"""
    print("[AutoSync] Running: git push")
    returncode, stdout, stderr = run_git_command(["git", "push"], check=False)
    if returncode != 0:
        print(f"[AutoSync][ERROR] git push failed:")
        print(f"  stdout: {stdout}")
        print(f"  stderr: {stderr}")
        return False
    print("[AutoSync] Push successful")
    return True


def main():
    """主函式"""
    args = parse_args()
    
    # 1. 檢查是否有變更
    print("[AutoSync] Checking for changes...")
    if not has_changes():
        print("[AutoSync] No changes to commit.")
        sys.exit(0)
    
    # 2. git add
    if not git_add():
        sys.exit(1)
    
    # 3. 產生 commit message
    commit_msg = generate_commit_message(args.msg if args.msg else None)
    
    # 4. git commit
    if not git_commit(commit_msg):
        sys.exit(1)
    
    # 5. git push
    if not git_push():
        sys.exit(1)
    
    print("[AutoSync] ✅ All done!")


if __name__ == "__main__":
    main()

