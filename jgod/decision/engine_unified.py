"""Decision Layer Unified Engine

Unified interface supporting both V1 and V2 decision engines.
"""

import logging
from typing import List, Literal, Optional

from jgod.decision.models import RawScoreItem, DecisionOutput, DecisionBatchResult
from jgod.decision.engine import DecisionEngineV1
from jgod.decision.engine_v2 import DecisionEngineV2
from jgod.decision.config import DecisionConfig

logger = logging.getLogger(__name__)


class DecisionEngineUnified:
    """Unified Decision Engine supporting V1 and V2"""
    
    def __init__(
        self,
        version: Literal["v1", "v2"] = "v2",
        config: Optional[DecisionConfig] = None,
        knowledge_brain=None,
    ):
        """
        Initialize unified decision engine
        
        Args:
            version: Engine version ("v1" or "v2")
            config: DecisionConfig (required for v1)
            knowledge_brain: KnowledgeBrain instance (optional)
        """
        self.version = version
        
        if version == "v1":
            if config is None:
                config = DecisionConfig()
            self.engine = DecisionEngineV1(config=config, knowledge_brain=knowledge_brain)
        elif version == "v2":
            self.engine = DecisionEngineV2(knowledge_brain=knowledge_brain)
        else:
            raise ValueError(f"Unsupported version: {version}")
        
        logger.info(f"DecisionEngineUnified initialized with version: {version}")
    
    def decide_for_batch(self, raw_items: List[RawScoreItem]) -> DecisionBatchResult:
        """Process batch using selected version"""
        return self.engine.decide_for_batch(raw_items)
    
    def decide_for_single(self, raw_item: RawScoreItem) -> DecisionOutput:
        """Process single item using selected version"""
        return self.engine.decide_for_single(raw_item)

