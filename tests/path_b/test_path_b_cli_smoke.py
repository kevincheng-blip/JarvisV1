"""
Smoke Test for Path B CLI Script

This test verifies that the Path B CLI script can be executed successfully
and generates the expected output files.

Reference: J-GOD Path B Engine Step B4
"""

from __future__ import annotations

import pytest
import subprocess
import sys
from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestPathBCLISmoke:
    """Smoke Test for Path B CLI Script"""
    
    def test_path_b_cli_execution(self):
        """
        Test that Path B CLI script can be executed successfully
        and generates expected output files.
        """
        experiment_name = "path_b_smoke_demo"
        output_dir = PROJECT_ROOT / "output" / "path_b" / experiment_name
        
        # 清理之前的輸出（如果存在）
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir)
        
        # 建立 CLI 命令
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_jgod_path_b.py"),
            "--name", experiment_name,
            "--start-date", "2024-01-01",
            "--end-date", "2024-06-30",
            "--rebalance-frequency", "M",
            "--universe", "2330.TW,2317.TW",
            "--data-source", "mock",
            "--mode", "basic",
            "--walkforward-window", "6m",
            "--walkforward-step", "3m",
        ]
        
        # 執行命令
        env = {"PYTHONPATH": str(PROJECT_ROOT)}
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        
        # 檢查 exit code
        assert result.returncode == 0, \
            f"CLI script failed with exit code {result.returncode}\n" \
            f"STDOUT:\n{result.stdout}\n" \
            f"STDERR:\n{result.stderr}"
        
        # 檢查輸出目錄是否存在
        assert output_dir.exists(), \
            f"Output directory {output_dir} does not exist"
        
        # 檢查必要檔案是否存在
        expected_files = [
            "windows_summary.csv",
            "governance_summary.json",
            "path_b_summary.json",
            "path_b_report.md",
        ]
        
        for filename in expected_files:
            filepath = output_dir / filename
            assert filepath.exists(), \
                f"Expected file {filepath} does not exist"
            assert filepath.stat().st_size > 0, \
                f"File {filepath} is empty"
        
        # 驗證 JSON 檔案格式
        governance_summary_path = output_dir / "governance_summary.json"
        with open(governance_summary_path, "r", encoding="utf-8") as f:
            governance_data = json.load(f)
            assert isinstance(governance_data, dict), \
                "governance_summary.json should be a JSON object"
            assert "total_windows" in governance_data, \
                "governance_summary.json should contain 'total_windows'"
        
        path_b_summary_path = output_dir / "path_b_summary.json"
        with open(path_b_summary_path, "r", encoding="utf-8") as f:
            summary_data = json.load(f)
            assert isinstance(summary_data, dict), \
                "path_b_summary.json should be a JSON object"
            assert "experiment_name" in summary_data, \
                "path_b_summary.json should contain 'experiment_name'"
            assert "num_windows" in summary_data, \
                "path_b_summary.json should contain 'num_windows'"
        
        # 驗證 CSV 檔案（檢查是否有 header）
        windows_summary_path = output_dir / "windows_summary.csv"
        with open(windows_summary_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) > 0, \
                "windows_summary.csv should have at least one line (header)"
            # 檢查是否有 header
            header = lines[0].strip()
            assert "window_id" in header, \
                "windows_summary.csv should have 'window_id' column"
            assert "sharpe" in header, \
                "windows_summary.csv should have 'sharpe' column"
        
        # 驗證 Markdown 報告
        report_path = output_dir / "path_b_report.md"
        with open(report_path, "r", encoding="utf-8") as f:
            report_content = f.read()
            assert len(report_content) > 0, \
                "path_b_report.md should not be empty"
            assert "Path B Walk-Forward Analysis Report" in report_content, \
                "path_b_report.md should contain report title"

