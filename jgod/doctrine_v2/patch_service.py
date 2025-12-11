"""Doctrine Patch Service

Core service for Doctrine Patch & Rollout workflow.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from jgod.doctrine_v2.models import (
    DoctrinePatch,
    DoctrineChangeItem,
    PatchStatus,
    RuleSimStatus,
)
from jgod.doctrine_v2.patch_storage import (
    save_patch,
    load_patch,
    list_patches,
    update_patch_status,
    update_patch_after_sim,
    update_patch_after_deploy,
    update_patch_revert,
)
from jgod.doctrine_v2.rule_sim_engine_stub import RuleSimEngineStub
from jgod.doctrine_v2.doctrine_repo_stub import (
    get_current_version,
    save_new_version,
    apply_changes_stub,
)

logger = logging.getLogger(__name__)


class DoctrinePatchService:
    """Doctrine Patch & Rollout Service"""
    
    def __init__(self):
        """Initialize Doctrine Patch Service"""
        self.rule_sim_engine = RuleSimEngineStub()
        logger.info("DoctrinePatchService initialized")
    
    def create_patch(
        self,
        author_id: str,
        description: str,
        changes: List[DoctrineChangeItem],
    ) -> DoctrinePatch:
        """
        Create a new DoctrinePatch with status PENDING_SIMULATION
        
        Args:
            author_id: Author ID
            description: Patch description
            changes: List of changes
            
        Returns:
            DoctrinePatch instance
        """
        patch_id = str(uuid.uuid4())
        
        patch = DoctrinePatch(
            patch_id=patch_id,
            created_at=datetime.now(),
            author_id=author_id,
            description=description,
            changes=changes,
            status=PatchStatus.PENDING_SIMULATION,
            sim_result_status=RuleSimStatus.PENDING,
        )
        
        save_patch(patch)
        logger.info(f"Created patch {patch_id} by {author_id}")
        return patch
    
    def run_rule_sim(self, patch_id: str) -> DoctrinePatch:
        """
        Run Rule Sim validation for a patch
        
        Args:
            patch_id: Patch ID
            
        Returns:
            Updated DoctrinePatch
        """
        patch = load_patch(patch_id)
        if not patch:
            raise ValueError(f"Patch not found: {patch_id}")
        
        logger.info(f"Running Rule Sim for patch {patch_id}")
        
        # Call RuleSimEngine to validate the patch
        sim_status = self.rule_sim_engine.run_simulation(patch)
        
        # Generate a stub report ID
        rule_sim_report_id = f"sim-{patch_id}-{uuid.uuid4().hex[:8]}"
        
        # Update patch via patch_storage
        update_patch_after_sim(patch_id, sim_status, rule_sim_report_id)
        
        # Reload and return
        return load_patch(patch_id)
    
    def approve_patch(self, patch_id: str, reviewer_id: str) -> DoctrinePatch:
        """
        Approve a patch (only if sim_result_status == APPROVED)
        
        Status will be set to APPROVED (from PENDING_REVIEW after sim approval)
        
        Args:
            patch_id: Patch ID
            reviewer_id: Reviewer ID
            
        Returns:
            Updated DoctrinePatch
        """
        patch = load_patch(patch_id)
        if not patch:
            raise ValueError(f"Patch not found: {patch_id}")
        
        # Only approve if sim_result_status == APPROVED
        if patch.sim_result_status != RuleSimStatus.APPROVED:
            raise ValueError(f"Patch {patch_id} sim_result_status is not APPROVED")
        
        # Status should be PENDING_REVIEW after sim approval, then approve -> APPROVED
        if patch.status != PatchStatus.PENDING_REVIEW:
            raise ValueError(f"Patch {patch_id} is not in PENDING_REVIEW status")
        
        # Status -> APPROVED
        update_patch_status(patch_id, PatchStatus.APPROVED)
        
        logger.info(f"Patch {patch_id} approved by {reviewer_id}")
        return load_patch(patch_id)
    
    def reject_patch(self, patch_id: str, reviewer_id: str) -> DoctrinePatch:
        """
        Reject a patch
        
        Args:
            patch_id: Patch ID
            reviewer_id: Reviewer ID
            
        Returns:
            Updated DoctrinePatch
        """
        patch = load_patch(patch_id)
        if not patch:
            raise ValueError(f"Patch not found: {patch_id}")
        
        # Status -> REJECTED_BY_SIM (or could be a separate reject status)
        update_patch_status(patch_id, PatchStatus.REJECTED_BY_SIM)
        
        logger.info(f"Patch {patch_id} rejected by {reviewer_id}")
        return load_patch(patch_id)
    
    def deploy_patch(self, patch_id: str) -> DoctrinePatch:
        """
        Deploy a patch to production
        
        Args:
            patch_id: Patch ID
            
        Returns:
            Updated DoctrinePatch
        """
        patch = load_patch(patch_id)
        if not patch:
            raise ValueError(f"Patch not found: {patch_id}")
        
        # Safety guard: Prevent deploying if patch.status != APPROVED
        if patch.status != PatchStatus.APPROVED:
            raise ValueError(f"Patch {patch_id} is not in APPROVED status (current: {patch.status.value})")
        
        # Safety guard: Prevent double deploy (status == DEPLOYED)
        if patch.status == PatchStatus.DEPLOYED:
            raise ValueError(f"Patch {patch_id} is already deployed")
        
        logger.info(f"Deploying patch {patch_id}")
        
        # Load current doctrine version
        current_version = get_current_version()
        
        # Apply changes to doctrine (stub)
        apply_changes_stub(patch)
        
        # Save new doctrine version number
        new_version = current_version + 1
        save_new_version(new_version)
        
        # Update patch via update_patch_after_deploy
        update_patch_after_deploy(patch_id, new_version)
        
        logger.info(f"Patch {patch_id} deployed successfully (version {new_version})")
        return load_patch(patch_id)
    
    def revert_patch(self, patch_id: str) -> DoctrinePatch:
        """
        Revert a deployed patch
        
        Args:
            patch_id: Patch ID
            
        Returns:
            Updated DoctrinePatch
        """
        patch = load_patch(patch_id)
        if not patch:
            raise ValueError(f"Patch not found: {patch_id}")
        
        # Safety guard: Prevent revert if patch.status != DEPLOYED
        if patch.status != PatchStatus.DEPLOYED:
            raise ValueError(f"Patch {patch_id} is not in DEPLOYED status (current: {patch.status.value})")
        
        logger.info(f"Reverting patch {patch_id}")
        
        # Restore doctrine to previous version (stub)
        if patch.deployment_version:
            logger.info(f"Restoring doctrine to version before {patch.deployment_version} (stub)")
            # In real implementation, would restore doctrine to previous version
            # For stub, just decrement version
            current_version = get_current_version()
            if current_version > 1:
                save_new_version(current_version - 1)
        
        # Update patch via update_patch_revert
        update_patch_revert(patch_id)
        
        logger.info(f"Patch {patch_id} reverted successfully")
        return load_patch(patch_id)
    
    def list_patches(
        self,
        status_filter: Optional[List[PatchStatus]] = None,
    ) -> List[DoctrinePatch]:
        """
        List patches with optional status filter
        
        Args:
            status_filter: Optional list of statuses to filter by
            
        Returns:
            List of patches
        """
        return list_patches(status=status_filter)
    
    def get_patch(self, patch_id: str) -> Optional[DoctrinePatch]:
        """
        Get a patch by ID
        
        Args:
            patch_id: Patch ID
            
        Returns:
            DoctrinePatch if found, None otherwise
        """
        return load_patch(patch_id)


# Manual smoke test for development
if __name__ == "__main__":
    """
    Manual smoke test for development
    
    Creates patch → run sim → approve → deploy → revert
    """
    import sys
    
    service = DoctrinePatchService()
    
    try:
        # 1. Create patch
        print("1. Creating patch...")
        from jgod.doctrine_v2.models import DoctrineChangeItem
        changes = [
            DoctrineChangeItem(
                change_type="add",
                rule_id="test-rule-1",
                old_text=None,
                new_text="Test rule content",
            ),
            DoctrineChangeItem(
                change_type="modify",
                rule_id="test-rule-2",
                old_text="Old content",
                new_text="New content",
            ),
        ]
        patch = service.create_patch(
            author_id="test-user",
            description="Test patch for smoke test",
            changes=changes,
        )
        print(f"   Created patch: {patch.patch_id} (status: {patch.status.value})")
        
        # 2. Run sim (even number of changes = APPROVED)
        print("2. Running Rule Sim...")
        patch = service.run_rule_sim(patch.patch_id)
        print(f"   Sim result: {patch.sim_result_status.value} (status: {patch.status.value})")
        
        if patch.sim_result_status.value == "APPROVED":
            # 3. Approve
            print("3. Approving patch...")
            patch = service.approve_patch(patch.patch_id, reviewer_id="test-reviewer")
            print(f"   Patch approved (status: {patch.status.value})")
            
            # 4. Deploy
            print("4. Deploying patch...")
            patch = service.deploy_patch(patch.patch_id)
            print(f"   Patch deployed (version: {patch.deployment_version}, status: {patch.status.value})")
            
            # 5. Revert
            print("5. Reverting patch...")
            patch = service.revert_patch(patch.patch_id)
            print(f"   Patch reverted (status: {patch.status.value})")
        else:
            print(f"   Patch rejected by sim, skipping approve/deploy/revert")
        
        print("\n✅ Smoke test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
