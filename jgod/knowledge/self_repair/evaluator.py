"""Proposal Evaluator

Evaluates fix proposals for quality and confidence using LLM.
"""

import logging
from typing import List, Optional, Protocol

from jgod.knowledge.self_repair.models import FixProposal

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM provider"""
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        ...


class ProposalEvaluator:
    """Evaluates fix proposals for quality"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        Initialize evaluator
        
        Args:
            llm_provider: LLM provider for evaluation
        """
        self.llm_provider = llm_provider
    
    def evaluate_proposals(self, proposals: List[FixProposal]) -> List[FixProposal]:
        """
        Evaluate proposals and assign confidence scores.
        
        Args:
            proposals: List of FixProposal objects to evaluate
        
        Returns:
            List of FixProposal objects with updated scores
        """
        logger.info(f"Evaluating {len(proposals)} proposals")
        
        evaluated = []
        
        for proposal in proposals:
            evaluated_proposal = self._evaluate_single_proposal(proposal)
            if evaluated_proposal:
                evaluated.append(evaluated_proposal)
            else:
                # If evaluation fails, keep original with low confidence
                proposal.confidence = 0.3
                evaluated.append(proposal)
        
        logger.info(f"Evaluated {len(evaluated)} proposals")
        return evaluated
    
    def _evaluate_single_proposal(self, proposal: FixProposal) -> Optional[FixProposal]:
        """Evaluate a single proposal"""
        if not self.llm_provider:
            logger.warning("LLM provider not available, using default confidence")
            proposal.confidence = 0.5
            return proposal
        
        system_prompt = """你是一個交易規則評估專家。請評估一個修復建議的品質，並給出數值評分。

請從以下四個維度評分（0.0 - 1.0）：
1. clarity_score: 清晰度（是否具體、易懂）
2. logical_score: 邏輯一致性（是否合理、無矛盾）
3. impact_score: 正向影響（是否能解決問題、帶來價值）
4. doctrine_alignment_score: 是否符合整體 Doctrine 哲學

最後給出整體 confidence（0.0 - 1.0），應綜合考慮所有分數。

回覆格式（必須嚴格遵守）：
CLARITY: [0.0-1.0]
LOGICAL: [0.0-1.0]
IMPACT: [0.0-1.0]
ALIGNMENT: [0.0-1.0]
CONFIDENCE: [0.0-1.0]
"""
        
        user_prompt = f"""請評估以下修復建議：

問題描述：
{proposal.justification}

建議修正：
{proposal.proposed_text[:500]}

影響說明：
{proposal.impact}

請給出評分。"""
        
        try:
            response = self.llm_provider.ask(system_prompt, user_prompt)
            
            # Parse scores
            clarity = 0.0
            logical = 0.0
            impact_score = 0.0
            alignment = 0.0
            confidence = 0.5  # Default
            
            for line in response.split("\n"):
                line = line.strip().upper()
                if line.startswith("CLARITY:"):
                    try:
                        clarity = float(line.replace("CLARITY:", "").strip())
                    except ValueError:
                        pass
                elif line.startswith("LOGICAL:"):
                    try:
                        logical = float(line.replace("LOGICAL:", "").strip())
                    except ValueError:
                        pass
                elif line.startswith("IMPACT:"):
                    try:
                        impact_score = float(line.replace("IMPACT:", "").strip())
                    except ValueError:
                        pass
                elif line.startswith("ALIGNMENT:"):
                    try:
                        alignment = float(line.replace("ALIGNMENT:", "").strip())
                    except ValueError:
                        pass
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.replace("CONFIDENCE:", "").strip())
                    except ValueError:
                        pass
            
            # Clip scores to [0, 1]
            clarity = max(0.0, min(1.0, clarity))
            logical = max(0.0, min(1.0, logical))
            impact_score = max(0.0, min(1.0, impact_score))
            alignment = max(0.0, min(1.0, alignment))
            confidence = max(0.0, min(1.0, confidence))
            
            # Update proposal
            proposal.clarity_score = clarity
            proposal.logical_score = logical
            proposal.impact_score = impact_score
            proposal.doctrine_alignment_score = alignment
            proposal.confidence = confidence
            
            return proposal
        
        except Exception as e:
            logger.error(f"Failed to evaluate proposal {proposal.id}: {e}")
            proposal.confidence = 0.3
            return proposal

