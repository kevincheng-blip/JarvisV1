"""Doctrine Patch API Schemas

Pydantic models for Doctrine Patch API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from jgod.doctrine_v2.models import PatchStatus, RuleSimStatus, DoctrinePatch


class DoctrineChangeItemSchema(BaseModel):
    """Doctrine change item schema"""
    change_type: str  # "add", "modify", "delete"
    rule_id: str
    old_text: Optional[str] = None
    new_text: Optional[str] = None

    class Config:
        from_attributes = True


class CreatePatchRequest(BaseModel):
    """Request to create a doctrine patch"""
    author_id: str
    description: str
    changes: List[DoctrineChangeItemSchema]


class DoctrinePatchSchema(BaseModel):
    """Doctrine patch schema"""
    patch_id: str
    created_at: datetime
    author_id: str
    description: str
    changes: List[DoctrineChangeItemSchema]
    status: str
    rule_sim_report_id: Optional[str] = None
    sim_result_status: str
    deployment_version: Optional[int] = None
    deployed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DoctrinePatchSummarySchema(BaseModel):
    """Doctrine patch summary schema (for list views)"""
    patch_id: str
    status: str
    created_at: datetime
    author_id: str
    description: str
    sim_result_status: str
    rule_sim_report_id: Optional[str] = None

    class Config:
        from_attributes = True


class RunSimResponse(BaseModel):
    """Response for run-sim endpoint"""
    success: bool
    patch: DoctrinePatchSchema
    message: Optional[str] = None


class ApprovePatchResponse(BaseModel):
    """Response for approve endpoint"""
    success: bool
    patch: DoctrinePatchSchema
    message: Optional[str] = None


class DeployPatchResponse(BaseModel):
    """Response for deploy endpoint"""
    success: bool
    patch: DoctrinePatchSchema
    deployment_version: int
    message: Optional[str] = None


class RevertPatchResponse(BaseModel):
    """Response for revert endpoint"""
    success: bool
    patch: DoctrinePatchSchema
    message: Optional[str] = None


# Mapping functions from DoctrinePatch → Schema

def patch_to_schema(patch: DoctrinePatch) -> DoctrinePatchSchema:
    """Convert DoctrinePatch to DoctrinePatchSchema"""
    return DoctrinePatchSchema(
        patch_id=patch.patch_id,
        created_at=patch.created_at,
        author_id=patch.author_id,
        description=patch.description,
        changes=[
            DoctrineChangeItemSchema(
                change_type=ch.change_type,
                rule_id=ch.rule_id,
                old_text=ch.old_text,
                new_text=ch.new_text,
            )
            for ch in patch.changes
        ],
        status=patch.status.value,
        rule_sim_report_id=patch.rule_sim_report_id,
        sim_result_status=patch.sim_result_status.value,
        deployment_version=patch.deployment_version,
        deployed_at=patch.deployed_at,
    )


def patch_to_summary_schema(patch: DoctrinePatch) -> DoctrinePatchSummarySchema:
    """Convert DoctrinePatch to DoctrinePatchSummarySchema"""
    return DoctrinePatchSummarySchema(
        patch_id=patch.patch_id,
        status=patch.status.value,
        created_at=patch.created_at,
        author_id=patch.author_id,
        description=patch.description,
        sim_result_status=patch.sim_result_status.value,
        rule_sim_report_id=patch.rule_sim_report_id,
    )
