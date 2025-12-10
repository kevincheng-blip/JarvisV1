"""Doctrine Service V2 API Router

Provides endpoints for Doctrine Management Console.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Body

from jgod.api.schemas.doctrine_v2 import (
    DoctrineSectionSchema,
    CreateDraftRequest,
    DiffResponse,
    BulkActionRequest,
)
from jgod.doctrine_v2.service import DoctrineServiceV2
from jgod.doctrine_v2.models import SectionStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service (singleton)
_service = DoctrineServiceV2()


def _section_to_schema(section) -> DoctrineSectionSchema:
    """Convert DoctrineSectionV2 to API schema"""
    return DoctrineSectionSchema(
        section_id=section.section_id,
        title=section.title,
        current_version_id=section.current_version_id,
        draft_version_id=section.draft_version_id,
        status=section.status.value,
        created_at=section.created_at,
        updated_at=section.updated_at,
        revision_history=[
            {
                "version_id": r.version_id,
                "timestamp": r.timestamp,
                "operator": r.operator,
                "change_type": r.change_type.value,
                "content": r.content,
                "metadata": r.metadata,
            }
            for r in section.revision_history
        ],
        source=section.source,
        severity=section.severity,
        metadata=section.metadata,
    )


@router.get(
    "/sections",
    response_model=dict,
    summary="Get Doctrine sections",
    description="Retrieves Doctrine sections with filtering and pagination.",
)
async def get_sections(
    status: Optional[str] = Query(None, description="Filter by status: APPROVED, DRAFT, PENDING_REVIEW, DEPRECATED"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
) -> dict:
    """
    Get Doctrine sections with filtering and pagination.
    
    Returns:
        Dictionary with sections list and pagination info
    """
    try:
        status_filter = None
        if status:
            try:
                status_filter = SectionStatus(status.upper())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        sections, total = _service.get_sections(
            status=status_filter,
            page=page,
            page_size=page_size,
        )
        
        return {
            "sections": [_section_to_schema(s) for s in sections],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/sections/{section_id}",
    response_model=DoctrineSectionSchema,
    summary="Get a specific Doctrine section",
)
async def get_section(section_id: str) -> DoctrineSectionSchema:
    """Get a specific Doctrine section"""
    section = _service.get_section(section_id)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section not found: {section_id}")
    return _section_to_schema(section)


@router.get(
    "/sections/{section_id}/diff",
    response_model=DiffResponse,
    summary="Get diff between two versions",
)
async def get_diff(
    section_id: str,
    from_version: str = Query(..., description="Source version ID"),
    to_version: str = Query(..., description="Target version ID"),
) -> DiffResponse:
    """Get unified diff between two versions"""
    diff = _service.get_diff(section_id, from_version, to_version)
    if diff is None:
        raise HTTPException(
            status_code=404,
            detail=f"One or both versions not found: {from_version}, {to_version}"
        )
    return DiffResponse(diff=diff, from_version_id=from_version, to_version_id=to_version)


@router.get(
    "/sections/{section_id}/versions/{version_id}/content",
    summary="Get content for a specific version",
)
async def get_version_content(
    section_id: str,
    version_id: str,
) -> dict:
    """Get content for a specific version"""
    content = _service.get_version_content(section_id, version_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {
        "section_id": section_id,
        "version_id": version_id,
        "content": content,
    }


@router.post(
    "/sections/{section_id}/draft",
    summary="Create a draft version",
)
async def create_draft(
    section_id: str,
    request: CreateDraftRequest = Body(...),
) -> dict:
    """Create a draft version for a section"""
    version_id = _service.create_draft(
        section_id=section_id,
        content=request.content,
        operator="human",
    )
    if not version_id:
        raise HTTPException(status_code=500, detail="Failed to create draft")
    return {
        "section_id": section_id,
        "version_id": version_id,
        "status": "success",
    }


@router.post(
    "/sections/{section_id}/submit",
    summary="Submit draft for review",
)
async def submit_for_review(section_id: str) -> dict:
    """Submit draft for review"""
    success = _service.submit_for_review(section_id)
    if not success:
        raise HTTPException(status_code=400, detail="No draft found or submit failed")
    return {"section_id": section_id, "status": "submitted"}


@router.post(
    "/sections/{section_id}/approve",
    summary="Approve a version",
)
async def approve_version(
    section_id: str,
    version_id: str = Query(..., description="Version ID to approve"),
) -> dict:
    """Approve a version"""
    success = _service.approve_version(section_id, version_id)
    if not success:
        raise HTTPException(status_code=400, detail="Approve failed")
    return {"section_id": section_id, "version_id": version_id, "status": "approved"}


@router.post(
    "/sections/{section_id}/reject",
    summary="Reject a version",
)
async def reject_version(
    section_id: str,
    version_id: str = Query(..., description="Version ID to reject"),
) -> dict:
    """Reject a version"""
    success = _service.reject_version(section_id, version_id)
    if not success:
        raise HTTPException(status_code=400, detail="Reject failed")
    return {"section_id": section_id, "version_id": version_id, "status": "rejected"}


@router.post(
    "/sections/{section_id}/rollback",
    summary="Rollback to a previous version",
)
async def rollback_version(
    section_id: str,
    target_version_id: str = Query(..., description="Target version ID to rollback to"),
) -> dict:
    """Rollback to a previous version"""
    success = _service.rollback_to_version(section_id, target_version_id)
    if not success:
        raise HTTPException(status_code=400, detail="Rollback failed")
    return {"section_id": section_id, "target_version_id": target_version_id, "status": "rolled_back"}


@router.post(
    "/sections/bulk-action",
    summary="Bulk approve or reject sections",
)
async def bulk_action(
    request: BulkActionRequest = Body(...),
) -> dict:
    """Bulk approve or reject sections"""
    if request.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'reject'")
    
    results = []
    for section_id in request.section_ids:
        section = _service.get_section(section_id)
        if not section:
            results.append({"section_id": section_id, "status": "not_found"})
            continue
        
        if section.status != SectionStatus.PENDING_REVIEW:
            results.append({"section_id": section_id, "status": "not_pending_review"})
            continue
        
        if request.action == "approve" and section.draft_version_id:
            success = _service.approve_version(section_id, section.draft_version_id)
            results.append({"section_id": section_id, "status": "approved" if success else "failed"})
        elif request.action == "reject" and section.draft_version_id:
            success = _service.reject_version(section_id, section.draft_version_id)
            results.append({"section_id": section_id, "status": "rejected" if success else "failed"})
        else:
            results.append({"section_id": section_id, "status": "no_draft"})
    
    return {
        "action": request.action,
        "results": results,
    }

