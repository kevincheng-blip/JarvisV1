#!/bin/bash
"""
Setup script for Ultra Auto-Git Mode daily tasks.

This script sets up a cron job to run daily tasks at 23:59 every day.

Usage:
    bash scripts/setup_ultra_git_cron.sh

The cron job will:
- Create daily version tag (vYYYY.MM.DD)
- Generate daily release notes (release_notes/release_YYYY_MM_DD.md)
"""

REPO_ROOT="/Users/kevincheng/JarvisV1"
SCRIPT_PATH="$REPO_ROOT/scripts/ultra_auto_git.py"
PYTHON_PATH=$(which python3)

# Check if cron job already exists
CRON_CMD="59 23 * * * cd $REPO_ROOT && $PYTHON_PATH $SCRIPT_PATH --daily-only >> $REPO_ROOT/logs/ultra_git_daily.log 2>&1"

# Check existing crontab
if crontab -l 2>/dev/null | grep -q "ultra_auto_git.py --daily-only"; then
    echo "✅ Ultra Auto-Git daily cron job already exists"
    crontab -l | grep "ultra_auto_git.py"
else
    echo "📅 Setting up Ultra Auto-Git daily cron job..."
    
    # Create logs directory if it doesn't exist
    mkdir -p "$REPO_ROOT/logs"
    
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    
    echo "✅ Ultra Auto-Git daily cron job installed"
    echo "   Schedule: Daily at 23:59"
    echo "   Command: $CRON_CMD"
    echo ""
    echo "To view cron jobs: crontab -l"
    echo "To remove cron job: crontab -e (then delete the line)"
fi

