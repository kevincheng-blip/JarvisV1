"""S-Rank Factor Engine

Core engine for calculating S-Rank scores for strategies.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List

from jgod.s_rank_engine.models import (
    StrategyPerformanceSnapshot,
    SignalQualityFactors,
    SRankFactor,
)
from jgod.s_rank_engine.config import (
    DEFAULT_TIME_HORIZON_DAYS,
    S_RANK_WEIGHTS,
    RANK_THRESHOLDS,
)
from jgod.s_rank_engine.storage import SRankFactorStorageV1

logger = logging.getLogger(__name__)


class SRankEngineV1:
    """S-Rank Factor Engine v1"""
    
    def __init__(self, storage: SRankFactorStorageV1 = None):
        """
        Initialize S-Rank engine
        
        Args:
            storage: Storage instance (optional)
        """
        self.storage = storage or SRankFactorStorageV1()
        logger.info("SRankEngineV1 initialized")
    
    def _load_strategy_performance(self, time_horizon_days: int) -> List[StrategyPerformanceSnapshot]:
        """
        Load strategy performance data.
        
        For v1, this is a simplified implementation that uses mock data.
        Future versions will integrate with actual backtest/policy logs.
        
        Args:
            time_horizon_days: Time horizon for evaluation
        
        Returns:
            List of StrategyPerformanceSnapshot
        """
        # TODO: Integrate with actual PathA backtest results or policy logs
        # For v1, return mock data for demonstration
        logger.info(f"Loading strategy performance for {time_horizon_days} days")
        
        # Mock data - in production, this would query from:
        # - PathA backtest results
        # - Policy experiment logs
        # - Strategy signal performance tracking
        
        end_date = date.today()
        start_date = end_date - timedelta(days=time_horizon_days)
        
        mock_snapshots = [
            StrategyPerformanceSnapshot(
                strategy_id="S1",
                sharpe_ratio=1.8,
                max_drawdown=0.12,
                total_return=0.25,
                avg_holding_period_days=5,
                last_run_date=end_date,
                is_active=True,
                market_correlation=0.65,
            ),
            StrategyPerformanceSnapshot(
                strategy_id="S2",
                sharpe_ratio=1.5,
                max_drawdown=0.15,
                total_return=0.20,
                avg_holding_period_days=7,
                last_run_date=end_date,
                is_active=True,
                market_correlation=0.70,
            ),
            StrategyPerformanceSnapshot(
                strategy_id="S3",
                sharpe_ratio=1.2,
                max_drawdown=0.18,
                total_return=0.15,
                avg_holding_period_days=10,
                last_run_date=end_date,
                is_active=True,
                market_correlation=0.55,
            ),
            StrategyPerformanceSnapshot(
                strategy_id="S4",
                sharpe_ratio=0.9,
                max_drawdown=0.22,
                total_return=0.10,
                avg_holding_period_days=12,
                last_run_date=end_date,
                is_active=True,
                market_correlation=0.60,
            ),
            StrategyPerformanceSnapshot(
                strategy_id="S5",
                sharpe_ratio=0.6,
                max_drawdown=0.30,
                total_return=0.05,
                avg_holding_period_days=15,
                last_run_date=end_date,
                is_active=True,
                market_correlation=0.50,
            ),
        ]
        
        logger.info(f"Loaded {len(mock_snapshots)} strategy performance snapshots")
        return mock_snapshots
    
    def _calculate_quality_factors(self, snapshot: StrategyPerformanceSnapshot) -> SignalQualityFactors:
        """
        Calculate signal quality factors for a strategy.
        
        For v1, uses simplified heuristics based on performance metrics.
        Future versions will use actual signal tracking data.
        
        Args:
            snapshot: Performance snapshot
        
        Returns:
            SignalQualityFactors
        """
        # TODO: Integrate with actual signal tracking
        # For v1, derive from performance metrics
        
        # Signal strength confidence: based on Sharpe ratio (normalized)
        signal_strength_confidence = min(max(snapshot.sharpe_ratio / 2.0, 0.0), 1.0)
        
        # Factor decay rate: inversely related to consistency (higher Sharpe = lower decay)
        factor_decay_rate = max(0.1, 1.0 - (snapshot.sharpe_ratio / 3.0))
        
        # Consistency score: based on drawdown and correlation
        # Lower drawdown and moderate correlation = higher consistency
        consistency_score = (1.0 - snapshot.max_drawdown) * (1.0 - abs(snapshot.market_correlation - 0.6))
        consistency_score = max(0.0, min(1.0, consistency_score))
        
        return SignalQualityFactors(
            signal_strength_confidence=signal_strength_confidence,
            factor_decay_rate=factor_decay_rate,
            consistency_score=consistency_score,
        )
    
    def _normalize_metrics(self, snapshots: List[StrategyPerformanceSnapshot], quality_factors_list: List[SignalQualityFactors]) -> dict:
        """
        Normalize all metrics to 0-1 range.
        
        Args:
            snapshots: List of performance snapshots
            quality_factors_list: List of quality factors
        
        Returns:
            Dictionary with normalized metrics for each strategy
        """
        # Extract raw values
        sharpe_values = [s.sharpe_ratio for s in snapshots]
        maxdd_values = [s.max_drawdown for s in snapshots if s.max_drawdown > 0]
        consistency_values = [q.consistency_score for q in quality_factors_list]
        decay_values = [q.factor_decay_rate for q in quality_factors_list if q.factor_decay_rate > 0]
        
        # Normalize Sharpe ratio
        sharpe_min = min(sharpe_values) if sharpe_values else 0.0
        sharpe_max = max(sharpe_values) if sharpe_values else 1.0
        sharpe_range = sharpe_max - sharpe_min if sharpe_max > sharpe_min else 1.0
        
        # Normalize inverse MaxDD (higher is better)
        inv_maxdd_values = [1.0 / md if md > 0 else 0.0 for md in maxdd_values]
        inv_maxdd_min = min(inv_maxdd_values) if inv_maxdd_values else 0.0
        inv_maxdd_max = max(inv_maxdd_values) if inv_maxdd_values else 1.0
        inv_maxdd_range = inv_maxdd_max - inv_maxdd_min if inv_maxdd_max > inv_maxdd_min else 1.0
        
        # Normalize consistency
        consistency_min = min(consistency_values) if consistency_values else 0.0
        consistency_max = max(consistency_values) if consistency_values else 1.0
        consistency_range = consistency_max - consistency_min if consistency_max > consistency_min else 1.0
        
        # Normalize inverse decay (higher is better)
        inv_decay_values = [1.0 / d if d > 0 else 0.0 for d in decay_values]
        inv_decay_min = min(inv_decay_values) if inv_decay_values else 0.0
        inv_decay_max = max(inv_decay_values) if inv_decay_values else 1.0
        inv_decay_range = inv_decay_max - inv_decay_min if inv_decay_max > inv_decay_min else 1.0
        
        # Build normalized metrics for each strategy
        normalized = {}
        for i, (snapshot, quality) in enumerate(zip(snapshots, quality_factors_list)):
            norm_sharpe = (snapshot.sharpe_ratio - sharpe_min) / sharpe_range if sharpe_range > 0 else 0.5
            norm_inv_maxdd = (1.0 / snapshot.max_drawdown - inv_maxdd_min) / inv_maxdd_range if snapshot.max_drawdown > 0 and inv_maxdd_range > 0 else 0.5
            norm_consistency = (quality.consistency_score - consistency_min) / consistency_range if consistency_range > 0 else 0.5
            norm_inv_decay = (1.0 / quality.factor_decay_rate - inv_decay_min) / inv_decay_range if quality.factor_decay_rate > 0 and inv_decay_range > 0 else 0.5
            
            normalized[snapshot.strategy_id] = {
                "sharpe_ratio": norm_sharpe,
                "inv_max_drawdown": norm_inv_maxdd,
                "consistency_score": norm_consistency,
                "inv_factor_decay": norm_inv_decay,
            }
        
        return normalized
    
    def _calculate_rank_level(self, s_rank_score: float) -> str:
        """
        Determine rank level based on S-Rank score.
        
        Args:
            s_rank_score: Calculated S-Rank score (0.0-1.0)
        
        Returns:
            Rank level: "S" | "A" | "B" | "C" | "D"
        """
        if s_rank_score > RANK_THRESHOLDS["S"]:
            return "S"
        elif s_rank_score > RANK_THRESHOLDS["A"]:
            return "A"
        elif s_rank_score > RANK_THRESHOLDS["B"]:
            return "B"
        elif s_rank_score > RANK_THRESHOLDS["C"]:
            return "C"
        else:
            return "D"
    
    def calculate(self, time_horizon_days: int = DEFAULT_TIME_HORIZON_DAYS) -> List[SRankFactor]:
        """
        Calculate S-Rank factors for all strategies.
        
        Steps:
        1. Load strategy performance data
        2. Calculate quality factors
        3. Normalize metrics
        4. Calculate S-Rank scores
        5. Determine rank levels
        6. Save to storage
        
        Args:
            time_horizon_days: Time horizon for evaluation
        
        Returns:
            List of SRankFactor
        """
        logger.info(f"Starting S-Rank calculation for {time_horizon_days} days")
        
        # Step 1: Load performance data
        snapshots = self._load_strategy_performance(time_horizon_days)
        if not snapshots:
            logger.warning("No strategy performance data found")
            return []
        
        # Step 2: Calculate quality factors
        quality_factors_list = [self._calculate_quality_factors(s) for s in snapshots]
        
        # Step 3: Normalize metrics
        normalized = self._normalize_metrics(snapshots, quality_factors_list)
        
        # Step 4 & 5: Calculate S-Rank scores and rank levels
        factors = []
        for snapshot, quality in zip(snapshots, quality_factors_list):
            norm_metrics = normalized[snapshot.strategy_id]
            
            # Calculate weighted score
            s_rank_score = (
                norm_metrics["sharpe_ratio"] * S_RANK_WEIGHTS["sharpe_ratio"] +
                norm_metrics["inv_max_drawdown"] * S_RANK_WEIGHTS["inv_max_drawdown"] +
                norm_metrics["consistency_score"] * S_RANK_WEIGHTS["consistency_score"] +
                norm_metrics["inv_factor_decay"] * S_RANK_WEIGHTS["inv_factor_decay"]
            )
            
            # Clamp to [0, 1]
            s_rank_score = max(0.0, min(1.0, s_rank_score))
            
            # Determine rank level
            rank_level = self._calculate_rank_level(s_rank_score)
            
            factor = SRankFactor(
                strategy_id=snapshot.strategy_id,
                performance_snapshot=snapshot,
                quality_factors=quality,
                s_rank_score=s_rank_score,
                rank_level=rank_level,
                calculated_at=datetime.now(),
            )
            factors.append(factor)
            
            logger.debug(
                f"Strategy {snapshot.strategy_id}: score={s_rank_score:.3f}, rank={rank_level}, "
                f"sharpe={snapshot.sharpe_ratio:.2f}, maxdd={snapshot.max_drawdown:.2%}"
            )
        
        # Sort by score descending
        factors.sort(key=lambda x: x.s_rank_score, reverse=True)
        
        # Step 6: Save to storage
        self.storage.save_factors(factors)
        logger.info(f"S-Rank calculation complete: {len(factors)} strategies ranked")
        
        return factors

