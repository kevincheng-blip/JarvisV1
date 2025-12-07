"""
J-GOD Strategy & Signal Engine v1

統一入口：從 prediction_snapshots 產生標準化的多空信號清單。

設計目標：
- 讀取特定日期的 prediction_snapshots
- 根據 score / signal / risk_flags → 產出標準化的多空信號
- 排出 Long Top N / Short Top N
- 未來 Path A / War Room / AI Policy 都只讀這裡
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Literal, Optional

from sqlalchemy.orm import Session

from jgod.storage.db import get_session
from jgod.storage.models import PredictionSnapshot


@dataclass
class StrategySignal:
    """單一股票、單一日期的策略信號"""
    symbol: str
    date: date
    side: Literal["LONG", "SHORT", "FLAT"]  # 多/空/中立
    base_score: float  # 來自 prediction_snapshots 的原始 score
    rank_score: float  # 用來排序的分數（v1 = base_score，未來可加權）
    raw_signal: str  # 原本 prediction 的 signal（如 STRONG_BUY / BUY / SHORT / AVOID）
    risk_flags_summary: Literal["LOW", "MEDIUM", "HIGH"]  # 風險分級
    sources: List[str] = field(default_factory=lambda: ["prediction_v1"])  # 信號來源列表
    
    def to_dict(self) -> Dict:
        """轉換為字典（API 回應格式）"""
        return {
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "side": self.side,
            "base_score": self.base_score,
            "rank_score": self.rank_score,
            "raw_signal": self.raw_signal,
            "risk_flags_summary": self.risk_flags_summary,
            "sources": self.sources,
        }


@dataclass
class DailySignalSet:
    """同一天、整個 universe 的匯總結果"""
    date: date
    universe_size: int  # 當天有幾檔有預測
    long_candidates: List[StrategySignal] = field(default_factory=list)  # 已排序
    short_candidates: List[StrategySignal] = field(default_factory=list)  # 已排序
    params: Dict = field(default_factory=dict)  # 生成參數（min_score, long_limit, short_limit, allow_short）
    
    def to_dict(self) -> Dict:
        """轉換為字典（API 回應格式）"""
        return {
            "date": self.date.isoformat(),
            "universe_size": self.universe_size,
            "long_candidates": [sig.to_dict() for sig in self.long_candidates],
            "short_candidates": [sig.to_dict() for sig in self.short_candidates],
            "params": self.params,
        }
    
    def get_long_summary(self) -> Dict:
        """取得 Long 清單統計摘要"""
        if not self.long_candidates:
            return {"count": 0, "avg_score": 0.0, "max_score": 0.0, "min_score": 0.0}
        
        scores = [sig.rank_score for sig in self.long_candidates]
        return {
            "count": len(scores),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
        }
    
    def get_short_summary(self) -> Dict:
        """取得 Short 清單統計摘要"""
        if not self.short_candidates:
            return {"count": 0, "avg_score": 0.0, "max_score": 0.0, "min_score": 0.0}
        
        scores = [sig.rank_score for sig in self.short_candidates]
        return {
            "count": len(scores),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
        }


class StrategyEngineV1:
    """
    Strategy & Signal Engine v1
    
    核心功能：
    - 從 prediction_snapshots 讀取特定日期的預測結果
    - 將預測結果轉換為標準化的多空信號
    - 排出 Long Top N / Short Top N
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        初始化 Strategy Engine
        
        Args:
            session: SQLAlchemy Session（如果為 None，則使用 get_session()）
        """
        self._session = session
        self._session_generator = None
    
    def _get_session(self) -> Session:
        """取得 Session（支援外部注入或自動生成）"""
        if self._session is not None:
            return self._session
        
        if self._session_generator is None:
            self._session_generator = get_session()
        return next(self._session_generator)
    
    def _map_signal_to_side(self, raw_signal: Optional[str]) -> Literal["LONG", "SHORT", "FLAT"]:
        """
        映射 prediction 的 signal → side
        
        Args:
            raw_signal: 原始 signal（如 STRONG_BUY / BUY / SHORT / AVOID）
        
        Returns:
            "LONG" / "SHORT" / "FLAT"
        """
        if not raw_signal:
            return "FLAT"
        
        signal_upper = raw_signal.upper()
        
        # LONG 訊號
        if signal_upper in ["STRONG_BUY", "BUY", "STRONG_BUY_BUY"]:
            return "LONG"
        
        # SHORT 訊號
        if signal_upper in ["SHORT", "STRONG_SHORT", "SELL"]:
            return "SHORT"
        
        # FLAT / 中立
        if signal_upper in ["NEUTRAL", "AVOID", "HOLD", "FLAT"]:
            return "FLAT"
        
        # 預設 FLAT
        return "FLAT"
    
    def _evaluate_risk_flags(self, risk_flags_json: Optional[Dict]) -> Literal["LOW", "MEDIUM", "HIGH"]:
        """
        評估風險標記，回傳風險分級
        
        Args:
            risk_flags_json: risk_flags_json 欄位（可能是 JSON 或 list）
        
        Returns:
            "LOW" / "MEDIUM" / "HIGH"
        """
        if not risk_flags_json:
            return "LOW"
        
        # 處理不同格式（可能是 list 或 dict）
        risk_flags = []
        if isinstance(risk_flags_json, list):
            risk_flags = risk_flags_json
        elif isinstance(risk_flags_json, dict):
            risk_flags = list(risk_flags_json.keys()) if risk_flags_json else []
        
        if not risk_flags:
            return "LOW"
        
        # 檢查是否有高風險標記
        high_risk_keywords = ["HIGH_RISK", "CRITICAL", "DANGER", "BLACKLIST", "SUSPEND"]
        for flag in risk_flags:
            flag_str = str(flag).upper()
            if any(keyword in flag_str for keyword in high_risk_keywords):
                return "HIGH"
        
        # 1-2 個一般風險 → MEDIUM，3 個以上 → HIGH
        if len(risk_flags) <= 2:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def generate_signals_for_date(
        self,
        date: date,
        universe: Optional[List[str]] = None,
        long_limit: int = 30,
        short_limit: int = 30,
        min_score: float = 0.0,
        allow_short: bool = True,
    ) -> DailySignalSet:
        """
        產生指定日期的多空信號清單
        
        Args:
            date: 日期
            universe: 股票池（如果為 None，則取得所有有預測的股票）
            long_limit: Long 候選清單上限（預設 30）
            short_limit: Short 候選清單上限（預設 30）
            min_score: 最低分數門檻（預設 0.0）
            allow_short: 是否允許放空（預設 True）
        
        Returns:
            DailySignalSet: 標準化的多空信號清單
        """
        session = self._get_session()
        
        try:
            # 查詢 prediction_snapshots
            query = (
                session.query(PredictionSnapshot)
                .filter(PredictionSnapshot.date == date)
            )
            
            # 如果指定 universe，只取該股票池
            if universe:
                query = query.filter(PredictionSnapshot.symbol.in_(universe))
            
            # 只保留有 score 的紀錄
            query = query.filter(PredictionSnapshot.score.isnot(None))
            
            snapshots = query.all()
            
            # 統計 universe_size（當天有預測的總檔數）
            universe_size = len(snapshots)
            
            # 轉換為 StrategySignal
            signals: List[StrategySignal] = []
            
            for snap in snapshots:
                # 取得原始 signal（優先使用 verdict，其次使用 signal）
                raw_signal = snap.verdict or snap.signal
                side = self._map_signal_to_side(raw_signal)
                
                # 取得 score
                base_score = snap.score or snap.total_score or 0.0
                
                # 如果 score 低於門檻，跳過
                if base_score < min_score:
                    continue
                
                # v1: rank_score = base_score（未來可加權）
                rank_score = base_score
                
                # 評估風險標記
                risk_flags_summary = self._evaluate_risk_flags(snap.risk_flags_json)
                
                signal = StrategySignal(
                    symbol=snap.symbol,
                    date=date,
                    side=side,
                    base_score=base_score,
                    rank_score=rank_score,
                    raw_signal=raw_signal or "UNKNOWN",
                    risk_flags_summary=risk_flags_summary,
                    sources=["prediction_v1"],
                )
                
                signals.append(signal)
            
            # 分類為 Long / Short
            long_signals = [sig for sig in signals if sig.side == "LONG"]
            short_signals = [sig for sig in signals if sig.side == "SHORT"] if allow_short else []
            
            # 排序：依 rank_score 由高到低
            long_signals.sort(key=lambda x: x.rank_score, reverse=True)
            short_signals.sort(key=lambda x: x.rank_score, reverse=True)
            
            # 取前 N 個
            long_candidates = long_signals[:long_limit]
            short_candidates = short_signals[:short_limit]
            
            # 組裝 DailySignalSet
            return DailySignalSet(
                date=date,
                universe_size=universe_size,
                long_candidates=long_candidates,
                short_candidates=short_candidates,
                params={
                    "universe": universe or "ALL",
                    "long_limit": long_limit,
                    "short_limit": short_limit,
                    "min_score": min_score,
                    "allow_short": allow_short,
                },
            )
            
        finally:
            if self._session is None:
                # 如果是自動生成的 session，需要關閉
                pass  # get_session() 使用 generator，會自動關閉

