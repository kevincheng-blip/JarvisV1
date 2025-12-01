"""Experiment Types v1

定義 Experiment Orchestrator 使用的資料結構類型。

Reference:
- docs/JGOD_EXPERIMENT_ORCHESTRATOR_STANDARD_v1.md
- spec/JGOD_ExperimentOrchestrator_Spec.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

# Type imports（避免循環導入）
try:
    from jgod.path_a.path_a_schema import PathABacktestResult
    from jgod.performance.performance_types import PerformanceEngineResult
    from jgod.diagnostics.diagnosis_types import DiagnosisEngineResult, RepairAction
except ImportError:
    # 開發階段可能無法導入，使用類型註解
    PathABacktestResult = Any
    PerformanceEngineResult = Any
    DiagnosisEngineResult = Any
    RepairAction = Any


@dataclass
class ExperimentConfig:
    """實驗設定資料結構"""
    
    name: str                         # 實驗名稱
    start_date: str                   # 開始日期 "YYYY-MM-DD"
    end_date: str                     # 結束日期 "YYYY-MM-DD"
    rebalance_frequency: str          # 再平衡頻率 "D" / "W" / "M"
    universe: List[str]               # 標的列表
    data_source: str                  # 資料來源 "finmind" / "mock"
    
    # 優化器參數
    optimizer_params: Dict[str, Any] = field(default_factory=dict)
    
    # 執行參數
    execution_params: Dict[str, Any] = field(default_factory=dict)
    
    # 診斷參數
    diagnosis_params: Dict[str, Any] = field(default_factory=dict)
    
    notes: Optional[str] = None       # 實驗備註
    
    def validate(self) -> None:
        """驗證實驗設定"""
        if self.rebalance_frequency not in ["D", "W", "M"]:
            raise ValueError(
                f"Invalid rebalance_frequency: {self.rebalance_frequency}. "
                "Must be 'D', 'W', or 'M'"
            )
        
        if self.data_source not in ["finmind", "mock"]:
            raise ValueError(
                f"Invalid data_source: {self.data_source}. "
                "Must be 'finmind' or 'mock'"
            )
        
        if not self.universe:
            raise ValueError("Universe cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "name": self.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "rebalance_frequency": self.rebalance_frequency,
            "universe": self.universe,
            "data_source": self.data_source,
            "optimizer_params": self.optimizer_params,
            "execution_params": self.execution_params,
            "diagnosis_params": self.diagnosis_params,
            "notes": self.notes,
        }


@dataclass
class ExperimentArtifacts:
    """實驗中間產物資料結構"""
    
    path_a_result: PathABacktestResult
    performance_result: PerformanceEngineResult
    diagnosis_result: DiagnosisEngineResult
    execution_stats: Dict[str, Any] = field(default_factory=dict)
    optimizer_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentReport:
    """實驗報告資料結構"""
    
    summary: Dict[str, Any]           # 績效摘要
    highlights: List[str]              # 亮點摘要
    diagnosis_summary: str             # 診斷摘要
    repair_actions: List[RepairAction] = field(default_factory=list)
    files_generated: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "summary": self.summary,
            "highlights": self.highlights,
            "diagnosis_summary": self.diagnosis_summary,
            "repair_actions": [action.to_dict() for action in self.repair_actions],
            "files_generated": self.files_generated,
        }


@dataclass
class ExperimentRunResult:
    """實驗執行結果資料結構"""
    
    config: ExperimentConfig
    artifacts: ExperimentArtifacts
    report: ExperimentReport
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "config": self.config.to_dict(),
            "report": self.report.to_dict(),
            # artifacts 包含大型物件，不轉換為 dict
        }

