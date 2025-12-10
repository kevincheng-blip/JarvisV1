"""Decision Layer V2 - Decision Engine

Enhanced decision engine with S-Rank weighting, conflict adjustment, and Doctrine alert integration.
"""

import logging
from typing import List, Optional, Dict
from datetime import date

from jgod.decision.models import (
    RawScoreItem,
    DecisionOutput,
    DecisionBatchResult,
    DecisionContextV2,
    DoctrineFlag,
)
from jgod.decision.policy_v2 import calculate_final_score_v2
from jgod.s_rank_engine.storage import SRankFactorStorageV1

logger = logging.getLogger(__name__)


class DecisionEngineV2:
    """Decision Layer V2 - Enhanced decision engine"""
    
    def __init__(
        self,
        knowledge_brain=None,
        s_rank_storage: Optional[SRankFactorStorageV1] = None,
    ):
        """
        Initialize Decision Engine V2
        
        Args:
            knowledge_brain: KnowledgeBrain instance (optional, for Doctrine queries)
            s_rank_storage: SRankFactorStorageV1 instance (optional, for S-Rank factors)
        """
        self.knowledge_brain = knowledge_brain
        self.s_rank_storage = s_rank_storage or SRankFactorStorageV1()
        
        # Cache for S-Rank factors
        self._s_rank_cache: Optional[Dict[str, float]] = None
        
        logger.info("DecisionEngineV2 initialized")
    
    def _load_s_rank_factors(self) -> Dict[str, float]:
        """
        Load latest S-Rank factors and cache them.
        
        Returns:
            Dict mapping strategy_id to s_rank_score
        """
        if self._s_rank_cache is not None:
            return self._s_rank_cache
        
        try:
            factors = self.s_rank_storage.load_latest_factors()
            self._s_rank_cache = {
                factor.strategy_id: factor.s_rank_score
                for factor in factors
            }
            logger.debug(f"Loaded {len(self._s_rank_cache)} S-Rank factors")
        except Exception as e:
            logger.warning(f"Failed to load S-Rank factors: {e}")
            self._s_rank_cache = {}
        
        return self._s_rank_cache
    
    def _gather_v2_context(
        self,
        raw_item: RawScoreItem,
    ) -> DecisionContextV2:
        """
        Gather V2 decision context for a raw score item.
        
        Steps:
        1. Extract strategy scores from raw_item.strategy_scores
        2. Load S-Rank factors
        3. Load conflict summary (if available)
        4. Load Doctrine alerts (if available)
        
        Args:
            raw_item: Raw score item
        
        Returns:
            DecisionContextV2
        """
        # Step 1: Extract strategy scores
        raw_scores = raw_item.strategy_scores.copy() if raw_item.strategy_scores else {}
        
        # If no strategy_scores, use raw_score as single strategy
        if not raw_scores:
            raw_scores = {"DEFAULT": raw_item.raw_score}
        
        # Step 2: Load S-Rank factors
        s_rank_factors = self._load_s_rank_factors()
        
        # Step 3: Load conflict summary (if available)
        conflict_summary = None
        try:
            from jgod.signal_aggregation.data_access import get_strategy_votes_for_date
            votes_data = get_strategy_votes_for_date(raw_item.date, [raw_item.symbol])
            if votes_data and len(votes_data) > 0:
                vote_row = votes_data[0]
                if vote_row.strategy_votes:
                    from jgod.signal_aggregation.engine import SignalAggregationEngineV1
                    engine = SignalAggregationEngineV1()
                    conflict_score, majority = engine._compute_conflict_score(
                        list(vote_row.strategy_votes.values())
                    )
                    consensus_score = engine._compute_consensus_score(
                        list(vote_row.strategy_votes.values())
                    )
                    conflict_summary = {
                        "conflict_score": conflict_score,
                        "consensus_score": consensus_score,
                        "majority_vote": majority,
                    }
        except Exception as e:
            logger.debug(f"Failed to load conflict summary for {raw_item.symbol}: {e}")
        
        # Step 4: Load Doctrine alerts (if available)
        doctrine_alerts = []
        try:
            from jgod.doctrine_alert.engine import DoctrineAlertEngineV1
            from jgod.doctrine_alert.config import DoctrineAlertConfig
            alert_config = DoctrineAlertConfig()
            alert_engine = DoctrineAlertEngineV1(config=alert_config)
            symbol_alerts = alert_engine.scan_symbol(raw_item.symbol)
            
            # Convert DoctrineAlertItem to DoctrineFlag
            for alert in symbol_alerts:
                # Extract doctrine_refs safely
                doctrine_refs_list = []
                if hasattr(alert, "doctrine_refs") and alert.doctrine_refs:
                    for ref in alert.doctrine_refs:
                        if isinstance(ref, str):
                            doctrine_refs_list.append(ref)
                        elif hasattr(ref, "model_dump"):
                            doctrine_refs_list.append(str(ref.model_dump()))
                        else:
                            doctrine_refs_list.append(str(ref))
                
                flag = DoctrineFlag(
                    code=alert.id.split("_")[0] if "_" in alert.id else alert.id,
                    severity=alert.severity.value.lower() if hasattr(alert.severity, "value") else str(alert.severity).lower(),
                    message=alert.message,
                    doctrine_refs=doctrine_refs_list,
                )
                doctrine_alerts.append(flag)
        except Exception as e:
            logger.debug(f"Failed to load Doctrine alerts for {raw_item.symbol}: {e}")
        
        return DecisionContextV2(
            symbol=raw_item.symbol,
            raw_scores=raw_scores,
            s_rank_factors=s_rank_factors if s_rank_factors else None,
            conflict_summary=conflict_summary,
            doctrine_alerts=doctrine_alerts,
            risk_metrics=raw_item.risk_metrics.copy() if raw_item.risk_metrics else {},
            context_tags=raw_item.context_tags.copy() if raw_item.context_tags else [],
        )
    
    def decide_for_single(self, raw_item: RawScoreItem) -> DecisionOutput:
        """
        Process single raw score item using V2 logic.
        
        Args:
            raw_item: Raw score item
        
        Returns:
            DecisionOutput
        """
        try:
            # Gather V2 context
            context = self._gather_v2_context(raw_item)
            
            # Calculate final score using V2 policy
            final_score, doctrine_flags, adjustment_reason = calculate_final_score_v2(context)
            
            # Calculate correction factor
            if raw_item.raw_score != 0:
                correction_factor = final_score / raw_item.raw_score
            else:
                correction_factor = 1.0
            
            return DecisionOutput(
                symbol=raw_item.symbol,
                date=raw_item.date,
                raw_score=raw_item.raw_score,
                final_score=final_score,
                correction_factor=correction_factor,
                doctrine_flags=doctrine_flags,
                adjustment_reason=adjustment_reason,
                llm_model="v2_policy",
            )
            
        except Exception as e:
            logger.error(f"Error processing {raw_item.symbol} in V2: {e}", exc_info=True)
            # Fallback to raw_score
            return DecisionOutput(
                symbol=raw_item.symbol,
                date=raw_item.date,
                raw_score=raw_item.raw_score,
                final_score=raw_item.raw_score,
                correction_factor=1.0,
                doctrine_flags=[],
                adjustment_reason=f"V2 processing error: {str(e)}",
                llm_model="v2_fallback",
            )
    
    def decide_for_batch(self, raw_items: List[RawScoreItem]) -> DecisionBatchResult:
        """
        Process batch of raw score items using V2 logic.
        
        Args:
            raw_items: List of raw score items
        
        Returns:
            DecisionBatchResult
        """
        logger.info(f"Processing batch of {len(raw_items)} items with V2")
        
        results = []
        for raw_item in raw_items:
            try:
                output = self.decide_for_single(raw_item)
                results.append(output)
            except Exception as e:
                logger.error(f"Error processing {raw_item.symbol}: {e}", exc_info=True)
                # Fallback output
                fallback_output = DecisionOutput(
                    symbol=raw_item.symbol,
                    date=raw_item.date,
                    raw_score=raw_item.raw_score,
                    final_score=raw_item.raw_score,
                    correction_factor=1.0,
                    doctrine_flags=[],
                    adjustment_reason=f"Batch processing error: {str(e)}",
                    llm_model="v2_fallback",
                )
                results.append(fallback_output)
        
        if results:
            result_date = results[0].date
        else:
            result_date = date.today()
        
        return DecisionBatchResult(date=result_date, items=results)

