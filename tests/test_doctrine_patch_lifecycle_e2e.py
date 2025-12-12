"""
Doctrine Patch Lifecycle E2E Contract Test

Tests the complete patch lifecycle: create → run-sim → approve → deploy → revert.
This test is data-independent: uses random patch IDs and ensures sim always APPROVED.
"""

import uuid
from fastapi.testclient import TestClient
from jgod.api.main import app

client = TestClient(app)


def test_patch_lifecycle_e2e():
    """E2E test: create → run-sim → approve → deploy → revert"""
    
    # Generate unique identifiers
    author_id = f"test-author-{uuid.uuid4().hex[:8]}"
    reviewer_id = f"test-reviewer-{uuid.uuid4().hex[:8]}"
    operator_id = f"test-operator-{uuid.uuid4().hex[:8]}"
    
    # Step 1: Create patch (2 change_items to guarantee sim APPROVED)
    print("Step 1: Creating patch...")
    create_request = {
        "author_id": author_id,
        "description": f"E2E test patch {uuid.uuid4().hex[:8]}",
        "changes": [
            {
                "change_type": "add",
                "rule_id": "test-rule-1",
                "old_text": None,
                "new_text": "Test rule content 1",
            },
            {
                "change_type": "modify",
                "rule_id": "test-rule-2",
                "old_text": "Old content",
                "new_text": "New content",
            },
        ],
    }
    
    create_response = client.post("/api/v1/doctrine/patches", json=create_request)
    assert create_response.status_code == 200, f"Expected 200, got {create_response.status_code}: {create_response.text}"
    patch_data = create_response.json()
    patch_id = patch_data["patch_id"]
    assert patch_data["status"] == "PENDING_SIMULATION", f"Expected PENDING_SIMULATION, got {patch_data['status']}"
    print(f"   ✅ Created patch: {patch_id}")
    
    # Step 2: Run Rule Sim
    print("Step 2: Running Rule Sim...")
    sim_response = client.post(f"/api/v1/doctrine/patches/{patch_id}/run-sim")
    assert sim_response.status_code == 200, f"Expected 200, got {sim_response.status_code}: {sim_response.text}"
    sim_data = sim_response.json()
    assert sim_data["success"] is True, "Sim should succeed"
    patch_after_sim = sim_data["patch"]
    assert patch_after_sim["sim_result_status"] == "APPROVED", \
        f"Expected sim_result_status APPROVED (2 changes = even), got {patch_after_sim['sim_result_status']}"
    assert patch_after_sim["status"] == "PENDING_REVIEW", \
        f"Expected status PENDING_REVIEW after sim approval, got {patch_after_sim['status']}"
    print(f"   ✅ Sim completed: {patch_after_sim['sim_result_status']}, status: {patch_after_sim['status']}")
    
    # Step 3: Approve patch
    print("Step 3: Approving patch...")
    approve_request = {
        "reviewer_id": reviewer_id,
        "comment": "E2E test approval",
    }
    approve_response = client.post(
        f"/api/v1/doctrine/patches/{patch_id}/approve",
        json=approve_request
    )
    assert approve_response.status_code == 200, f"Expected 200, got {approve_response.status_code}: {approve_response.text}"
    approve_data = approve_response.json()
    assert approve_data["success"] is True, "Approve should succeed"
    patch_after_approve = approve_data["patch"]
    assert patch_after_approve["status"] == "APPROVED", \
        f"Expected status APPROVED, got {patch_after_approve['status']}"
    print(f"   ✅ Patch approved, status: {patch_after_approve['status']}")
    
    # Step 4: Deploy patch
    print("Step 4: Deploying patch...")
    deploy_request = {
        "operator_id": operator_id,
    }
    deploy_response = client.post(
        f"/api/v1/doctrine/patches/{patch_id}/deploy",
        json=deploy_request
    )
    assert deploy_response.status_code == 200, f"Expected 200, got {deploy_response.status_code}: {deploy_response.text}"
    deploy_data = deploy_response.json()
    assert deploy_data["success"] is True, "Deploy should succeed"
    patch_after_deploy = deploy_data["patch"]
    assert patch_after_deploy["status"] == "DEPLOYED", \
        f"Expected status DEPLOYED, got {patch_after_deploy['status']}"
    assert patch_after_deploy["deployment_version"] is not None, "deployment_version should be set"
    print(f"   ✅ Patch deployed, version: {patch_after_deploy['deployment_version']}, status: {patch_after_deploy['status']}")
    
    # Step 5: Revert patch
    print("Step 5: Reverting patch...")
    revert_request = {
        "operator_id": operator_id,
    }
    revert_response = client.post(
        f"/api/v1/doctrine/patches/{patch_id}/revert",
        json=revert_request
    )
    assert revert_response.status_code == 200, f"Expected 200, got {revert_response.status_code}: {revert_response.text}"
    revert_data = revert_response.json()
    assert revert_data["success"] is True, "Revert should succeed"
    patch_after_revert = revert_data["patch"]
    assert patch_after_revert["status"] == "REVERTED", \
        f"Expected status REVERTED, got {patch_after_revert['status']}"
    print(f"   ✅ Patch reverted, status: {patch_after_revert['status']}")
    
    print("\n✅ E2E lifecycle test completed successfully!")


def test_patch_lifecycle_state_guards():
    """Test that state guards prevent invalid transitions"""
    
    author_id = f"test-author-{uuid.uuid4().hex[:8]}"
    
    # Create patch
    create_request = {
        "author_id": author_id,
        "description": "State guard test patch",
        "changes": [
            {
                "change_type": "add",
                "rule_id": "test-rule",
                "old_text": None,
                "new_text": "Test content",
            },
        ],
    }
    create_response = client.post("/api/v1/doctrine/patches", json=create_request)
    patch_id = create_response.json()["patch_id"]
    
    # Try to approve before sim (should fail)
    approve_response = client.post(
        f"/api/v1/doctrine/patches/{patch_id}/approve",
        json={"reviewer_id": "test-reviewer"}
    )
    assert approve_response.status_code == 400, "Should reject approve before sim"
    
    # Try to deploy before approve (should fail)
    deploy_response = client.post(
        f"/api/v1/doctrine/patches/{patch_id}/deploy",
        json={"operator_id": "test-operator"}
    )
    assert deploy_response.status_code == 400, "Should reject deploy before approve"
    
    # Try to revert before deploy (should fail)
    revert_response = client.post(
        f"/api/v1/doctrine/patches/{patch_id}/revert",
        json={"operator_id": "test-operator"}
    )
    assert revert_response.status_code == 400, "Should reject revert before deploy"

