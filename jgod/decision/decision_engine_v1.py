"""
J-GOD Decision & Risk Engine v1

統一入口：從 DailySignalSet 產生目標部位配置表 PortfolioPlan。

核心功能：
- 讀取 Strategy & Signal Engine v1 產出的 DailySignalSet
- 套用簡單但合理的風險規則（score 加總、cap、normalize + 風險上限）
- 計算每檔股票的 target_weight、多空總曝險等
- v1 版本不做複雜 Markowitz MVO，只做簡單權重分配
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Literal, Optional

from jgod.strategy import StrategyEngineV1, DailySignalSet, StrategySignal

# Import risk config loader
try:
    from jgod.decision.risk_config_loader import load_risk_config
except ImportError:
    # Fallback if module not found
    def load_risk_config(path: str) -> Optional[Dict]:
        return None


@dataclass
class RiskConfig:
    """風控參數配置"""
    long_budget: float = 0.6  # Long 總預算（60%）
    short_budget: float = 0.2  # Short 總預算（20%）
    max_weight_per_symbol: float = 0.10  # 單檔最大權重（10%）
    min_score: float = 0.0  # 最低分數門檻
    allow_short: bool = True  # 是否允許放空
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            "long_budget": self.long_budget,
            "short_budget": self.short_budget,
            "max_weight_per_symbol": self.max_weight_per_symbol,
            "min_score": self.min_score,
            "allow_short": self.allow_short,
        }


@dataclass
class PositionPlan:
    """單檔部位計劃"""
    symbol: str
    date: date
    side: Literal["LONG", "SHORT"]
    target_weight: float  # LONG 為正，SHORT 為負（例如 0.05 = 5% 資金，-0.03 = 空 3% 資金）
    base_score: float  # 來自 StrategySignal.base_score
    rank_score: float  # 用來分配權重的分數
    risk_flags_summary: Literal["LOW", "MEDIUM", "HIGH"]
    source_signals: List[str] = field(default_factory=lambda: ["strategy_engine_v1"])
    
    def to_dict(self) -> Dict:
        """轉換為字典（API 回應格式）"""
        return {
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "side": self.side,
            "target_weight": self.target_weight,
            "base_score": self.base_score,
            "rank_score": self.rank_score,
            "risk_flags_summary": self.risk_flags_summary,
            "source_signals": self.source_signals,
        }


@dataclass
class PortfolioPlan:
    """整體組合計劃"""
    date: date
    universe_size: int  # 當天 universe 有幾檔有預測
    params: Dict = field(default_factory=dict)  # 生成參數
    positions: List[PositionPlan] = field(default_factory=list)  # 依 abs(target_weight) 由大到小排序
    summary: Dict = field(default_factory=dict)  # 統計摘要
    
    def to_dict(self) -> Dict:
        """轉換為字典（API 回應格式）"""
        return {
            "date": self.date.isoformat(),
            "universe_size": self.universe_size,
            "params": self.params,
            "positions": [pos.to_dict() for pos in self.positions],
            "summary": self.summary,
        }


class DecisionEngineV1:
    """
    Decision & Risk Engine v1
    
    核心功能：
    - 從 DailySignalSet 讀取多空信號
    - 套用簡單權重分配邏輯（score 加總、cap、normalize + 風險上限）
    - 產出 PortfolioPlan（目標部位配置表）
    """
    
    def __init__(
        self,
        strategy_engine: Optional[StrategyEngineV1] = None,
        risk_config_dict: Optional[Dict] = None,
    ):
        """
        初始化 Decision Engine
        
        Args:
            strategy_engine: StrategyEngineV1 實例（如果為 None，則自動建立）
            risk_config_dict: RiskConfig 參數字典（可選），會作為預設值使用
                - long_budget
                - short_budget
                - max_weight_per_symbol
                - min_score
                - allow_short
        """
        self.strategy_engine = strategy_engine or StrategyEngineV1()
        self.risk_config_dict = risk_config_dict or {}
    
    def _calculate_weights_with_cap(
        self,
        candidates: List[StrategySignal],
        budget: float,
        max_weight_per_symbol: float,
    ) -> List[float]:
        """
        計算權重（帶有單檔上限 cap 和重新分配）
        
        Args:
            candidates: 候選清單（已排序，score 高的在前）
            budget: 總預算
            max_weight_per_symbol: 單檔最大權重
        
        Returns:
            List[float]: 權重列表（對應 candidates）
        """
        if not candidates:
            return []
        
        # 只取 score > 0 的候選
        valid_candidates = [c for c in candidates if c.rank_score > 0]
        if not valid_candidates:
            return [0.0] * len(candidates)
        
        # 計算總分
        total_score = sum(c.rank_score for c in valid_candidates)
        if total_score <= 0:
            return [0.0] * len(candidates)
        
        # 初步權重（按分數比例分配）
        raw_weights = []
        candidate_to_weight = {}
        
        for candidate in valid_candidates:
            w_raw = (candidate.rank_score / total_score) * budget
            candidate_to_weight[candidate.symbol] = w_raw
            raw_weights.append((candidate, w_raw))
        
        # 套用 cap 限制
        capped_weights = []
        excess_weights = 0.0
        
        for candidate, w_raw in raw_weights:
            if w_raw > max_weight_per_symbol:
                # 超過 cap，只給 max_weight_per_symbol
                capped_weights.append((candidate, max_weight_per_symbol))
                excess_weights += (w_raw - max_weight_per_symbol)
            else:
                capped_weights.append((candidate, w_raw))
        
        # 重新分配超出的權重（簡單版：均分給未達 cap 的檔）
        if excess_weights > 0:
            # 找出未達 cap 的檔
            uncapped = [(c, w) for c, w in capped_weights if w < max_weight_per_symbol]
            
            if uncapped:
                # 計算還能分配的空間
                remaining_space = sum(max_weight_per_symbol - w for _, w in uncapped)
                
                if remaining_space > 0:
                    # 按剩餘空間比例分配 excess
                    for i, (candidate, w) in enumerate(uncapped):
                        can_add = max_weight_per_symbol - w
                        add_amount = min(can_add, (can_add / remaining_space) * excess_weights)
                        
                        # 更新 capped_weights
                        for j, (c, w2) in enumerate(capped_weights):
                            if c.symbol == candidate.symbol:
                                capped_weights[j] = (c, w + add_amount)
                                break
        
        # 建立 symbol -> weight 映射
        weight_map = {c.symbol: w for c, w in capped_weights}
        
        # 回傳對應原始 candidates 順序的權重
        result = []
        for candidate in candidates:
            result.append(weight_map.get(candidate.symbol, 0.0))
        
        return result
    
    def generate_portfolio_for_date(
        self,
        date: date,
        universe: Optional[List[str]] = None,
        long_budget: Optional[float] = None,
        short_budget: Optional[float] = None,
        max_weight_per_symbol: Optional[float] = None,
        min_score: Optional[float] = None,
        allow_short: Optional[bool] = None,
    ) -> PortfolioPlan:
        """
        產生指定日期的目標部位配置表
        
        Args:
            date: 日期
            universe: 股票池（如果為 None，則取得所有有預測的股票）
            long_budget: Long 總預算（如果為 None，使用 risk_config_dict 或預設 0.6）
            short_budget: Short 總預算（如果為 None，使用 risk_config_dict 或預設 0.2）
            max_weight_per_symbol: 單檔最大權重（如果為 None，使用 risk_config_dict 或預設 0.10）
            min_score: 最低分數門檻（如果為 None，使用 risk_config_dict 或預設 0.0）
            allow_short: 是否允許放空（如果為 None，使用 risk_config_dict 或預設 True）
        
        Returns:
            PortfolioPlan: 目標部位配置表
        """
        # 優先順序：參數 > risk_config_dict > 預設值
        long_budget = long_budget if long_budget is not None else self.risk_config_dict.get("long_budget", 0.6)
        short_budget = short_budget if short_budget is not None else self.risk_config_dict.get("short_budget", 0.2)
        max_weight_per_symbol = max_weight_per_symbol if max_weight_per_symbol is not None else self.risk_config_dict.get("max_weight_per_symbol", 0.10)
        min_score = min_score if min_score is not None else self.risk_config_dict.get("min_score", 0.0)
        allow_short = allow_short if allow_short is not None else self.risk_config_dict.get("allow_short", True)
        # 取得 DailySignalSet
        signal_set = self.strategy_engine.generate_signals_for_date(
            date=date,
            universe=universe,
            long_limit=100,  # 先取足夠多的候選，之後再分配權重
            short_limit=100 if allow_short else 0,
            min_score=min_score,
            allow_short=allow_short,
        )
        
        # 過濾：長空對稱 + 針對 SHORT 用 rank_score / 絕對值門檻
        # LONG: 只接受「分數為正」且「大於等於 min_score」
        long_candidates = []
        for sig in signal_set.long_candidates:
            if sig.base_score is None:
                continue
            if sig.base_score <= 0:
                continue
            if sig.base_score < min_score:
                continue
            long_candidates.append(sig)
        
        # SHORT: 只接受「分數為負」，但門檻用絕對值 / rank_score
        # rank_score 在 StrategyEngineV1 已經是 abs(score)
        short_candidates = []
        if allow_short:
            for sig in signal_set.short_candidates:
                if sig.base_score is None:
                    continue
                if sig.base_score >= 0:
                    continue
                # rank_score 在 StrategyEngineV1 已經是 abs(score)
                if sig.rank_score < min_score:
                    continue
                short_candidates.append(sig)
        
        # 計算 Long 權重
        long_weights = self._calculate_weights_with_cap(
            candidates=long_candidates,
            budget=long_budget,
            max_weight_per_symbol=max_weight_per_symbol,
        )
        
        # 計算 Short 權重（為負數）
        short_weights_raw = self._calculate_weights_with_cap(
            candidates=short_candidates,
            budget=short_budget,
            max_weight_per_symbol=max_weight_per_symbol,
        )
        short_weights = [-w for w in short_weights_raw]  # Short 為負
        
        # 組裝 PositionPlan
        positions: List[PositionPlan] = []
        
        # Long positions
        for candidate, weight in zip(long_candidates, long_weights):
            if weight > 0:  # 只加入有權重的部位
                positions.append(PositionPlan(
                    symbol=candidate.symbol,
                    date=date,
                    side="LONG",
                    target_weight=weight,
                    base_score=candidate.base_score,
                    rank_score=candidate.rank_score,
                    risk_flags_summary=candidate.risk_flags_summary,
                    source_signals=candidate.sources,
                ))
        
        # Short positions
        for candidate, weight in zip(short_candidates, short_weights):
            if weight < 0:  # 只加入有權重的部位（負數）
                positions.append(PositionPlan(
                    symbol=candidate.symbol,
                    date=date,
                    side="SHORT",
                    target_weight=weight,
                    base_score=candidate.base_score,
                    rank_score=candidate.rank_score,
                    risk_flags_summary=candidate.risk_flags_summary,
                    source_signals=candidate.sources,
                ))
        
        # 排序：依 abs(target_weight) 由大到小
        positions.sort(key=lambda x: abs(x.target_weight), reverse=True)
        
        # 計算 summary
        total_long_weight = sum(pos.target_weight for pos in positions if pos.side == "LONG")
        total_short_weight = sum(pos.target_weight for pos in positions if pos.side == "SHORT")  # 已經是負數
        net_exposure = total_long_weight + total_short_weight
        num_long_positions = len([pos for pos in positions if pos.side == "LONG"])
        num_short_positions = len([pos for pos in positions if pos.side == "SHORT"])
        
        summary = {
            "total_long_weight": round(total_long_weight, 4),
            "total_short_weight": round(total_short_weight, 4),
            "net_exposure": round(net_exposure, 4),
            "num_long_positions": num_long_positions,
            "num_short_positions": num_short_positions,
        }
        
        # 組裝 PortfolioPlan
        return PortfolioPlan(
            date=date,
            universe_size=signal_set.universe_size,
            params={
                "universe": universe or "ALL",
                "long_budget": long_budget,
                "short_budget": short_budget,
                "max_weight_per_symbol": max_weight_per_symbol,
                "min_score": min_score,
                "allow_short": allow_short,
            },
            positions=positions,
            summary=summary,
        )

