#!/usr/bin/env python3
"""
Ultra Auto-Git Hook - Auto-execute on file changes

This script should be called automatically whenever files are changed.
It can be integrated with:
- File watchers (watchdog, inotify)
- IDE hooks (VS Code tasks)
- Git hooks (post-commit, post-merge)

For now, this is a simple wrapper that calls ultra_auto_git.py.
"""

import sys
from pathlib import Path
import subprocess

REPO_ROOT = Path("/Users/kevincheng/JarvisV1")
ULTRA_GIT_SCRIPT = REPO_ROOT / "scripts" / "ultra_auto_git.py"

def main():
    """Execute Ultra Auto-Git Mode"""
    try:
        result = subprocess.run(
            [sys.executable, str(ULTRA_GIT_SCRIPT)],
            cwd=REPO_ROOT,
            capture_output=False
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error executing Ultra Auto-Git: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

