"""S-Rank Factor Storage

JSONL-based storage for S-Rank factors.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import date

from jgod.s_rank_engine.models import SRankFactor, StrategyPerformanceSnapshot, SignalQualityFactors
from jgod.s_rank_engine.config import S_RANK_REPORTS_PATH

logger = logging.getLogger(__name__)


class SRankFactorStorageV1:
    """Storage for S-Rank factors"""
    
    def __init__(self, path: Optional[Path] = None):
        """
        Initialize storage
        
        Args:
            path: Path to JSONL file (default: config.S_RANK_REPORTS_PATH)
        """
        self.path = path or S_RANK_REPORTS_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"SRankFactorStorageV1 initialized at: {self.path}")
    
    def _factor_to_dict(self, factor: SRankFactor) -> dict:
        """Convert SRankFactor to dict for JSON serialization"""
        return {
            "strategy_id": factor.strategy_id,
            "performance_snapshot": {
                "strategy_id": factor.performance_snapshot.strategy_id,
                "sharpe_ratio": factor.performance_snapshot.sharpe_ratio,
                "max_drawdown": factor.performance_snapshot.max_drawdown,
                "total_return": factor.performance_snapshot.total_return,
                "avg_holding_period_days": factor.performance_snapshot.avg_holding_period_days,
                "last_run_date": factor.performance_snapshot.last_run_date.isoformat(),
                "is_active": factor.performance_snapshot.is_active,
                "market_correlation": factor.performance_snapshot.market_correlation,
            },
            "quality_factors": {
                "signal_strength_confidence": factor.quality_factors.signal_strength_confidence,
                "factor_decay_rate": factor.quality_factors.factor_decay_rate,
                "consistency_score": factor.quality_factors.consistency_score,
            },
            "s_rank_score": factor.s_rank_score,
            "rank_level": factor.rank_level,
            "calculated_at": factor.calculated_at.isoformat(),
        }
    
    def _dict_to_factor(self, data: dict) -> SRankFactor:
        """Convert dict to SRankFactor"""
        from datetime import datetime
        
        perf_data = data["performance_snapshot"]
        quality_data = data["quality_factors"]
        
        performance_snapshot = StrategyPerformanceSnapshot(
            strategy_id=perf_data["strategy_id"],
            sharpe_ratio=perf_data["sharpe_ratio"],
            max_drawdown=perf_data["max_drawdown"],
            total_return=perf_data["total_return"],
            avg_holding_period_days=perf_data["avg_holding_period_days"],
            last_run_date=date.fromisoformat(perf_data["last_run_date"]),
            is_active=perf_data.get("is_active", True),
            market_correlation=perf_data.get("market_correlation", 0.0),
        )
        
        quality_factors = SignalQualityFactors(
            signal_strength_confidence=quality_data["signal_strength_confidence"],
            factor_decay_rate=quality_data["factor_decay_rate"],
            consistency_score=quality_data["consistency_score"],
        )
        
        return SRankFactor(
            strategy_id=data["strategy_id"],
            performance_snapshot=performance_snapshot,
            quality_factors=quality_factors,
            s_rank_score=data["s_rank_score"],
            rank_level=data["rank_level"],
            calculated_at=datetime.fromisoformat(data["calculated_at"]),
        )
    
    def save_factors(self, factors: List[SRankFactor]) -> None:
        """
        Save S-Rank factors to JSONL
        
        Args:
            factors: List of SRankFactor to save
        """
        try:
            # For v1, append to file (can be enhanced to deduplicate by date)
            with open(self.path, "a", encoding="utf-8") as f:
                for factor in factors:
                    f.write(json.dumps(self._factor_to_dict(factor), ensure_ascii=False) + "\n")
            logger.info(f"Saved {len(factors)} S-Rank factors to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save factors: {e}", exc_info=True)
            raise
    
    def load_latest_factors(self) -> List[SRankFactor]:
        """
        Load latest S-Rank factors (most recent calculation)
        
        Returns:
            List of SRankFactor from latest calculation
        """
        if not self.path.exists():
            return []
        
        factors: List[SRankFactor] = []
        try:
            # Read all lines and group by calculated_at date
            with open(self.path, "r", encoding="utf-8") as f:
                all_factors = []
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            factor = self._dict_to_factor(data)
                            all_factors.append(factor)
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.warning(f"Skipping invalid JSON line: {e}")
                            continue
            
            if not all_factors:
                return []
            
            # Get latest calculation date
            latest_date = max(f.calculated_at.date() for f in all_factors)
            
            # Filter factors from latest date
            factors = [f for f in all_factors if f.calculated_at.date() == latest_date]
            
            logger.info(f"Loaded {len(factors)} latest S-Rank factors from {latest_date}")
            return factors
            
        except Exception as e:
            logger.error(f"Failed to load latest factors: {e}", exc_info=True)
            return []
    
    def load_historical_factors(self, target_date: date) -> List[SRankFactor]:
        """
        Load historical S-Rank factors for a specific date
        
        Args:
            target_date: Target date to load factors for
        
        Returns:
            List of SRankFactor for the target date, empty if not found
        """
        if not self.path.exists():
            return []
        
        factors: List[SRankFactor] = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            factor = self._dict_to_factor(data)
                            if factor.calculated_at.date() == target_date:
                                factors.append(factor)
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.warning(f"Skipping invalid JSON line: {e}")
                            continue
            
            logger.info(f"Loaded {len(factors)} historical factors for {target_date}")
            return factors
            
        except Exception as e:
            logger.error(f"Failed to load historical factors: {e}", exc_info=True)
            return []
    
    def load_all(self) -> List[SRankFactor]:
        """
        Load all S-Rank factors from storage
        
        Returns:
            List of all SRankFactor objects
        """
        if not self.path.exists():
            return []
        
        factors: List[SRankFactor] = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            factor = self._dict_to_factor(data)
                            factors.append(factor)
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.warning(f"Skipping invalid JSON line: {e}")
                            continue
            
            logger.debug(f"Loaded {len(factors)} total S-Rank factors")
            return factors
            
        except Exception as e:
            logger.error(f"Failed to load all factors: {e}", exc_info=True)
            return []

