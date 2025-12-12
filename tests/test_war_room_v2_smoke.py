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


def test_predictions_latest_ok():
    """測試 Predictions Latest API 能正常回應（允許 404 或 200）"""
    response = client.get("/api/v1/predictions/latest/2330")
    # Should be 200 (even if no data, should return 200 with null/empty)
    # Or 404 is acceptable if symbol doesn't exist, but prefer 200
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text}"
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"


def test_predictions_timeline_ok():
    """測試 Predictions Timeline API 能正常回應（允許空 items）"""
    response = client.get("/api/v1/predictions/timeline/2330?limit=5")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "symbol" in data, "Response should have 'symbol' field"
    assert "items" in data, "Response should have 'items' field"
    assert isinstance(data["items"], list), "items should be a list"


def test_observer_prediction_stability_ok():
    """測試 Observer Prediction Stability API 能正常回應（允許 NO_DATA）"""
    response = client.get("/api/v1/observer/prediction-stability/2330?limit=5")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "symbol" in data, "Response should have 'symbol' field"
    assert "stability_grade" in data, "Response should have 'stability_grade' field"
    assert data["stability_grade"] in ["NO_DATA", "STABLE", "WATCH", "VOLATILE"], \
        f"stability_grade should be valid, got {data['stability_grade']}"


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
