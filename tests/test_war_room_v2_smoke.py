"""
J-GOD War Room V2 / Observer / Doctrine Patch / AB Test Smoke Tests

本檔案是 J-GOD War Room V2 / Observer / Doctrine Patch / AB Test 的最小 smoke test，
執行方式：pytest tests/test_war_room_v2_smoke.py

這些測試只驗證 API endpoint 能正常回應（status_code == 200），
不檢查具體業務邏輯是否正確。即使回傳空陣列也可以通過。
"""

from fastapi.testclient import TestClient
from jgod.api.main import app

client = TestClient(app)


def test_observer_governance_summary_ok():
    """測試 Observer Governance Summary API 能正常回應"""
    response = client.get("/api/v1/observer/governance-summary")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    # 驗證可以正常解析 JSON
    data = response.json()
    assert data is not None


def test_observer_stability_alerts_ok():
    """測試 Observer Stability Alerts API 能正常回應"""
    response = client.get("/api/v1/observer/stability-alerts")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    # 驗證可以正常解析 JSON
    data = response.json()
    assert isinstance(data, list), "Stability alerts should return a list"


def test_observer_s_rank_distribution_ok():
    """測試 Observer S-Rank Distribution History API 能正常回應"""
    response = client.get("/api/v1/observer/s-rank-history/distribution?days=30")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    # 驗證可以正常解析 JSON
    data = response.json()
    assert data is not None


def test_doctrine_patches_queue_ok():
    """測試 Doctrine Patches Queue API 能正常回應"""
    response = client.get("/api/v1/doctrine/patches/queue")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    # 驗證可以正常解析 JSON
    data = response.json()
    assert isinstance(data, list), "Patches queue should return a list"


def test_decision_ab_reports_recent_ok():
    """測試 Decision AB Test Recent Reports API 能正常回應"""
    response = client.get("/api/v1/ab-test/decision-reports/recent?limit=1")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    # 驗證可以正常解析 JSON
    data = response.json()
    assert isinstance(data, list), "Recent AB test reports should return a list"
