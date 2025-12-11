"""Rule Sim Engine Stub

Stub implementation for Rule Simulation Engine.
"""

import logging
from jgod.doctrine_v2.models import DoctrinePatch, RuleSimStatus

logger = logging.getLogger(__name__)


class RuleSimEngineStub:
    """Stub Rule Simulation Engine for testing"""
    
    def run_simulation(self, patch: DoctrinePatch) -> RuleSimStatus:
        """
        Run simulation for a patch (stub implementation)
        
        For now: even number of changes = APPROVED, else REJECTED
        
        Args:
            patch: DoctrinePatch to simulate
            
        Returns:
            RuleSimStatus (APPROVED or REJECTED)
        """
        # Stub logic: even number of changes = APPROVED
        if len(patch.changes) % 2 == 0:
            logger.info(f"Rule Sim stub: APPROVED (even number of changes: {len(patch.changes)})")
            return RuleSimStatus.APPROVED
        else:
            logger.info(f"Rule Sim stub: REJECTED (odd number of changes: {len(patch.changes)})")
            return RuleSimStatus.REJECTED
