#!/usr/bin/env python3
"""
Ultra Auto-Git Mode - Permanent Automatic Git Management System

This script implements a fully automated Git workflow:
- Auto-commit and push on any file changes
- Professional commit messages with What/Why/Impact/Related modules
- Daily version tags (vYYYY.MM.DD)
- Daily release notes (release_notes/release_YYYY_MM_DD.md)
- Automatic conflict resolution
- Never asks for user input

Usage:
    python scripts/ultra_auto_git.py [--daily-only]

When --daily-only is set, only runs daily tasks (tag + release notes).
Otherwise, runs full pipeline: check changes → commit → push → daily tasks.
"""

from __future__ import annotations

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Tuple, Optional

# Project root
REPO_ROOT = Path("/Users/kevincheng/JarvisV1")
RELEASE_NOTES_DIR = REPO_ROOT / "release_notes"
RELEASE_NOTES_DIR.mkdir(exist_ok=True)


def log(message: str, level: str = "INFO") -> None:
    """Output log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [ultra-git-{level}] {message}")


def run_git_command(
    cmd: str, 
    check: bool = True, 
    capture_output: bool = True,
    allow_failure: bool = False
) -> Optional[str]:
    """Execute Git command"""
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
        if allow_failure:
            return e.stdout.strip() if e.stdout else ""
        if capture_output:
            return e.stdout.strip() if e.stdout else ""
        raise


def ensure_gitignore() -> None:
    """Ensure .gitignore contains all required patterns"""
    gitignore_path = REPO_ROOT / ".gitignore"
    
    required_patterns = [
        "__pycache__/",
        ".pytest_cache/",
        ".mypy_cache/",
        "*.log",
        "*.tmp",
        "*.sqlite",
        "*.db",
        ".env",
        "env/",
        "venv/",
        ".venv/",
        "node_modules/",
        "output/",
        "checkpoints/",
        "dist/",
        "build/",
        ".DS_Store",
        "*.egg-info",
    ]
    
    if not gitignore_path.exists():
        gitignore_path.write_text("")
    
    current_content = gitignore_path.read_text()
    missing_patterns = []
    
    for pattern in required_patterns:
        # Check if pattern exists (as exact line or in a comment)
        if pattern not in current_content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        log(f"Adding {len(missing_patterns)} missing patterns to .gitignore")
        with open(gitignore_path, "a") as f:
            f.write("\n# Ultra Auto-Git Mode - Required patterns\n")
            for pattern in missing_patterns:
                f.write(f"{pattern}\n")
        log("Updated .gitignore")


def get_current_branch() -> str:
    """Get current Git branch"""
    branch = run_git_command("git branch --show-current", check=False, allow_failure=True)
    return branch if branch else "main"


def check_git_status() -> bool:
    """Check if there are any changes"""
    status = run_git_command("git status --porcelain", check=False, allow_failure=True)
    return bool(status and status.strip())


def analyze_changes() -> Dict[str, any]:
    """Analyze Git changes and categorize them"""
    status_lines = run_git_command("git status --porcelain", check=False, allow_failure=True)
    
    if not status_lines:
        return {
            "added": [],
            "modified": [],
            "deleted": [],
            "renamed": [],
            "all_files": []
        }
    
    added = []
    modified = []
    deleted = []
    renamed = []
    
    for line in status_lines.split('\n'):
        if not line.strip():
            continue
        
        status_code = line[:2].strip()
        filename = line[3:].strip()
        
        if status_code == "??":
            added.append(filename)
        elif status_code.startswith("D"):
            deleted.append(filename)
        elif status_code.startswith("R"):
            # Renamed: "R  old -> new"
            parts = filename.split(" -> ")
            if len(parts) == 2:
                renamed.append((parts[0], parts[1]))
        elif status_code.startswith("M") or status_code.startswith("A"):
            if filename not in added:
                modified.append(filename)
    
    all_files = added + modified + [f for f, _ in renamed] + deleted
    
    return {
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "renamed": renamed,
        "all_files": all_files
    }


def detect_module_category(files: List[str]) -> List[str]:
    """Detect which J-GOD modules are affected"""
    categories = []
    
    module_patterns = {
        "Path A": ["path_a", "path-a"],
        "Alpha Engine": ["alpha_engine", "alpha-engine"],
        "Risk Model": ["risk", "risk_model", "risk-model"],
        "Optimizer": ["optimizer"],
        "War Room": ["war_room", "war-room"],
        "Knowledge Brain": ["knowledge", "knowledge_brain"],
        "Error Learning": ["error_learning", "error-learning", "learning"],
        "Factor Engine": ["factor_engine", "factor-engine"],
        "Data Feed": ["data_feed", "data-feed"],
    }
    
    for file in files:
        file_lower = file.lower()
        for module, patterns in module_patterns.items():
            if any(pattern in file_lower for pattern in patterns):
                if module not in categories:
                    categories.append(module)
    
    return categories if categories else ["General"]


def generate_commit_message(changes: Dict[str, any]) -> str:
    """Generate professional commit message"""
    added = changes["added"]
    modified = changes["modified"]
    deleted = changes["deleted"]
    renamed = changes["renamed"]
    
    all_files = changes["all_files"]
    modules = detect_module_category(all_files)
    
    # Generate summary line (<= 50 chars)
    summary_parts = []
    
    if added:
        if len(added) == 1:
            summary_parts.append(f"Add {Path(added[0]).name}")
        else:
            summary_parts.append(f"Add {len(added)} files")
    
    if modified:
        if len(modified) == 1:
            summary_parts.append(f"Update {Path(modified[0]).name}")
        else:
            summary_parts.append(f"Update {len(modified)} files")
    
    if deleted:
        summary_parts.append(f"Remove {len(deleted)} files")
    
    if renamed:
        summary_parts.append(f"Rename {len(renamed)} files")
    
    if not summary_parts:
        summary = "Update project files"
    else:
        summary = ", ".join(summary_parts[:2])  # Limit to 2 parts
        if len(summary) > 50:
            summary = summary[:47] + "..."
    
    # Generate detailed message
    details = []
    details.append("What changed:")
    
    if added:
        details.append(f"- Added {len(added)} file(s): {', '.join([Path(f).name for f in added[:5]])}")
        if len(added) > 5:
            details.append(f"  ... and {len(added) - 5} more")
    
    if modified:
        details.append(f"- Modified {len(modified)} file(s): {', '.join([Path(f).name for f in modified[:5]])}")
        if len(modified) > 5:
            details.append(f"  ... and {len(modified) - 5} more")
    
    if deleted:
        details.append(f"- Deleted {len(deleted)} file(s): {', '.join([Path(f).name for f in deleted[:5]])}")
    
    if renamed:
        details.append(f"- Renamed {len(renamed)} file(s)")
        for old, new in renamed[:3]:
            details.append(f"  {Path(old).name} -> {Path(new).name}")
    
    details.append("")
    details.append("Why it was changed:")
    details.append("- Automated commit from Ultra Auto-Git Mode")
    details.append("- Code changes detected and committed automatically")
    
    details.append("")
    details.append("Impact on the system:")
    if "Path A" in modules:
        details.append("- Path A: Backtest pipeline or data loading updates")
    if "Alpha Engine" in modules:
        details.append("- Alpha Engine: Signal generation or factor computation changes")
    if "Risk Model" in modules:
        details.append("- Risk Model: Risk estimation or covariance updates")
    if "Optimizer" in modules:
        details.append("- Optimizer: Portfolio optimization logic updates")
    if "War Room" in modules:
        details.append("- War Room: UI or backend engine updates")
    if "Knowledge Brain" in modules:
        details.append("- Knowledge Brain: Knowledge base or query system updates")
    if "Error Learning" in modules:
        details.append("- Error Learning: Error analysis or learning engine updates")
    if not any(m in modules for m in ["Path A", "Alpha Engine", "Risk Model", "Optimizer", "War Room", "Knowledge Brain", "Error Learning"]):
        details.append("- General: Project-wide updates or infrastructure changes")
    
    details.append("")
    details.append(f"Related modules: {', '.join(modules)}")
    
    full_message = f"{summary}\n\nDetails:\n\n" + "\n".join(details)
    return full_message


def stage_all_changes() -> bool:
    """Stage all changes (except .gitignore patterns)"""
    log("Staging all changes...")
    run_git_command("git add -A", check=True, capture_output=False)
    
    # Check if there are staged changes
    staged = run_git_command("git diff --cached --stat", check=False, allow_failure=True)
    return bool(staged and staged.strip())


def commit_changes(message: str) -> bool:
    """Commit staged changes"""
    log("Committing changes...")
    try:
        # Escape message for shell
        escaped_message = message.replace('"', '\\"').replace('$', '\\$')
        run_git_command(
            f'git commit -m "{escaped_message}"',
            check=True,
            capture_output=False
        )
        log("Commit successful")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Commit failed: {e}", level="ERROR")
        return False


def handle_push_conflict() -> bool:
    """Handle push conflicts automatically"""
    log("Push conflict detected, attempting automatic resolution...")
    
    try:
        # Pull with rebase
        log("Executing: git pull --rebase")
        run_git_command("git pull --rebase", check=True, capture_output=False)
        log("Rebase completed successfully")
        
        # Push again
        log("Pushing after rebase...")
        run_git_command("git push origin main", check=True, capture_output=False)
        log("Push successful after rebase")
        return True
    except subprocess.CalledProcessError as e:
        # Check for merge conflicts
        status = run_git_command("git status", check=False, allow_failure=True)
        
        if status and ("conflict" in status.lower() or "CONFLICT" in status):
            log("ERROR: Merge conflict detected that cannot be auto-resolved", level="ERROR")
            log("Attempting to resolve by keeping local version...", level="WARN")
            
            # Try to resolve by keeping local version
            try:
                # Abort rebase and try merge strategy
                run_git_command("git rebase --abort", check=False, allow_failure=True)
                run_git_command("git pull --no-rebase -X ours", check=False, allow_failure=True)
                run_git_command("git push origin main", check=True, capture_output=False)
                log("Resolved conflict by keeping local version")
                return True
            except:
                log("ERROR: Could not auto-resolve conflict. Manual intervention required.", level="ERROR")
                return False
        
        # Other errors
        log(f"Push failed: {e}", level="ERROR")
        return False


def push_changes() -> bool:
    """Push changes to remote"""
    branch = get_current_branch()
    log(f"Pushing to origin/{branch}...")
    
    try:
        run_git_command(f"git push origin {branch}", check=True, capture_output=False)
        log("Push successful")
        return True
    except subprocess.CalledProcessError:
        # Try to handle conflict
        return handle_push_conflict()


def create_daily_tag() -> None:
    """Create daily version tag (vYYYY.MM.DD)"""
    today = datetime.now()
    tag_name = f"v{today.strftime('%Y.%m.%d')}"
    
    # Check if tag already exists locally
    existing_tags = run_git_command("git tag -l", check=False, allow_failure=True)
    if existing_tags and tag_name in existing_tags:
        log(f"Daily tag {tag_name} already exists locally, skipping")
        return
    
    # Check if tag exists on remote
    run_git_command("git fetch --tags", check=False, allow_failure=True)
    remote_tags = run_git_command("git ls-remote --tags origin", check=False, allow_failure=True)
    if remote_tags and tag_name in remote_tags:
        log(f"Daily tag {tag_name} already exists on remote, skipping")
        return
    
    # Create and push tag
    try:
        run_git_command(f"git tag {tag_name}", check=True, capture_output=False)
        log(f"Created daily tag: {tag_name}")
        
        run_git_command(f"git push origin {tag_name}", check=True, capture_output=False)
        log(f"Pushed daily tag: {tag_name}")
    except subprocess.CalledProcessError as e:
        log(f"Warning: Failed to create/push tag {tag_name}: {e}", level="WARN")


def get_today_commits() -> List[Dict[str, str]]:
    """Get all commits from today"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get commits from today
    log_output = run_git_command(
        f'git log --since="{today} 00:00:00" --until="{today} 23:59:59" --pretty=format:"%H|%s|%an|%ad" --date=iso',
        check=False,
        allow_failure=True
    )
    
    commits = []
    if log_output:
        for line in log_output.split('\n'):
            if not line.strip():
                continue
            parts = line.split('|')
            if len(parts) >= 2:
                commits.append({
                    "hash": parts[0][:8],
                    "message": parts[1],
                    "author": parts[2] if len(parts) > 2 else "Unknown",
                    "date": parts[3] if len(parts) > 3 else today
                })
    
    return commits


def get_code_stats() -> Tuple[int, int]:
    """Get today's code statistics (added/deleted lines)"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get diff stats for today's commits
    stats_output = run_git_command(
        f'git log --since="{today} 00:00:00" --until="{today} 23:59:59" --pretty=format:"%H" --numstat',
        check=False,
        allow_failure=True
    )
    
    added = 0
    deleted = 0
    
    if stats_output:
        for line in stats_output.split('\n'):
            if not line.strip() or '|' in line or len(line) == 40:  # Skip commit hashes
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    added += int(parts[0]) if parts[0] != '-' else 0
                    deleted += int(parts[1]) if parts[1] != '-' else 0
                except ValueError:
                    continue
    
    return added, deleted


def generate_daily_release_notes() -> None:
    """Generate daily release notes"""
    today = datetime.now()
    date_str = today.strftime("%Y_%m_%d")
    tag_name = f"v{today.strftime('%Y.%m.%d')}"
    
    notes_path = RELEASE_NOTES_DIR / f"release_{date_str}.md"
    
    # Check if already generated today
    if notes_path.exists():
        log(f"Release notes for {date_str} already exist, skipping")
        return
    
    log(f"Generating daily release notes: release_{date_str}.md")
    
    commits = get_today_commits()
    added_lines, deleted_lines = get_code_stats()
    
    # Analyze today's changes
    today_files = set()
    modules_worked = set()
    
    for commit in commits:
        # Get files changed in this commit
        files_output = run_git_command(
            f'git show --name-status --pretty=format: {commit["hash"]}',
            check=False,
            allow_failure=True
        )
        if files_output:
            for line in files_output.split('\n'):
                if line.strip() and not line.startswith('commit'):
                    parts = line.split()
                    if len(parts) >= 2:
                        filename = parts[-1]
                        today_files.add(filename)
                        modules_worked.update(detect_module_category([filename]))
    
    # Generate release notes content
    content = []
    content.append(f"# J-GOD Daily Release Notes - {today.strftime('%Y-%m-%d')}")
    content.append("")
    content.append(f"**Version Tag:** `{tag_name}`")
    content.append(f"**Date:** {today.strftime('%Y-%m-%d %A')}")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## 📊 Today's Summary")
    content.append("")
    content.append(f"- **Total Commits:** {len(commits)}")
    content.append(f"- **Lines Added:** +{added_lines}")
    content.append(f"- **Lines Deleted:** -{deleted_lines}")
    content.append(f"- **Net Change:** {added_lines - deleted_lines:+d} lines")
    content.append(f"- **Files Changed:** {len(today_files)}")
    content.append("")
    
    if commits:
        content.append("## 📝 Today's Commits")
        content.append("")
        for i, commit in enumerate(commits[:20], 1):  # Limit to 20 commits
            content.append(f"{i}. `{commit['hash']}` - {commit['message']}")
        if len(commits) > 20:
            content.append(f"\n... and {len(commits) - 20} more commits")
        content.append("")
    
    if modules_worked:
        content.append("## 🔧 Modules Worked On")
        content.append("")
        for module in sorted(modules_worked):
            content.append(f"- {module}")
        content.append("")
    
    if today_files:
        content.append("## 📁 Files Changed Today")
        content.append("")
        # Group by directory
        by_dir: Dict[str, List[str]] = {}
        for file in sorted(today_files):
            dir_path = str(Path(file).parent)
            if dir_path == ".":
                dir_path = "root"
            if dir_path not in by_dir:
                by_dir[dir_path] = []
            by_dir[dir_path].append(Path(file).name)
        
        for dir_path in sorted(by_dir.keys()):
            content.append(f"### {dir_path}/")
            for filename in by_dir[dir_path][:10]:  # Limit to 10 files per directory
                content.append(f"- `{filename}`")
            if len(by_dir[dir_path]) > 10:
                content.append(f"  ... and {len(by_dir[dir_path]) - 10} more files")
            content.append("")
    
    content.append("## 🎯 Major Updates")
    content.append("")
    if not commits:
        content.append("- No commits today (quiet day)")
    else:
        # Extract major updates from commit messages
        major_updates = []
        for commit in commits:
            msg = commit['message'].lower()
            if any(keyword in msg for keyword in ['complete', 'finish', 'implement', 'add', 'create']):
                major_updates.append(commit['message'])
        
        if major_updates:
            for update in major_updates[:5]:
                content.append(f"- {update}")
        else:
            content.append("- Various improvements and bug fixes")
    content.append("")
    
    content.append("## 📋 Next Steps / TODO")
    content.append("")
    content.append("- Continue development on active modules")
    content.append("- Monitor system performance and stability")
    content.append("- Review and integrate feedback")
    content.append("")
    
    content.append("---")
    content.append("")
    content.append(f"*Generated automatically by Ultra Auto-Git Mode at {today.strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Write release notes
    notes_path.write_text("\n".join(content))
    log(f"Generated release notes: {notes_path}")
    
    # Stage and commit release notes
    run_git_command("git add release_notes/", check=False, allow_failure=True)
    if check_git_status():
        commit_msg = f"Add daily release notes for {today.strftime('%Y-%m-%d')}"
        run_git_command(
            f'git commit -m "{commit_msg}"',
            check=False,
            allow_failure=True
        )
        push_changes()


def run_daily_tasks() -> None:
    """Run daily tasks (tag + release notes)"""
    log("Running daily tasks...")
    create_daily_tag()
    generate_daily_release_notes()
    log("Daily tasks completed")


def main() -> None:
    """Main workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ultra Auto-Git Mode")
    parser.add_argument(
        "--daily-only",
        action="store_true",
        help="Only run daily tasks (tag + release notes)"
    )
    args = parser.parse_args()
    
    log("=" * 60)
    log("Ultra Auto-Git Mode - Starting")
    log("=" * 60)
    
    # Ensure we're in the right directory
    if not REPO_ROOT.exists():
        log(f"ERROR: Repository root not found: {REPO_ROOT}", level="ERROR")
        sys.exit(1)
    
    # Ensure .gitignore is up to date
    ensure_gitignore()
    
    # If daily-only mode, just run daily tasks
    if args.daily_only:
        run_daily_tasks()
        log("=" * 60)
        log("Ultra Auto-Git Mode - Daily tasks completed")
        log("=" * 60)
        return
    
    # Check current branch
    branch = get_current_branch()
    log(f"Current branch: {branch}")
    
    # Check for changes
    if not check_git_status():
        log("No changes detected, running daily tasks only...")
        run_daily_tasks()
        log("=" * 60)
        log("Ultra Auto-Git Mode - Completed (no changes)")
        log("=" * 60)
        return
    
    log("Changes detected, proceeding with full pipeline...")
    
    # Analyze changes
    changes = analyze_changes()
    if not changes["all_files"]:
        log("No meaningful changes to commit, running daily tasks only...")
        run_daily_tasks()
        return
    
    # Generate commit message
    commit_message = generate_commit_message(changes)
    log("Generated commit message")
    
    # Stage all changes
    if not stage_all_changes():
        log("No staged changes (all changes are in .gitignore), running daily tasks only...")
        run_daily_tasks()
        return
    
    # Commit
    if not commit_changes(commit_message):
        log("Commit failed, running daily tasks only...")
        run_daily_tasks()
        return
    
    # Push
    if not push_changes():
        log("Push failed, but continuing with daily tasks...", level="WARN")
    
    # Run daily tasks
    run_daily_tasks()
    
    log("=" * 60)
    log("Ultra Auto-Git Mode - Completed successfully")
    log("=" * 60)


if __name__ == "__main__":
    main()

