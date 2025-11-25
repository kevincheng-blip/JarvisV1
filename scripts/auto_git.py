#!/usr/bin/env python3
"""
Full Auto Git Mode v2 for JarvisV1
自動執行 Git 流程：檢查變更 → 產生摘要 → commit → push → 更新 Release Notes → 建立每日 tag
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
import re

# 專案根目錄
REPO_ROOT = Path("/Users/kevincheng/JarvisV1")
RELEASE_NOTES_PATH = REPO_ROOT / "docs" / "JGOD_RELEASE_NOTES.md"


def log(message):
    """輸出日誌訊息"""
    print(f"[auto-git] {message}")


def run_git_command(cmd, check=True, capture_output=True):
    """執行 Git 指令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=REPO_ROOT,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        if capture_output:
            return e.stdout.strip() if e.stdout else ""
        raise


def get_current_branch():
    """取得當前分支"""
    branch = run_git_command("git branch --show-current", check=False)
    return branch if branch else "main"


def check_git_status():
    """檢查 Git 狀態，回傳是否有變更"""
    status = run_git_command("git status --porcelain", check=False)
    return bool(status.strip())


def get_git_diff_summary():
    """分析 git diff 產生英文摘要"""
    # 取得 staged 和 unstaged 的變更
    diff_staged = run_git_command("git diff --cached --stat", check=False)
    diff_unstaged = run_git_command("git diff --stat", check=False)
    
    # 取得新增/刪除/修改的檔案列表
    status_lines = run_git_command("git status --porcelain", check=False)
    
    if not (diff_staged or diff_unstaged or status_lines):
        return None
    
    # 分析變更類型
    added_files = []
    modified_files = []
    deleted_files = []
    
    for line in status_lines.split('\n'):
        if not line.strip():
            continue
        status_code = line[:2]
        filename = line[3:].strip()
        
        if status_code.startswith('??'):
            added_files.append(filename)
        elif status_code.startswith('D'):
            deleted_files.append(filename)
        elif status_code.startswith('M') or status_code.startswith('A'):
            if filename not in added_files:
                modified_files.append(filename)
    
    # 產生摘要
    summary_parts = []
    
    # 分析主要變更領域
    if any('war_room' in f for f in (added_files + modified_files)):
        if any('provider' in f for f in (added_files + modified_files)):
            summary_parts.append("Update war room AI provider")
        elif any('component' in f for f in (added_files + modified_files)):
            summary_parts.append("Refactor war room UI components")
        elif any('core' in f for f in (added_files + modified_files)):
            summary_parts.append("Improve war room core engine")
        else:
            summary_parts.append("Enhance war room functionality")
    
    if any('config' in f for f in (added_files + modified_files)):
        summary_parts.append("Update configuration")
    
    if any('api_client' in f for f in (added_files + modified_files)):
        summary_parts.append("Update API client")
    
    if any('script' in f or 'auto_git' in f for f in (added_files + modified_files)):
        summary_parts.append("Add auto Git pipeline")
    
    if deleted_files:
        summary_parts.append("Remove obsolete files")
    
    # 如果沒有特定模式，使用通用描述
    if not summary_parts:
        if added_files:
            summary_parts.append("Add new features")
        elif modified_files:
            summary_parts.append("Update codebase")
        else:
            summary_parts.append("Maintain codebase")
    
    # 組合摘要（限制在 20 字以內）
    summary = " ".join(summary_parts[:2])  # 最多取前兩個部分
    
    # 確保不超過 20 字
    words = summary.split()
    if len(words) > 4:
        summary = " ".join(words[:4])
    
    # 使用現在式動詞開頭
    if not any(summary.startswith(v) for v in ['Add', 'Update', 'Fix', 'Remove', 'Improve', 'Refactor', 'Enhance']):
        summary = f"Update {summary.lower()}"
    
    return summary


def update_release_notes(summary):
    """更新 Release Notes"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 讀取現有內容
    if RELEASE_NOTES_PATH.exists():
        content = RELEASE_NOTES_PATH.read_text(encoding='utf-8')
    else:
        content = "# J-GOD Release Notes\n\n"
    
    # 檢查今天是否已有區塊
    date_header = f"## {today}"
    
    if date_header in content:
        # 在同一天的區塊中追加
        # 找到日期標題後，在下一行插入新的 bullet
        pattern = f"(## {today}\\n)"
        replacement = f"\\1- auto-commit: {summary}\n"
        content = re.sub(pattern, replacement, content)
    else:
        # 建立新的日期區塊（插入在標題後、第一個日期區塊前）
        if "## " in content:
            # 插入在現有日期區塊之前
            pattern = "(# J-GOD Release Notes\\n\\n)"
            replacement = f"\\1{date_header}\n- auto-commit: {summary}\n\n"
            content = re.sub(pattern, replacement, content)
        else:
            # 如果沒有其他日期區塊，直接追加
            content += f"\n{date_header}\n- auto-commit: {summary}\n"
    
    # 寫回檔案
    RELEASE_NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
    RELEASE_NOTES_PATH.write_text(content, encoding='utf-8')
    log(f"Updated docs/JGOD_RELEASE_NOTES.md")


def create_daily_tag():
    """建立每日 tag（如果今天還沒有）"""
    today_str = datetime.now().strftime("%Y%m%d")
    tag_name = f"jgod-daily-{today_str}"
    
    # 檢查本地是否已存在
    existing_tags = run_git_command("git tag -l", check=False)
    if tag_name in existing_tags:
        log(f"Daily tag {tag_name} already exists locally, skipping")
        return
    
    # 檢查遠端是否已存在
    run_git_command("git fetch --tags", check=False)
    remote_tags = run_git_command("git ls-remote --tags origin", check=False)
    if tag_name in remote_tags:
        log(f"Daily tag {tag_name} already exists on remote, skipping")
        return
    
    # 建立並推送 tag
    try:
        run_git_command(f"git tag {tag_name}", check=True, capture_output=False)
        log(f"Created daily tag: {tag_name}")
        
        run_git_command(f"git push origin {tag_name}", check=True, capture_output=False)
        log(f"Pushed daily tag: {tag_name}")
    except subprocess.CalledProcessError as e:
        log(f"Warning: Failed to create/push tag {tag_name}: {e}")


def handle_push_conflict():
    """處理 Push 衝突"""
    log("Push conflict detected, attempting rebase...")
    
    try:
        # 嘗試 rebase
        run_git_command("git pull --rebase", check=True, capture_output=False)
        log("Rebase completed successfully")
        
        # 再次嘗試 push
        run_git_command("git push", check=True, capture_output=False)
        log("Push successful after rebase")
        return True
    except subprocess.CalledProcessError as e:
        # 檢查是否有 conflict
        status = run_git_command("git status", check=False)
        
        if "conflict" in status.lower() or "CONFLICT" in status:
            log("ERROR: Merge conflict detected that cannot be auto-resolved")
            log("Please resolve conflicts manually:")
            
            # 找出衝突檔案
            conflict_files = []
            for line in status.split('\n'):
                if 'both modified' in line or 'both added' in line:
                    # 提取檔案名稱
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part in ['modified:', 'added:'] and i + 1 < len(parts):
                            conflict_files.append(parts[i + 1])
                            break
            
            if conflict_files:
                log("Conflict files:")
                for f in conflict_files:
                    log(f"  - {f}")
            else:
                log("  (Check 'git status' for details)")
            
            return False
        else:
            # 其他錯誤，重新拋出
            raise


def main():
    """主流程"""
    log("Starting Full Auto Git Mode v2")
    
    # 確認在正確的目錄
    if not REPO_ROOT.exists():
        log(f"ERROR: Repository root not found: {REPO_ROOT}")
        sys.exit(1)
    
    # 確認當前分支
    branch = get_current_branch()
    log(f"Current branch: {branch}")
    
    # 檢查是否有變更
    if not check_git_status():
        log("No changes detected, skipping auto Git workflow")
        return
    
    log("Changes detected, proceeding with auto Git workflow")
    
    # 產生摘要
    summary = get_git_diff_summary()
    if not summary:
        log("No meaningful changes to commit, skipping")
        return
    
    log(f"Generated summary: {summary}")
    
    # 更新 Release Notes
    update_release_notes(summary)
    
    # Stage 所有變更
    log("Staging all changes...")
    run_git_command("git add -A", check=True, capture_output=False)
    
    # 檢查是否有 staged 變更
    staged_status = run_git_command("git diff --cached --stat", check=False)
    if not staged_status.strip():
        log("No staged changes (all changes are in .gitignore), skipping commit")
        return
    
    # Commit
    commit_message = f"auto-commit: {summary}"
    log(f"Committing: {commit_message}")
    try:
        run_git_command(f'git commit -m "{commit_message}"', check=True, capture_output=False)
        log("Commit successful")
    except subprocess.CalledProcessError:
        log("Commit failed (no staged changes), skipping")
        return
    
    # Push
    log("Pushing to remote...")
    try:
        run_git_command("git push", check=True, capture_output=False)
        log("Push successful")
    except subprocess.CalledProcessError:
        # 嘗試處理衝突
        if not handle_push_conflict():
            log("ERROR: Push failed due to conflicts, manual intervention required")
            sys.exit(1)
    
    # 建立每日 tag
    create_daily_tag()
    
    log("Full Auto Git Mode v2 completed successfully")


if __name__ == "__main__":
    main()

