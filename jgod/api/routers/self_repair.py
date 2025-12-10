"""Self-Repair API Router

Provides endpoints for Doctrine self-repair analysis and proposal management.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Body

from jgod.api.schemas.self_repair import (
    RepairReport,
    ApplyProposalRequest,
)
from jgod.knowledge.self_repair.engine import SelfRepairEngineV1
from jgod.knowledge.self_repair.models import (
    DoctrineSection,
    RepairReport as RepairReportModel,
    FixProposal,
)
from jgod.knowledge.self_repair.storage import RepairReportStorage
from jgod.knowledge.self_repair.patcher import SafePatcher

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize storage (singleton)
_storage = RepairReportStorage()


def _convert_to_schema(report: RepairReportModel) -> RepairReport:
    """Convert internal RepairReport to API schema"""
    return RepairReport(
        id=report.id,
        scan_summary=[
            {
                "id": issue.id,
                "issue_type": issue.issue_type.value,
                "doctrine_refs": issue.doctrine_refs,
                "description": issue.description,
                "severity": issue.severity.value,
                "context": issue.context,
                "created_at": issue.created_at,
            }
            for issue in report.scan_summary
        ],
        proposals=[
            {
                "id": prop.id,
                "issue_id": prop.issue_id,
                "proposed_text": prop.proposed_text,
                "justification": prop.justification,
                "confidence": prop.confidence,
                "impact": prop.impact,
                "clarity_score": prop.clarity_score,
                "logical_score": prop.logical_score,
                "impact_score": prop.impact_score,
                "doctrine_alignment_score": prop.doctrine_alignment_score,
                "metadata": prop.metadata,
                "created_at": prop.created_at,
            }
            for prop in report.proposals
        ],
        created_at=report.created_at,
        metadata=report.metadata,
    )


def _load_doctrine_sections() -> List[DoctrineSection]:
    """
    Load Doctrine sections for scanning.
    
    This is a placeholder - in production, this would load from DoctrineService.
    """
    try:
        from jgod.doctrine import DoctrineQueryV1
        
        query = DoctrineQueryV1()
        
        # Load sections from all registered books
        from jgod.doctrine.doctrine_registry_v1 import DOCTRINE_REGISTRY_V1
        
        all_sections = []
        for book_id in DOCTRINE_REGISTRY_V1.books.keys():
            try:
                sections = query.list_sections(book_id)
                for section in sections:
                    all_sections.append(DoctrineSection(
                        id=f"{section.book_id}#{section.section_id}",
                        text=f"{section.heading}\n\n{section.content}",
                        tags=section.tags or [],
                        source=section.book_id,
                        section_id=section.section_id,
                        metadata={
                            "heading": section.heading,
                            "level": section.level,
                        }
                    ))
            except Exception as e:
                logger.warning(f"Failed to load sections for {book_id}: {e}")
        
        logger.info(f"Loaded {len(all_sections)} Doctrine sections")
        return all_sections
    
    except Exception as e:
        logger.error(f"Failed to load Doctrine sections: {e}", exc_info=True)
        return []


@router.post(
    "/run",
    response_model=RepairReport,
    summary="Run full self-repair analysis",
    description="Scans Doctrine sections, generates proposals, and evaluates them.",
)
async def run_self_repair_analysis(
    use_llm: bool = Body(True, description="Whether to use LLM for advanced analysis"),
) -> RepairReport:
    """
    Run a complete self-repair analysis.
    
    Returns a RepairReport with all found issues and generated proposals.
    """
    try:
        # Load LLM provider
        llm_provider = None
        if use_llm:
            try:
                from api_clients.gemini_client import GeminiProvider
                llm_provider = GeminiProvider()
            except Exception as e:
                logger.warning(f"Failed to initialize LLM provider: {e}")
                use_llm = False
        
        # Load Doctrine sections
        doctrine_sections = _load_doctrine_sections()
        
        if not doctrine_sections:
            raise HTTPException(
                status_code=404,
                detail="No Doctrine sections found. Please ensure DoctrineService is properly configured."
            )
        
        # Initialize engine
        engine = SelfRepairEngineV1(llm_provider=llm_provider, storage=_storage)
        
        # Run analysis
        report = engine.run_full_repair_analysis(
            doctrine_sections=doctrine_sections,
            use_llm=use_llm,
            save_report=True,
        )
        
        # Convert to API schema
        return _convert_to_schema(report)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running self-repair analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/reports",
    response_model=List[RepairReport],
    summary="Get repair reports",
    description="Retrieves recent repair reports.",
)
async def get_repair_reports(
    limit: int = 10,
) -> List[RepairReport]:
    """
    Get recent repair reports.
    
    Args:
        limit: Maximum number of reports to return
    
    Returns:
        List of RepairReport objects
    """
    try:
        reports = _storage.load_recent(limit=limit)
        return [_convert_to_schema(r) for r in reports]
    except Exception as e:
        logger.error(f"Error loading repair reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/apply",
    summary="Apply a fix proposal",
    description="Applies a fix proposal to the knowledge base. Requires manual approval.",
)
async def apply_proposal(
    request: ApplyProposalRequest = Body(...),
) -> dict:
    """
    Apply a fix proposal to the knowledge base.
    
    This endpoint requires manual approval and creates backups before applying.
    """
    try:
        # Load the report containing this proposal
        reports = _storage.load_recent(limit=100)
        proposal = None
        for report in reports:
            for prop in report.proposals:
                if prop.id == request.proposal_id:
                    proposal = prop
                    break
            if proposal:
                break
        
        if not proposal:
            raise HTTPException(
                status_code=404,
                detail=f"Proposal not found: {request.proposal_id}"
            )
        
        # Initialize patcher
        patcher = SafePatcher()
        
        # Apply proposal
        success = patcher.apply_proposal(
            proposal=proposal,
            create_backup=request.create_backup,
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to apply proposal"
            )
        
        return {
            "success": True,
            "proposal_id": request.proposal_id,
            "message": "Proposal applied successfully. Please review and commit changes manually.",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying proposal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

