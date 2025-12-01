"""Diagnosis Types v1

定義 Diagnosis Engine 使用的資料結構類型。

Reference:
- docs/JGOD_DIAGNOSIS_ENGINE_STANDARD_v1.md
- spec/JGOD_DiagnosisEngine_Spec.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import uuid


@dataclass
class DiagnosticEvent:
    """診斷事件資料結構
    
    將系統問題轉換為標準事件格式。
    
    Attributes:
        id: 唯一識別碼
        timestamp: 事件時間戳
        source_module: 來源模組（PATH_A, EXECUTION, PERFORMANCE, OPTIMIZER, RISK_MODEL）
        issue_type: 問題類型
        severity: 嚴重度（INFO, WARN, CRITICAL）
        message: 人類可讀描述
        metrics_before: 指標變更前快照
        metrics_after: 指標變更後快照
        tags: 標籤列表
        related_symbols: 相關標的列表
        related_factors: 相關因子列表
        related_error_event_id: 相關的 ErrorEvent ID（如果已有）
    """
    
    source_module: str
    issue_type: str
    severity: str
    message: str
    timestamp: Optional[datetime] = None
    id: Optional[str] = None
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    related_symbols: List[str] = field(default_factory=list)
    related_factors: List[str] = field(default_factory=list)
    related_error_event_id: Optional[str] = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.id is None:
            self.id = f"diag_{uuid.uuid4().hex[:8]}"
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        # 驗證
        if self.severity not in ["INFO", "WARN", "CRITICAL"]:
            raise ValueError(f"Invalid severity: {self.severity}")
        
        valid_issue_types = [
            "TE_EXCEEDED",
            "DRAWDOWN_EXCEEDED",
            "TURNOVER_TOO_HIGH",
            "CONSTRAINT_VIOLATION",
            "ALPHA_UNDERPERFORM",
            "RISK_CONTROL_FAILED",
            "DATA_QUALITY",
            "OPTIMIZER_INFEASIBLE",
        ]
        if self.issue_type not in valid_issue_types:
            # 允許自定義 issue_type，但記錄警告
            pass
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "source_module": self.source_module,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "tags": self.tags,
            "related_symbols": self.related_symbols,
            "related_factors": self.related_factors,
            "related_error_event_id": self.related_error_event_id,
        }


@dataclass
class SystemHealthSnapshot:
    """系統健康快照資料結構
    
    對「某一實驗 / 某一回測」的總體健康快照。
    
    Attributes:
        experiment_name: 實驗名稱
        start_date: 開始日期
        end_date: 結束日期
        total_return: 累積報酬
        cagr: 年化報酬
        sharpe: Sharpe Ratio
        max_drawdown: 最大回落
        tracking_error: 追蹤誤差
        turnover: 換手率
        violated_constraints: 違反的約束列表
        error_event_counts: ErrorEvent 計數（依類型）
    """
    
    experiment_name: str
    start_date: date
    end_date: date
    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    tracking_error: float
    turnover: float
    violated_constraints: List[str] = field(default_factory=list)
    error_event_counts: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "experiment_name": self.experiment_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_return": self.total_return,
            "cagr": self.cagr,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "tracking_error": self.tracking_error,
            "turnover": self.turnover,
            "violated_constraints": self.violated_constraints,
            "error_event_counts": self.error_event_counts,
        }


@dataclass
class RepairAction:
    """修復行動資料結構
    
    不直接改 code，只輸出建議。
    
    Attributes:
        action_id: 行動 ID
        action_type: 行動類型（TUNE_CONFIG, CHECK_DATA, REVIEW_RULES, etc.）
        target_module: 目標模組
        description: 行動描述
        proposed_changes: 建議的變更（例如：{"optimizer.params.TE_max": 0.15}）
        priority: 優先級（HIGH, MEDIUM, LOW）
    """
    
    action_type: str
    target_module: str
    description: str
    priority: str
    action_id: Optional[str] = None
    proposed_changes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化後處理"""
        if self.action_id is None:
            self.action_id = f"action_{uuid.uuid4().hex[:8]}"
        
        # 驗證
        valid_action_types = [
            "TUNE_CONFIG",
            "CHECK_DATA",
            "REVIEW_RULES",
            "ADJUST_FACTOR_WEIGHT",
            "RELAX_CONSTRAINT",
        ]
        if self.action_type not in valid_action_types:
            # 允許自定義 action_type
            pass
        
        if self.priority not in ["HIGH", "MEDIUM", "LOW"]:
            raise ValueError(f"Invalid priority: {self.priority}")
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "target_module": self.target_module,
            "description": self.description,
            "proposed_changes": self.proposed_changes,
            "priority": self.priority,
        }


@dataclass
class RepairPlan:
    """修復計畫資料結構
    
    Attributes:
        experiment_name: 實驗名稱
        summary: 計畫摘要
        actions: 修復行動列表
    """
    
    experiment_name: str
    summary: str
    actions: List[RepairAction] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "experiment_name": self.experiment_name,
            "summary": self.summary,
            "actions": [action.to_dict() for action in self.actions],
        }


@dataclass
class DiagnosisEngineResult:
    """Diagnosis Engine 完整輸出結果
    
    Attributes:
        health: 系統健康快照
        diagnostic_events: 診斷事件列表
        repair_plan: 修復計畫
    """
    
    health: SystemHealthSnapshot
    diagnostic_events: List[DiagnosticEvent]
    repair_plan: RepairPlan
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "health": self.health.to_dict(),
            "diagnostic_events": [event.to_dict() for event in self.diagnostic_events],
            "repair_plan": self.repair_plan.to_dict(),
        }

