"""
時序監控器：追蹤效能指標
"""
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class TimingMetrics:
    """時序指標"""
    start_time: float = 0.0
    first_chunk_time: Optional[float] = None
    completion_time: Optional[float] = None
    total_chunks: int = 0
    
    @property
    def time_to_first_chunk(self) -> Optional[float]:
        """第一個 chunk 出現的時間"""
        if self.first_chunk_time:
            return self.first_chunk_time - self.start_time
        return None
    
    @property
    def total_duration(self) -> Optional[float]:
        """總執行時間"""
        if self.completion_time:
            return self.completion_time - self.start_time
        return None


class TimingMonitor:
    """時序監控器"""
    
    def __init__(self):
        self.metrics: Dict[str, TimingMetrics] = defaultdict(TimingMetrics)
    
    def start_role(self, role_name: str):
        """開始追蹤角色"""
        self.metrics[role_name].start_time = time.time()
    
    def record_first_chunk(self, role_name: str):
        """記錄第一個 chunk"""
        if self.metrics[role_name].first_chunk_time is None:
            self.metrics[role_name].first_chunk_time = time.time()
        self.metrics[role_name].total_chunks += 1
    
    def complete_role(self, role_name: str):
        """完成角色"""
        self.metrics[role_name].completion_time = time.time()
    
    def get_metrics(self, role_name: str) -> TimingMetrics:
        """取得角色的時序指標"""
        return self.metrics[role_name]
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """取得所有角色的時序摘要"""
        summary = {}
        for role_name, metrics in self.metrics.items():
            summary[role_name] = {
                "time_to_first_chunk": metrics.time_to_first_chunk or 0.0,
                "total_duration": metrics.total_duration or 0.0,
                "total_chunks": metrics.total_chunks,
            }
        return summary
    
    def reset(self):
        """重置所有指標"""
        self.metrics.clear()

