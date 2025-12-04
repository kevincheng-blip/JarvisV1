"""
Path C v1 - Validation Lab / Scenario Engine

This module provides the Path C Engine for executing batch scenario validation
by calling Path B Engine multiple times with different configurations.

Path C is responsible for:
- Executing multiple scenarios in batch
- Ranking scenarios based on performance metrics
- Generating comprehensive reports (CSV, JSON, Markdown)
- Identifying best-performing scenarios for production use

Reference:
- spec/JGOD_PathCEngine_Spec.md
- docs/JGOD_PATH_C_STANDARD_v1.md
"""

from __future__ import annotations

import json
import csv
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

from jgod.path_c.path_c_types import (
    PathCScenarioConfig,
    PathCScenarioResult,
    PathCExperimentConfig,
    PathCRunSummary,
)
from jgod.path_b.path_b_engine import (
    PathBEngine,
    PathBConfig,
    PathBRunResult,
)

logger = logging.getLogger(__name__)


class PathCEngine:
    """Path C Engine - Validation Lab / Scenario Engine"""
    
    def __init__(
        self,
        path_b_engine: Optional[PathBEngine] = None,
    ):
        """
        初始化 Path C Engine
        
        Args:
            path_b_engine: Path B Engine 實例（可選，若為 None 則在執行時建立）
        """
        self.path_b_engine = path_b_engine
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def run_experiment(
        self,
        config: PathCExperimentConfig,
    ) -> PathCRunSummary:
        """
        執行完整的 Path C 實驗
        
        Args:
            config: Path C 實驗配置
        
        Returns:
            PathCRunSummary 物件
        """
        self.logger.info(f"=== Path C Experiment: {config.name} ===")
        self.logger.info(f"Total scenarios: {len(config.scenarios)}")
        
        # 初始化 Path B Engine（如果尚未初始化）
        if self.path_b_engine is None:
            self.path_b_engine = PathBEngine()
        
        # 執行所有 scenario
        scenario_results: List[PathCScenarioResult] = []
        
        for i, scenario_config in enumerate(config.scenarios, 1):
            self.logger.info(f"[{i}/{len(config.scenarios)}] Running scenario: {scenario_config.name}")
            
            try:
                result = self._run_single_scenario(scenario_config)
                scenario_results.append(result)
                
                status = "Success" if result.error_message is None else "Failed"
                self.logger.info(
                    f"  Scenario '{scenario_config.name}': {status} "
                    f"(Sharpe={result.sharpe:.2f}, MaxDD={result.max_drawdown:.2%}, "
                    f"Breach={result.governance_breach_ratio:.1%})"
                )
            except Exception as e:
                self.logger.exception(f"  Scenario '{scenario_config.name}' failed with exception")
                # 建立失敗結果
                error_result = PathCScenarioResult(
                    scenario=scenario_config,
                    sharpe=0.0,
                    max_drawdown=0.0,
                    total_return=0.0,
                    governance_breach_ratio=1.0,
                    governance_breach_count=0,
                    windows_count=0,
                    raw_path_b_summary={},
                    raw_governance_summary={},
                    error_message=str(e),
                )
                scenario_results.append(error_result)
        
        # 排名 scenarios
        ranking_table = self._rank_scenarios(scenario_results)
        best_scenarios = self._get_best_scenarios(ranking_table, top_n=3)
        
        # 建立總結
        summary = PathCRunSummary(
            experiment_name=config.name,
            scenarios=scenario_results,
            ranking_table=ranking_table,
            best_scenarios=best_scenarios,
            created_at=datetime.now().isoformat(),
            config_snapshot=self._serialize_config(config),
        )
        
        # 輸出檔案
        output_dir = Path(config.output_dir) / config.name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = self._export_results(summary, output_dir)
        summary.output_files = output_files
        
        self.logger.info(f"Experiment completed. Output directory: {output_dir}")
        self.logger.info(f"  Successful: {summary.successful_scenarios}/{summary.total_scenarios}")
        self.logger.info(f"  Best scenarios: {', '.join(best_scenarios)}")
        
        return summary
    
    def _run_single_scenario(
        self,
        scenario: PathCScenarioConfig,
    ) -> PathCScenarioResult:
        """
        執行單一 scenario（呼叫 Path B Engine）
        
        Args:
            scenario: Scenario 配置
        
        Returns:
            PathCScenarioResult
        """
        start_time = time.time()
        
        # 轉換為 Path B Config
        path_b_config = self._convert_scenario_to_path_b_config(scenario)
        
        # 執行 Path B
        path_b_result: PathBRunResult = self.path_b_engine.run(path_b_config)
        
        execution_time = time.time() - start_time
        
        # 提取關鍵指標
        summary = path_b_result.summary
        governance_summary = path_b_result.governance_summary
        
        # 計算平均指標
        sharpe = summary.get("avg_sharpe", 0.0)
        max_drawdown = summary.get("avg_max_drawdown", 0.0)
        total_return = summary.get("avg_total_return", 0.0)
        windows_count = summary.get("num_windows", 0)
        
        # 計算 governance breach 比例
        if governance_summary:
            governance_breach_count = governance_summary.windows_with_any_breach
            governance_breach_ratio = (
                governance_breach_count / governance_summary.total_windows
                if governance_summary.total_windows > 0
                else 0.0
            )
        else:
            governance_breach_count = 0
            governance_breach_ratio = 0.0
        
        # 提取其他指標
        avg_tracking_error = summary.get("avg_tracking_error")
        avg_turnover = summary.get("avg_turnover_rate")
        
        return PathCScenarioResult(
            scenario=scenario,
            sharpe=sharpe,
            max_drawdown=max_drawdown,
            total_return=total_return,
            governance_breach_ratio=governance_breach_ratio,
            governance_breach_count=governance_breach_count,
            windows_count=windows_count,
            raw_path_b_summary=summary,
            raw_governance_summary=self._serialize_governance_summary(governance_summary) if governance_summary else {},
            execution_time_seconds=execution_time,
            avg_tracking_error=avg_tracking_error,
            avg_turnover=avg_turnover,
        )
    
    def _convert_scenario_to_path_b_config(
        self,
        scenario: PathCScenarioConfig,
    ) -> PathBConfig:
        """
        將 Path C Scenario Config 轉換為 Path B Config
        
        Args:
            scenario: Path C Scenario Config
        
        Returns:
            Path B Config
        """
        # 計算 train/test 日期（簡化版：使用固定比例）
        # 實際應用中可能需要更複雜的邏輯
        from datetime import datetime, timedelta
        
        start_date = datetime.strptime(scenario.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(scenario.end_date, "%Y-%m-%d")
        
        # 預設：70% train, 30% test
        total_days = (end_date - start_date).days
        train_days = int(total_days * 0.7)
        test_days = total_days - train_days
        
        train_start = start_date.strftime("%Y-%m-%d")
        train_end = (start_date + timedelta(days=train_days)).strftime("%Y-%m-%d")
        test_start = (start_date + timedelta(days=train_days + 1)).strftime("%Y-%m-%d")
        test_end = end_date.strftime("%Y-%m-%d")
        
        # 建立 Path B Config
        path_b_config = PathBConfig(
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            walkforward_window=scenario.walkforward_window,
            walkforward_step=scenario.walkforward_step,
            universe=scenario.universe,
            rebalance_frequency=scenario.rebalance_frequency,
            alpha_config_set=scenario.alpha_config_set or [
                {"name": "default_strategy", "alpha_config": {}}
            ],
            governance_rules=scenario.governance_rules,
            data_source=scenario.data_source,
            mode=scenario.mode,
            initial_nav=scenario.initial_nav,
            transaction_cost_bps=scenario.transaction_cost_bps,
            slippage_bps=scenario.slippage_bps,
            max_drawdown_threshold=scenario.max_drawdown_limit or -0.15,
            sharpe_threshold=scenario.min_sharpe or 2.0,
            tracking_error_max=scenario.max_tracking_error or 0.04,
            turnover_max=scenario.max_turnover or 1.0,
            experiment_name=f"{scenario.name}_path_b",
        )
        
        return path_b_config
    
    def _rank_scenarios(
        self,
        scenario_results: List[PathCScenarioResult],
    ) -> List[Dict[str, Any]]:
        """
        排名 scenarios
        
        排序規則：
        1. 先依 Sharpe 降冪
        2. 再依 Max Drawdown 升冪（越小越好）
        3. 再依 governance breach 比例升冪（越小越好）
        
        Args:
            scenario_results: Scenario 結果列表
        
        Returns:
            已排序的排名表
        """
        # 過濾掉失敗的 scenario
        valid_results = [r for r in scenario_results if r.error_message is None]
        
        # 排序
        sorted_results = sorted(
            valid_results,
            key=lambda r: (
                -r.sharpe,  # Sharpe 降冪（負號）
                r.max_drawdown,  # MaxDD 升冪
                r.governance_breach_ratio,  # Breach 比例升冪
            ),
        )
        
        # 建立排名表
        ranking_table = []
        for rank, result in enumerate(sorted_results, 1):
            ranking_table.append({
                "rank": rank,
                "scenario_name": result.scenario.name,
                "sharpe": result.sharpe,
                "max_drawdown": result.max_drawdown,
                "total_return": result.total_return,
                "governance_breach_ratio": result.governance_breach_ratio,
                "governance_breach_count": result.governance_breach_count,
                "windows_count": result.windows_count,
                "mode": result.scenario.mode,
                "data_source": result.scenario.data_source,
                "regime_tag": result.scenario.regime_tag or "",
            })
        
        # 將失敗的 scenario 放在最後
        failed_results = [r for r in scenario_results if r.error_message is not None]
        for result in failed_results:
            ranking_table.append({
                "rank": len(ranking_table) + 1,
                "scenario_name": result.scenario.name,
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "total_return": 0.0,
                "governance_breach_ratio": 1.0,
                "governance_breach_count": 0,
                "windows_count": 0,
                "mode": result.scenario.mode,
                "data_source": result.scenario.data_source,
                "regime_tag": result.scenario.regime_tag or "",
                "error": result.error_message,
            })
        
        return ranking_table
    
    def _get_best_scenarios(
        self,
        ranking_table: List[Dict[str, Any]],
        top_n: int = 3,
    ) -> List[str]:
        """
        取得最佳 scenario 名稱列表
        
        Args:
            ranking_table: 排名表
            top_n: 取前 N 名
        
        Returns:
            Scenario 名稱列表
        """
        best = []
        for row in ranking_table[:top_n]:
            if "error" not in row:  # 排除失敗的 scenario
                best.append(row["scenario_name"])
        return best
    
    def _export_results(
        self,
        summary: PathCRunSummary,
        output_dir: Path,
    ) -> List[str]:
        """
        匯出結果檔案
        
        Args:
            summary: Path C Run Summary
            output_dir: 輸出目錄
        
        Returns:
            輸出檔案路徑列表
        """
        output_files = []
        
        # 1. CSV 排名表
        csv_path = output_dir / "scenarios_rankings.csv"
        self._export_rankings_csv(summary.ranking_table, csv_path)
        output_files.append(str(csv_path))
        
        # 2. JSON 總結
        json_path = output_dir / "path_c_summary.json"
        self._export_summary_json(summary, json_path)
        output_files.append(str(json_path))
        
        # 3. Markdown 報告
        md_path = output_dir / "path_c_report.md"
        self._export_report_markdown(summary, md_path)
        output_files.append(str(md_path))
        
        # 4. Config JSON（可選）
        config_path = output_dir / "config.json"
        config_path.write_text(json.dumps(summary.config_snapshot, indent=2, ensure_ascii=False))
        output_files.append(str(config_path))
        
        return output_files
    
    def _export_rankings_csv(
        self,
        ranking_table: List[Dict[str, Any]],
        csv_path: Path,
    ):
        """匯出排名表為 CSV"""
        if not ranking_table:
            return
        
        fieldnames = [
            "rank", "scenario_name", "sharpe", "max_drawdown", "total_return",
            "governance_breach_ratio", "governance_breach_count", "windows_count",
            "mode", "data_source", "regime_tag",
        ]
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(ranking_table)
    
    def _export_summary_json(
        self,
        summary: PathCRunSummary,
        json_path: Path,
    ):
        """匯出總結為 JSON"""
        summary_dict = {
            "experiment_name": summary.experiment_name,
            "created_at": summary.created_at,
            "total_scenarios": summary.total_scenarios,
            "successful_scenarios": summary.successful_scenarios,
            "failed_scenarios": summary.failed_scenarios,
            "best_scenarios": summary.best_scenarios,
            "ranking_table": summary.ranking_table,
            "scenarios": [
                {
                    "name": r.scenario.name,
                    "sharpe": r.sharpe,
                    "max_drawdown": r.max_drawdown,
                    "total_return": r.total_return,
                    "governance_breach_ratio": r.governance_breach_ratio,
                    "windows_count": r.windows_count,
                    "error": r.error_message,
                }
                for r in summary.scenarios
            ],
        }
        
        json_path.write_text(
            json.dumps(summary_dict, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    
    def _export_report_markdown(
        self,
        summary: PathCRunSummary,
        md_path: Path,
    ):
        """匯出 Markdown 報告"""
        lines = [
            f"# Path C Experiment Report: {summary.experiment_name}",
            "",
            f"**Created**: {summary.created_at}",
            f"**Total Scenarios**: {summary.total_scenarios}",
            f"**Successful**: {summary.successful_scenarios}",
            f"**Failed**: {summary.failed_scenarios}",
            "",
            "## Top 3 Scenarios",
            "",
        ]
        
        # 前 3 名詳細資訊
        top_3 = [r for r in summary.ranking_table[:3] if "error" not in r]
        
        if top_3:
            for rank, row in enumerate(top_3, 1):
                scenario_name = row["scenario_name"]
                scenario_result = next(
                    (s for s in summary.scenarios if s.scenario.name == scenario_name),
                    None,
                )
                
                if scenario_result:
                    lines.extend([
                        f"### {rank}. {scenario_name}",
                        "",
                        f"- **Sharpe Ratio**: {scenario_result.sharpe:.3f}",
                        f"- **Max Drawdown**: {scenario_result.max_drawdown:.2%}",
                        f"- **Total Return**: {scenario_result.total_return:.2%}",
                        f"- **Governance Breach Ratio**: {scenario_result.governance_breach_ratio:.1%}",
                        f"- **Windows Count**: {scenario_result.windows_count}",
                        f"- **Mode**: {scenario_result.scenario.mode}",
                        f"- **Data Source**: {scenario_result.scenario.data_source}",
                        f"- **Regime Tag**: {scenario_result.scenario.regime_tag or 'N/A'}",
                        "",
                        f"*Description*: {scenario_result.scenario.description}",
                        "",
                    ])
        else:
            lines.append("No successful scenarios found.")
            lines.append("")
        
        # 所有 scenarios 摘要表格
        lines.extend([
            "## All Scenarios Summary",
            "",
            "| Rank | Scenario | Sharpe | Max DD | Total Return | Breach Ratio | Mode |",
            "|------|----------|--------|--------|--------------|--------------|------|",
        ])
        
        for row in summary.ranking_table:
            scenario_name = row["scenario_name"]
            sharpe = row.get("sharpe", 0.0)
            max_dd = row.get("max_drawdown", 0.0)
            total_return = row.get("total_return", 0.0)
            breach_ratio = row.get("governance_breach_ratio", 0.0)
            mode = row.get("mode", "")
            
            if "error" in row:
                lines.append(
                    f"| {row['rank']} | {scenario_name} (ERROR) | - | - | - | - | {mode} |"
                )
            else:
                lines.append(
                    f"| {row['rank']} | {scenario_name} | {sharpe:.3f} | {max_dd:.2%} | "
                    f"{total_return:.2%} | {breach_ratio:.1%} | {mode} |"
                )
        
        lines.append("")
        lines.append("---")
        lines.append("*Report generated by J-GOD Path C Engine*")
        
        md_path.write_text("\n".join(lines), encoding="utf-8")
    
    def _serialize_config(self, config: PathCExperimentConfig) -> Dict:
        """序列化配置"""
        return {
            "name": config.name,
            "description": config.description,
            "created_by": config.created_by,
            "tags": config.tags,
            "output_dir": config.output_dir,
            "scenarios": [
                {
                    "name": s.name,
                    "description": s.description,
                    "start_date": s.start_date,
                    "end_date": s.end_date,
                    "universe": s.universe,
                    "mode": s.mode,
                    "data_source": s.data_source,
                    "walkforward_window": s.walkforward_window,
                    "walkforward_step": s.walkforward_step,
                    "regime_tag": s.regime_tag,
                }
                for s in config.scenarios
            ],
        }
    
    def _serialize_governance_summary(self, gov_summary) -> Dict:
        """序列化 governance summary"""
        if gov_summary is None:
            return {}
        
        return {
            "total_windows": gov_summary.total_windows,
            "rule_hit_counts": gov_summary.rule_hit_counts,
            "windows_with_any_breach": gov_summary.windows_with_any_breach,
            "max_consecutive_breach_windows": gov_summary.max_consecutive_breach_windows,
            "global_metrics": gov_summary.global_metrics,
        }

