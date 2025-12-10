"""Self-Repair Engine

Main engine that orchestrates the self-repair pipeline.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Protocol

from jgod.knowledge.self_repair.models import (
    DoctrineSection,
    RepairReport,
)
from jgod.knowledge.self_repair.scanner import SelfRepairScanner
from jgod.knowledge.self_repair.proposer import RepairProposer
from jgod.knowledge.self_repair.evaluator import ProposalEvaluator
from jgod.knowledge.self_repair.storage import RepairReportStorage

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM provider"""
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        ...


class SelfRepairEngineV1:
    """Self-Repair Engine v1
    
    Orchestrates the complete self-repair pipeline:
    1. Scan Doctrine for issues
    2. Generate fix proposals
    3. Evaluate proposals
    4. Store report
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        storage: Optional[RepairReportStorage] = None,
    ):
        """
        Initialize self-repair engine
        
        Args:
            llm_provider: LLM provider for scanning and proposal generation
            storage: Storage instance for reports (optional)
        """
        self.scanner = SelfRepairScanner(llm_provider=llm_provider)
        self.proposer = RepairProposer(llm_provider=llm_provider)
        self.evaluator = ProposalEvaluator(llm_provider=llm_provider)
        self.storage = storage or RepairReportStorage()
        logger.info("SelfRepairEngineV1 initialized")
    
    def run_full_repair_analysis(
        self,
        doctrine_sections: List[DoctrineSection],
        use_llm: bool = True,
        save_report: bool = True,
    ) -> RepairReport:
        """
        Run complete self-repair analysis pipeline.
        
        Args:
            doctrine_sections: List of Doctrine sections to analyze
            use_llm: Whether to use LLM for advanced analysis
            save_report: Whether to save report to storage
        
        Returns:
            RepairReport with issues and proposals
        """
        logger.info(f"Starting full repair analysis for {len(doctrine_sections)} sections")
        
        # Step 1: Scan for issues
        issues = self.scanner.scan_doctrine(doctrine_sections, use_llm=use_llm)
        logger.info(f"Found {len(issues)} issues")
        
        # Step 2: Generate proposals
        proposals = self.proposer.generate_proposals(issues, doctrine_sections)
        logger.info(f"Generated {len(proposals)} proposals")
        
        # Step 3: Evaluate proposals
        evaluated_proposals = self.evaluator.evaluate_proposals(proposals)
        logger.info(f"Evaluated {len(evaluated_proposals)} proposals")
        
        # Step 4: Create report
        report = RepairReport(
            id=str(uuid.uuid4()),
            scan_summary=issues,
            proposals=evaluated_proposals,
            created_at=datetime.now(),
            metadata={
                "num_sections_scanned": len(doctrine_sections),
                "use_llm": use_llm,
                "engine_version": "v1.0",
            }
        )
        
        # Step 5: Save report (if enabled)
        if save_report:
            try:
                self.storage.save(report)
            except Exception as e:
                logger.error(f"Failed to save report: {e}", exc_info=True)
        
        logger.info(f"Repair analysis complete: {len(issues)} issues, {len(evaluated_proposals)} proposals")
        return report

