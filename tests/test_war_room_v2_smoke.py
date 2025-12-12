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


def test_doctrine_patch_queue_health_check():
    """測試 Doctrine Patch Queue API 健康檢查（允許空陣列）"""
    response = client.get("/api/v1/doctrine/patches/queue")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"


def test_s_rank_v2_recommendation_health_check():
    """測試 S-Rank V2 Recommendation API 健康檢查（允許 items empty）"""
    response = client.get("/api/v1/s-rank-v2/recommendation/2330?limit=60&k=5")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "symbol" in data, "Response should have 'symbol' field"
    assert "metrics" in data, "Response should have 'metrics' field"
    assert "items" in data, "Response should have 'items' field"
    assert isinstance(data["items"], list), "items should be a list"


def test_strategy_perf_latest_health_check():
    """測試 Strategy Performance Latest API 健康檢查（允許 items empty）"""
    response = client.get("/api/v1/strategy-perf/latest/2330")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "symbol" in data, "Response should have 'symbol' field"
    assert "items" in data, "Response should have 'items' field"
    assert isinstance(data["items"], list), "items should be a list"


def test_s_rank_v2_recommendation_performance_mode_health_check():
    """測試 S-Rank V2 Recommendation API (mode=performance) 健康檢查"""
    response = client.get("/api/v1/s-rank-v2/recommendation/2330?mode=performance&limit=60&k=5")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "symbol" in data, "Response should have 'symbol' field"
    assert "items" in data, "Response should have 'items' field"
    assert isinstance(data["items"], list), "items should be a list"


def test_decision_v3_health_check():
    """測試 Decision V3 API 健康檢查（允許 NO_DATA）"""
    response = client.get("/api/v1/decision-v3/decide/2330?mode=performance&limit=60&k=5")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "symbol" in data, "Response should have 'symbol' field"
    assert "risk_plan" in data, "Response should have 'risk_plan' field"
    assert "confidence" in data, "Response should have 'confidence' field"
    assert "explain" in data, "Response should have 'explain' field"
    assert isinstance(data["risk_plan"], dict), "risk_plan should be a dictionary"
    assert "risk_state" in data["risk_plan"], "risk_plan should have 'risk_state' field"
    assert "position_scale" in data["risk_plan"], "risk_plan should have 'position_scale' field"


def test_decision_v3_latest_health_check():
    """測試 Decision V3 Latest API 健康檢查（允許 NO_DATA）"""
    response = client.get("/api/v1/decision-v3/latest/2330")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "symbol" in data, "Response should have 'symbol' field"
    assert "result" in data, "Response should have 'result' field"
    assert isinstance(data["result"], dict), "result should be a dictionary"


def test_decision_v3_recompute_health_check():
    """測試 Decision V3 Recompute API 健康檢查"""
    response = client.post("/api/v1/decision-v3/recompute/2330?mode=performance&limit=60&k=5")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "snapshot_id" in data, "Response should have 'snapshot_id' field"
    assert "result" in data, "Response should have 'result' field"
    assert isinstance(data["result"], dict), "result should be a dictionary"


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
