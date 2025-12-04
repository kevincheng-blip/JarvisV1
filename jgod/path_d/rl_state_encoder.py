"""
Path D State Encoder

將 Path B Window Result 轉換為 Path D RL 狀態向量。
"""

from __future__ import annotations

from typing import Dict, List, Any
import numpy as np

from jgod.path_d.path_d_types import PathDState
from jgod.path_b.path_b_engine import PathBWindowResult


def build_pathd_state_from_pathb(
    window_result: PathBWindowResult,
    current_params: Dict[str, float],
    recent_windows: List[PathBWindowResult] = None,
) -> PathDState:
    """
    從 Path B Window Result 建立 Path D State
    
    Args:
        window_result: 最新的 Path B Window Result
        current_params: 當前治理參數
            - "sharpe_floor"
            - "max_drawdown_limit"
            - "turnover_limit"
            - "te_max"
            - "mode" (basic / extreme)
        recent_windows: 最近的 window results（用於計算平均值）
    
    Returns:
        PathDState 物件
    """
    recent_windows = recent_windows or []
    
    # 從 window_result 提取績效指標
    sharpe = window_result.sharpe_ratio
    max_dd = window_result.max_drawdown
    turnover = window_result.turnover_rate
    tracking_error = window_result.tracking_error or 0.0
    
    # 計算 breach ratio（從 governance events 或 windows_governance）
    breach_ratio = 0.0
    if hasattr(window_result, 'governance_events') and window_result.governance_events:
        breaches = sum(1 for event in window_result.governance_events if event.get('triggered', False))
        breach_ratio = breaches / len(window_result.governance_events) if window_result.governance_events else 0.0
    
    # 計算最近 3 個和 5 個 window 的平均值
    sharpe_list = [wr.sharpe_ratio for wr in recent_windows[-5:]]
    breach_list = []
    for wr in recent_windows[-5:]:
        if hasattr(wr, 'governance_events') and wr.governance_events:
            breaches = sum(1 for event in wr.governance_events if event.get('triggered', False))
            breach_ratio_local = breaches / len(wr.governance_events) if wr.governance_events else 0.0
            breach_list.append(breach_ratio_local)
        else:
            breach_list.append(0.0)
    
    avg_sharpe_3 = np.mean(sharpe_list[-3:]) if len(sharpe_list) >= 3 else sharpe
    avg_sharpe_5 = np.mean(sharpe_list) if sharpe_list else sharpe
    avg_breach_3 = np.mean(breach_list[-3:]) if len(breach_list) >= 3 else breach_ratio
    avg_breach_5 = np.mean(breach_list) if breach_list else breach_ratio
    
    # 從 current_params 取得當前設定
    sharpe_floor = current_params.get("sharpe_floor", 0.0)
    max_drawdown_limit = current_params.get("max_drawdown_limit", 15.0)
    turnover_limit = current_params.get("turnover_limit", 100.0)
    te_max = current_params.get("te_max", 4.0)
    mode = current_params.get("mode", "basic")
    mode_id = 1 if mode == "extreme" else 0
    
    return PathDState(
        sharpe_last=sharpe,
        max_drawdown_last=max_dd,
        breach_ratio_last=breach_ratio,
        avg_sharpe_3=avg_sharpe_3,
        avg_breach_ratio_3=avg_breach_3,
        avg_sharpe_5=avg_sharpe_5,
        avg_breach_ratio_5=avg_breach_5,
        current_sharpe_floor=sharpe_floor,
        current_max_drawdown_limit=max_drawdown_limit,
        current_turnover_limit=turnover_limit,
        current_te_max=te_max,
        mode_id=mode_id,
    )


def encode_state_to_vector(state: PathDState) -> np.ndarray:
    """
    將 PathDState 編碼為 1D numpy array
    
    Args:
        state: PathDState 物件
    
    Returns:
        1D numpy array (dtype=float32)
    """
    # 依固定順序轉換所有欄位
    vector = np.array([
        state.sharpe_last,
        state.max_drawdown_last / 100.0,  # Normalize MaxDD (百分比轉小數)
        state.breach_ratio_last,  # 已在 0~1 範圍
        state.avg_sharpe_3,
        state.avg_breach_ratio_3,
        state.avg_sharpe_5,
        state.avg_breach_ratio_5,
        state.current_sharpe_floor,
        state.current_max_drawdown_limit / 100.0,  # Normalize
        state.current_turnover_limit / 100.0,  # Normalize
        state.current_te_max / 100.0,  # Normalize
        float(state.mode_id),  # 0 or 1
    ], dtype=np.float32)
    
    # Clip 極端值以避免 NaN
    vector = np.clip(vector, -10.0, 10.0)
    
    # 檢查是否有 NaN
    if np.isnan(vector).any():
        vector = np.nan_to_num(vector, nan=0.0, posinf=10.0, neginf=-10.0)
    
    return vector

