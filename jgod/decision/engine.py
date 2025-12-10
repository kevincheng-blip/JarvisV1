"""
Decision Layer v1/v2 - Decision Engine

核心決策引擎，負責 Raw Score → Final Score 轉換
支援 v1 (LLM-based) 和 v2 (S-Rank weighted) 兩種模式
"""

import logging
from typing import List, Optional, Literal

from jgod.decision.models import (
    RawScoreItem,
    DecisionOutput,
    DecisionBatchResult,
    DecisionContext,
    DoctrineFlag,
    LlmDecisionResponse
)
from jgod.decision.config import DecisionConfig
from jgod.decision.prompt_builder import build_decision_prompt
from jgod.decision.llm_client import DecisionLlmWrapper

logger = logging.getLogger(__name__)


class DecisionEngineV1:
    """Decision Layer v1 核心引擎"""
    
    def __init__(self, config: DecisionConfig, knowledge_brain):
        """
        Args:
            config: Decision Layer 配置
            knowledge_brain: KnowledgeBrain 實例（用於查詢 Doctrine）
        """
        self.config = config
        self.knowledge_brain = knowledge_brain
        self.llm_wrapper = DecisionLlmWrapper(config)
        
        logger.info(f"DecisionEngineV1 initialized: enable_llm={config.enable_llm}, enable_doctrine={config.enable_doctrine}")
    
    def decide_for_batch(self, raw_items: List[RawScoreItem]) -> DecisionBatchResult:
        """批次處理 Raw Scores
        
        Args:
            raw_items: Raw Score 項目列表
        
        Returns:
            DecisionBatchResult 包含所有決策結果
        """
        logger.info(f"Processing batch of {len(raw_items)} items")
        
        results = []
        for raw_item in raw_items:
            try:
                output = self.decide_for_single(raw_item)
                results.append(output)
            except Exception as e:
                logger.error(f"Error processing {raw_item.symbol}: {e}", exc_info=True)
                # 建立 fallback output
                fallback_output = DecisionOutput(
                    symbol=raw_item.symbol,
                    date=raw_item.date,
                    raw_score=raw_item.raw_score,
                    final_score=raw_item.raw_score * self.config.fallback_correction_factor,
                    correction_factor=self.config.fallback_correction_factor,
                    adjustment_reason=f"Error during processing: {str(e)}",
                    llm_model="fallback"
                )
                results.append(fallback_output)
        
        if results:
            result_date = results[0].date
        else:
            from datetime import date
            result_date = date.today()
        
        return DecisionBatchResult(date=result_date, items=results)
    
    def decide_for_single(self, raw_item: RawScoreItem) -> DecisionOutput:
        """處理單一 Raw Score 項目
        
        Args:
            raw_item: Raw Score 項目
        
        Returns:
            DecisionOutput 決策結果
        """
        # 1. 建立決策上下文
        context = self._build_context(raw_item)
        
        # 2. 查詢 Doctrine（如果啟用）
        if self.config.enable_doctrine and self.knowledge_brain:
            context.doctrine_hits = self._query_doctrine(raw_item)
            logger.debug(f"Found {len(context.doctrine_hits)} Doctrine hits for {raw_item.symbol}")
        else:
            context.doctrine_hits = []
            logger.debug(f"Doctrine disabled or knowledge_brain not available for {raw_item.symbol}")
        
        # 3. 呼叫 LLM（如果啟用）
        llm_response: Optional[LlmDecisionResponse] = None
        if self.config.enable_llm:
            prompt = build_decision_prompt(raw_item, context.doctrine_hits)
            llm_response = self.llm_wrapper.call_llm(prompt)
            
            if llm_response is None:
                logger.warning(f"LLM call failed for {raw_item.symbol}, using fallback")
        
        # 4. 套用修正
        output = self._apply_correction(raw_item, llm_response)
        
        return output
    
    def _build_context(self, raw_item: RawScoreItem) -> DecisionContext:
        """建立決策上下文"""
        # 組合查詢字串
        query_parts = [
            raw_item.symbol,
            f"raw_score {raw_item.raw_score:.2f}",
        ]
        
        # 加入風險指標關鍵字
        if raw_item.risk_metrics:
            if "vol" in str(raw_item.risk_metrics).lower():
                query_parts.append("high volatility")
            if "liquidity" in str(raw_item.risk_metrics).lower():
                query_parts.append("low liquidity")
            if any(v < 0 for v in raw_item.risk_metrics.values()):
                query_parts.append("negative metrics")
        
        # 加入上下文標籤
        query_parts.extend(raw_item.context_tags)
        
        query_string = ", ".join(query_parts)
        
        return DecisionContext(
            raw_item=raw_item,
            query_string=query_string
        )
    
    def _query_doctrine(self, raw_item: RawScoreItem) -> List[any]:
        """查詢 Doctrine 條文
        
        Returns:
            DoctrineHit 列表
        """
        if not self.knowledge_brain:
            logger.warning("KnowledgeBrain not available for Doctrine query")
            return []
        
        try:
            # 使用 KnowledgeBrain 的 search_doctrine 方法
            context = self._build_context(raw_item)
            doctrine_hits = self.knowledge_brain.search_doctrine(
                query=context.query_string,
                top_k=self.config.doctrine_top_k
            )
            
            if not doctrine_hits:
                logger.debug(f"No Doctrine hits found for query: {context.query_string}")
            
            return doctrine_hits
        
        except Exception as e:
            logger.error(f"Error querying Doctrine: {e}", exc_info=True)
            return []
    
    def _apply_correction(
        self,
        raw_item: RawScoreItem,
        llm_response: Optional[LlmDecisionResponse]
    ) -> DecisionOutput:
        """套用 LLM 決策到 Raw Score
        
        Args:
            raw_item: Raw Score 項目
            llm_response: LLM 回應（可能為 None）
        
        Returns:
            DecisionOutput 決策結果
        """
        # 決定 correction_factor
        if llm_response:
            correction_factor = llm_response.correction_factor
            adjustment_reason = llm_response.adjustment_reason
            llm_model = self.config.llm_model
            
            # 轉換 doctrine_flags
            doctrine_flags = []
            for flag_dict in llm_response.doctrine_flags:
                try:
                    flag = DoctrineFlag(
                        code=flag_dict.get("code", "unknown"),
                        severity=flag_dict.get("severity", "info"),
                        message=flag_dict.get("message", ""),
                        doctrine_refs=flag_dict.get("doctrine_refs", [])
                    )
                    doctrine_flags.append(flag)
                except Exception as e:
                    logger.warning(f"Failed to parse doctrine_flag: {flag_dict}, error: {e}")
            
        else:
            # Fallback：不修正
            correction_factor = self.config.fallback_correction_factor
            adjustment_reason = "LLM unavailable or disabled, no adjustment applied."
            doctrine_flags = []
            llm_model = "fallback"
        
        # Clip correction_factor 到安全範圍
        original_factor = correction_factor
        correction_factor = max(
            self.config.min_correction,
            min(correction_factor, self.config.max_correction)
        )
        
        if original_factor != correction_factor:
            logger.warning(
                f"Correction factor clipped for {raw_item.symbol}: "
                f"{original_factor:.3f} -> {correction_factor:.3f}"
            )
            adjustment_reason += f" (correction_factor clipped to safety bounds: {self.config.min_correction} ~ {self.config.max_correction})"
        
        # 計算 final_score
        final_score = raw_item.raw_score * correction_factor
        
        # 確保 final_score 在合理範圍（假設 raw_score 在 [0, 1]）
        final_score = max(0.0, min(final_score, 2.0))  # 允許略超過 1.0
        
        return DecisionOutput(
            symbol=raw_item.symbol,
            date=raw_item.date,
            raw_score=raw_item.raw_score,
            final_score=final_score,
            correction_factor=correction_factor,
            doctrine_flags=doctrine_flags,
            adjustment_reason=adjustment_reason,
            llm_model=llm_model
        )

