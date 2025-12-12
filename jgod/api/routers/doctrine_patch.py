"""Doctrine Patch API Router

Provides endpoints for Doctrine Patch workflow.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Body

from jgod.api.schemas.doctrine_patch import (
    CreatePatchRequest,
    DoctrinePatchSchema,
    DoctrinePatchSummarySchema,
    RunSimResponse,
    ApprovePatchResponse,
    DeployPatchResponse,
    RevertPatchResponse,
    ApprovePatchRequest,
    RejectPatchRequest,
    DeployPatchRequest,
    RevertPatchRequest,
    patch_to_schema,
    patch_to_summary_schema,
)
from jgod.doctrine_v2.patch_service import DoctrinePatchService
from jgod.doctrine_v2.models import (
    PatchStatus,
    DoctrineChangeItem,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service (singleton)
_service = DoctrinePatchService()


@router.post(
    "/patches",
    response_model=DoctrinePatchSchema,
    summary="Create a doctrine patch",
    description="Creates a new doctrine patch with status PENDING_SIMULATION",
)
async def create_patch(request: CreatePatchRequest) -> DoctrinePatchSchema:
    """Create a new doctrine patch"""
    try:
        # Convert schema changes to model changes
        changes = [
            DoctrineChangeItem(
                change_type=ch.change_type,
                rule_id=ch.rule_id,
                old_text=ch.old_text,
                new_text=ch.new_text,
            )
            for ch in request.changes
        ]
        
        # Create patch via service
        patch = _service.create_patch(
            author_id=request.author_id,
            description=request.description,
            changes=changes,
        )
        
        return patch_to_schema(patch)
    except Exception as e:
        logger.error(f"Error creating patch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create patch: {str(e)}")


@router.get(
    "/patches/queue",
    response_model=List[DoctrinePatchSummarySchema],
    summary="Get patch queue",
    description="Retrieves patches with filtering",
)
async def get_patch_queue(
    status: Optional[str] = Query(None, description="Filter by status"),
) -> List[DoctrinePatchSummarySchema]:
    """Get patch queue"""
    try:
        status_filter = None
        if status:
            try:
                status_filter = [PatchStatus(status.upper())]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        else:
            # Default: return patches with status in [PENDING_SIMULATION, PENDING_REVIEW, APPROVED]
            status_filter = [
                PatchStatus.PENDING_SIMULATION,
                PatchStatus.PENDING_REVIEW,
                PatchStatus.APPROVED,
            ]
        
        patches = _service.list_patches(status_filter=status_filter)
        return [patch_to_summary_schema(p) for p in patches]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patch queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/patches/{patch_id}",
    response_model=DoctrinePatchSchema,
    summary="Get patch details",
)
async def get_patch(patch_id: str) -> DoctrinePatchSchema:
    """Get patch details"""
    patch = _service.get_patch(patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail=f"Patch not found: {patch_id}")
    return patch_to_schema(patch)


@router.post(
    "/patches/{patch_id}/run-sim",
    response_model=RunSimResponse,
    summary="Run Rule Sim for a patch",
)
async def run_sim(patch_id: str) -> RunSimResponse:
    """Run Rule Sim validation for a patch"""
    try:
        patch = _service.run_rule_sim(patch_id)
        return RunSimResponse(
            success=True,
            patch=patch_to_schema(patch),
            message="Rule Sim completed successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running Rule Sim for patch {patch_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to run Rule Sim: {str(e)}")


@router.post(
    "/patches/{patch_id}/approve",
    response_model=ApprovePatchResponse,
    summary="Approve a patch",
)
async def approve_patch(
    patch_id: str,
    request: ApprovePatchRequest = Body(...),
) -> ApprovePatchResponse:
    """Approve a patch"""
    try:
        patch = _service.approve_patch(patch_id, request.reviewer_id)
        return ApprovePatchResponse(
            success=True,
            patch=patch_to_schema(patch),
            message="Patch approved successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving patch {patch_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve patch: {str(e)}")


@router.post(
    "/patches/{patch_id}/reject",
    response_model=DoctrinePatchSchema,
    summary="Reject a patch",
)
async def reject_patch(
    patch_id: str,
    request: RejectPatchRequest = Body(...),
) -> DoctrinePatchSchema:
    """Reject a patch"""
    try:
        patch = _service.reject_patch(patch_id, request.reviewer_id)
        return patch_to_schema(patch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting patch {patch_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reject patch: {str(e)}")


@router.post(
    "/patches/{patch_id}/deploy",
    response_model=DeployPatchResponse,
    summary="Deploy a patch to production",
)
async def deploy_patch(
    patch_id: str,
    request: DeployPatchRequest = Body(...),
) -> DeployPatchResponse:
    """Deploy a patch to production"""
    try:
        patch = _service.deploy_patch(patch_id)
        return DeployPatchResponse(
            success=True,
            patch=patch_to_schema(patch),
            deployment_version=patch.deployment_version or 0,
            message="Patch deployed successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deploying patch {patch_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to deploy patch: {str(e)}")


@router.post(
    "/patches/{patch_id}/revert",
    response_model=RevertPatchResponse,
    summary="Revert a deployed patch",
)
async def revert_patch(
    patch_id: str,
    request: RevertPatchRequest = Body(...),
) -> RevertPatchResponse:
    """Revert a deployed patch"""
    try:
        patch = _service.revert_patch(patch_id)
        return RevertPatchResponse(
            success=True,
            patch=patch_to_schema(patch),
            message="Patch reverted successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error reverting patch {patch_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to revert patch: {str(e)}")
