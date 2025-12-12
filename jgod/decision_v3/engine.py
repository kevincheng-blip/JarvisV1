"""
Decision Engine V3

Rule-based decision engine powered by S-Rank V2 and Performance Feed.
"""

import logging
from typing import Optional, List
from datetime import date

from jgod.decision_v3.models import DecisionV3Result, StrategyWeight, RiskPlan
from jgod.s_rank_v2.service import get_recommendation
from jgod.s_rank_v2.models import StabilityGrade

logger = logging.getLogger(__name__)


class DecisionEngineV3:
    """Decision Engine V3: Rule-based × S-Rank V2 × Performance Feed"""
    
    def __init__(self):
        """Initialize Decision Engine V3 (no complex dependencies)"""
        pass
    
    def decide(
        self,
        symbol: str,
        mode: str = "performance",
        limit: int = 60,
        k: int = 5,
        as_of_date: Optional[date] = None,
    ) -> DecisionV3Result:
        """
        Make decision for a symbol.
        
        Args:
            symbol: Stock symbol
            mode: "performance" (default) or "signals"
            limit: Number of timeline items to use
            k: Number of top strategies to recommend
            as_of_date: Optional date (defaults to today)
            
        Returns:
            DecisionV3Result
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # Step 1: Get recommendation from S-Rank V2
        try:
            snapshot = get_recommendation(symbol, limit, k, mode)
        except Exception as e:
            logger.warning(f"Failed to get recommendation for {symbol}, using empty result: {e}")
            # Return empty result with RISK_OFF
            return DecisionV3Result(
                symbol=symbol,
                as_of_date=as_of_date,
                risk_plan=RiskPlan(
                    position_scale=0.20,
                    risk_state="RISK_OFF",
                    reasons=["無法取得策略推薦資料"],
                ),
                confidence=0.0,
                explain=f"無法為 {symbol} 產生決策：系統無法取得策略推薦資料。建議檢查資料完整性。",
            )
        
        # Step 2: Extract primary and secondary strategies
        items = snapshot.items
        weights_dict = snapshot.weights
        metrics = snapshot.metrics
        rationale_dict = snapshot.rationale
        
        if not items or not metrics:
            # NO_DATA case
            return DecisionV3Result(
                symbol=symbol,
                as_of_date=as_of_date,
                risk_plan=RiskPlan(
                    position_scale=0.20,
                    risk_state="RISK_OFF",
                    reasons=["暫無預測資料"],
                ),
                confidence=0.0,
                explain=f"目前 {symbol} 暫無足夠的預測資料，無法產生決策建議。請等待更多資料點後再試。",
            )
        
        # Primary strategy: Top 1
        primary_strategy = items[0].strategy if items else None
        
        # Secondary strategies: Top 2-3 (max 2)
        secondary_strategies = [item.strategy for item in items[1:3]] if len(items) > 1 else []
        
        # Step 3: Build StrategyWeight list
        strategy_weights = []
        for item in items:
            # Try to get performance metrics if mode=performance
            perf_metrics = None
            grade = None
            
            if mode == "performance":
                # Try to get performance data (optional, may not exist)
                try:
                    from jgod.strategy_perf.service import get_performance
                    perf_snapshot = get_performance(symbol, limit, window=20)
                    perf_item = next(
                        (p for p in perf_snapshot.items if p.strategy_id == item.strategy),
                        None
                    )
                    if perf_item:
                        perf_metrics = {
                            "sharpe_proxy": perf_item.sharpe_proxy,
                            "max_drawdown_proxy": perf_item.max_drawdown_proxy,
                            "turnover_proxy": perf_item.turnover_proxy,
                            "decay_slope": perf_item.decay_slope,
                        }
                        grade = perf_item.grade.value
                except Exception:
                    pass  # Performance data not available, skip
            
            strategy_weights.append(
                StrategyWeight(
                    strategy_id=item.strategy,
                    weight=item.weight,
                    grade=grade,
                    metrics=perf_metrics,
                    rationale=rationale_dict.get(item.strategy),
                )
            )
        
        # Step 4: Calculate risk plan
        risk_plan = self._calculate_risk_plan(metrics, mode, snapshot, symbol)
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(metrics, items, weights_dict)
        
        # Step 6: Generate explanation
        explain = self._generate_explanation(
            symbol, mode, metrics, primary_strategy, secondary_strategies,
            items, risk_plan, confidence
        )
        
        return DecisionV3Result(
            symbol=symbol,
            as_of_date=as_of_date,
            selected_primary_strategy=primary_strategy,
            selected_secondary_strategies=secondary_strategies,
            weights=strategy_weights,
            risk_plan=risk_plan,
            confidence=confidence,
            explain=explain,
        )
    
    def _calculate_risk_plan(
        self,
        metrics,
        mode: str,
        snapshot,
        symbol: str,
    ) -> RiskPlan:
        """Calculate risk plan based on metrics"""
        reasons = []
        position_scale = 1.0
        
        # Base position scale from stability grade
        if metrics.stability_grade == StabilityGrade.VOLATILE:
            position_scale = 0.35
            risk_state = "CAUTION"
            reasons.append("預測穩定性為 VOLATILE，建議降低倉位")
        elif metrics.stability_grade == StabilityGrade.WATCH:
            position_scale = 0.55
            risk_state = "CAUTION"
            reasons.append("預測穩定性為 WATCH，建議謹慎操作")
        elif metrics.stability_grade == StabilityGrade.STABLE:
            position_scale = 0.80
            risk_state = "RISK_ON"
            reasons.append("預測穩定性為 STABLE，可正常操作")
        else:  # NO_DATA
            position_scale = 0.20
            risk_state = "RISK_OFF"
            reasons.append("暫無預測資料，建議暫停操作")
        
        # Additional adjustment from performance metrics (if mode=performance)
        if mode == "performance" and snapshot.items:
            try:
                from jgod.strategy_perf.service import get_performance
                perf_snapshot = get_performance(symbol, limit=60, window=20)
                
                # Check max drawdown across all strategies
                max_mdd = 0.0
                for perf_item in perf_snapshot.items:
                    if perf_item.max_drawdown_proxy > max_mdd:
                        max_mdd = perf_item.max_drawdown_proxy
                
                if max_mdd > 0.15:
                    position_scale *= 0.7
                    reasons.append("近期回撤偏高，進一步降低倉位")
            except Exception:
                pass  # Performance data not available, skip
        
        # Clamp position_scale to [0.05, 1.0]
        position_scale = max(0.05, min(1.0, position_scale))
        
        return RiskPlan(
            position_scale=round(position_scale, 2),
            risk_state=risk_state,
            reasons=reasons,
        )
    
    def _calculate_confidence(
        self,
        metrics,
        items,
        weights_dict: dict,
    ) -> float:
        """Calculate confidence score (0.0 ~ 1.0)"""
        base = 0.5
        
        # Stability grade adjustment
        if metrics.stability_grade == StabilityGrade.STABLE:
            base += 0.25
        elif metrics.stability_grade == StabilityGrade.WATCH:
            base += 0.1
        elif metrics.stability_grade == StabilityGrade.VOLATILE:
            base -= 0.15
        else:  # NO_DATA
            base -= 0.25
        
        # Top1 weight adjustment
        if items and items[0]:
            top1_weight = items[0].weight
            if top1_weight >= 0.45:
                base += 0.1
            elif top1_weight < 0.30:
                base -= 0.1
        
        # Clamp to [0.0, 1.0]
        confidence = max(0.0, min(1.0, base))
        return round(confidence, 2)
    
    def _generate_explanation(
        self,
        symbol: str,
        mode: str,
        metrics,
        primary_strategy: Optional[str],
        secondary_strategies: List[str],
        items,
        risk_plan: RiskPlan,
        confidence: float,
    ) -> str:
        """Generate explanation text (Traditional Chinese, <= 10 lines)"""
        lines = []
        
        # Line 1: Mode and symbol
        mode_text = "績效驅動模式" if mode == "performance" else "訊號驅動模式"
        lines.append(f"【{symbol} 決策摘要】使用 {mode_text}。")
        
        # Line 2: Stability grade
        stability_text = {
            StabilityGrade.STABLE: "穩定",
            StabilityGrade.WATCH: "觀察",
            StabilityGrade.VOLATILE: "波動",
            StabilityGrade.NO_DATA: "無資料",
        }.get(metrics.stability_grade, "未知")
        lines.append(f"預測穩定性：{stability_text}（{metrics.n_points} 個資料點）。")
        
        # Line 3-4: Primary strategy
        if primary_strategy:
            strategy_names = {
                "trend_follow": "趨勢跟隨",
                "mean_reversion": "均值回歸",
                "breakout": "突破",
                "risk_off": "風險規避",
                "momentum": "動量",
            }
            primary_name = strategy_names.get(primary_strategy, primary_strategy)
            primary_weight = items[0].weight if items else 0.0
            lines.append(f"主要策略：{primary_name}（權重 {primary_weight:.1%}）。")
            
            if secondary_strategies:
                sec_names = [strategy_names.get(s, s) for s in secondary_strategies]
                lines.append(f"輔助策略：{', '.join(sec_names)}。")
        
        # Line 5-6: Risk plan
        risk_state_text = {
            "RISK_ON": "正常操作",
            "CAUTION": "謹慎操作",
            "RISK_OFF": "暫停操作",
        }.get(risk_plan.risk_state, risk_plan.risk_state)
        lines.append(f"風險狀態：{risk_state_text}，建議倉位縮放：{risk_plan.position_scale:.0%}。")
        
        if risk_plan.reasons:
            lines.append(f"風險理由：{'; '.join(risk_plan.reasons[:2])}。")
        
        # Line 7: Confidence
        lines.append(f"決策信心度：{confidence:.0%}。")
        
        # Ensure <= 10 lines
        return "\n".join(lines[:10])

