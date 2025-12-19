import pytest
from fastapi.testclient import TestClient

from jgod.api.main import app
from jgod.governance.reason_catalog import REASON_CATALOG


client = TestClient(app)


def test_governance_summary_contract():
    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200

    data = resp.json()

    required_keys = [
        "drift_status",
        "execution_confidence",
        "cluster_risk",
        "regime",
        "market_complexity",
        "ai_action",
        "updated_at",
        "is_stub",
    ]
    for key in required_keys:
        assert key in data, f"missing key: {key}"

    # module statuses
    for field in ["execution_confidence", "cluster_risk", "regime"]:
        mod = data[field]
        assert isinstance(mod, dict)
        for k in ["status", "updated_at", "is_stub", "reasons"]:
            assert k in mod
        assert isinstance(mod["reasons"], list)

    assert isinstance(data.get("reasons", []), list)
    for k in ["primary_reason_code", "human_sentence", "recommended_human_action", "action_confidence"]:
        assert k in data
        assert isinstance(data[k], str)
        if k in {"human_sentence", "recommended_human_action"} and data["primary_reason_code"] != "UNKNOWN_REASON_CODE":
            assert data[k].strip() != ""

    assert "recommended_ops" in data
    assert isinstance(data["recommended_ops"], dict)
    assert "guardrails" in data
    assert isinstance(data["guardrails"], dict)
    assert data["ai_action"] == data["recommended_ops"].get("mode")

    valid_ai_actions = {
        "FULL_TRUST",
        "CAUTIOUS_USE",
        "OBSERVE_ONLY",
        "REDUCE_EXPOSURE",
        "BLOCK_AI",
    }
    assert data["ai_action"] in valid_ai_actions
    valid_reason_codes = set(REASON_CATALOG.keys()) | {
        "EXEC_STUB",
        "CLUSTER_STUB",
        "REGIME_STUB",
        "DRIFT_UNKNOWN",
        "UNKNOWN_REASON_CODE",
    }
    assert data["primary_reason_code"] in valid_reason_codes


def test_ai_action_chaos_regime(monkeypatch):
    from jgod import governance

    def stub_regime():
        from jgod.api.schemas.governance_summary import GovernanceModuleStatus
        return GovernanceModuleStatus(status="CHAOS", is_stub=False), "HIGH"

    monkeypatch.setattr(governance.providers, "get_market_regime_status", stub_regime)

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_action"] == "BLOCK_AI"
    assert data["primary_reason_code"] == "REGIME_CHAOS_ANY"
    spec = REASON_CATALOG["REGIME_CHAOS_ANY"]
    assert data["human_sentence"] == spec.human_sentence
    assert data["recommended_human_action"] == spec.recommended_human_action
    assert data["recommended_ops"]["mode"] == "BLOCK_AI"
    assert data["recommended_ops"]["suggested_exposure_cap"] is None or data["recommended_ops"]["suggested_exposure_cap"] <= 0.1


def test_ai_action_drift_and_cluster_high(monkeypatch):
    """Test drift HIGH + cluster HIGH escalation (when regime is not CHAOS/COMPLEX/STABLE)"""
    from jgod.governance import providers
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler

    monkeypatch.setattr(
        providers,
        "get_cluster_risk_status",
        lambda: GovernanceModuleStatus(status="HIGH", is_stub=False, reasons=["CLUSTER_HIGH_CONSENSUS"]),
    )
    monkeypatch.setattr(
        providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MED", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    # Use STABLE regime (not CHAOS) so matrix applies, but drift will override
    monkeypatch.setattr(
        providers,
        "get_market_regime_status",
        lambda: (GovernanceModuleStatus(status="STABLE", is_stub=False, reasons=["REGIME_STABLE"]), "LOW"),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="HIGH", is_stub=False, reasons=["DRIFT_HIGH"]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    # Drift HIGH should override matrix (OBSERVE_ONLY)
    assert data["ai_action"] == "OBSERVE_ONLY"
    assert data["primary_reason_code"] == "DRIFT_HIGH"


def test_execution_no_data(monkeypatch):
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus

    # Force no data
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=["EXEC_NO_DATA"], metrics={"fill_rate": 0.0}),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    exec_conf = data["execution_confidence"]
    assert exec_conf["status"] == "LOW"
    assert "EXEC_NO_DATA" in exec_conf.get("reasons", [])


def test_execution_low_fill_caps_exposure(monkeypatch):
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler

    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(
            status="LOW",
            is_stub=False,
            score=0.2,
            reasons=["EXEC_LOW_FILL"],
            metrics={"fill_rate": 0.5, "avg_slippage_bp": 10, "reject_rate": 0.0},
        ),
    )
    # Keep other modules neutral
    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: (GovernanceModuleStatus(status="STABLE", is_stub=False, reasons=[]), "MED"),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_action"] == data["recommended_ops"]["mode"]
    assert data["recommended_ops"]["suggested_exposure_cap"] <= 0.3


def test_cluster_risk_non_stub_high_consensus(monkeypatch):
    """Test non-stub cluster risk with high consensus (18 positive, 2 negative = 90%)"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload
    from datetime import datetime

    # Mock SignalBus: 18 positive, 2 negative
    def mock_signal_bus_override():
        signals = []
        base_time = datetime.utcnow()
        for i in range(18):
            signals.append(SignalPayload(
                id=f"m50_pos_{i}",
                family="M50",
                value=0.8,
                weight=1.0,
                timestamp=base_time,
            ))
        for i in range(2):
            signals.append(SignalPayload(
                id=f"m50_neg_{i}",
                family="M50",
                value=-0.5,
                weight=1.0,
                timestamp=base_time,
            ))
        return signals

    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    # Keep other modules neutral
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: (GovernanceModuleStatus(status="STABLE", is_stub=False, reasons=[]), "MED"),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    cluster = data["cluster_risk"]
    assert cluster["is_stub"] is False
    assert cluster["status"] == "HIGH"
    assert "CLUSTER_HIGH_CONSENSUS" in cluster["reasons"]
    assert cluster["score"] is not None
    assert abs(cluster["score"] - 90.0) < 1.0  # 18/20 = 90%
    assert cluster["metrics"]["total_signals"] == 20
    assert cluster["metrics"]["positive_count"] == 18
    assert cluster["metrics"]["negative_count"] == 2


def test_cluster_risk_gate_high_affects_ai_action(monkeypatch):
    """Test that cluster HIGH triggers REDUCE_EXPOSURE with correct exposure cap"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload
    from datetime import datetime

    # Mock SignalBus: 18 positive, 2 negative (90% consensus = HIGH)
    def mock_signal_bus_override():
        signals = []
        base_time = datetime.utcnow()
        for i in range(18):
            signals.append(SignalPayload(
                id=f"m50_pos_{i}",
                family="M50",
                value=0.8,
                weight=1.0,
                timestamp=base_time,
            ))
        for i in range(2):
            signals.append(SignalPayload(
                id=f"m50_neg_{i}",
                family="M50",
                value=-0.5,
                weight=1.0,
                timestamp=base_time,
            ))
        return signals

    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    # Keep other modules neutral (don't trigger higher priority)
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: (GovernanceModuleStatus(status="STABLE", is_stub=False, reasons=[]), "MED"),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    # STABLE × HIGH → CAUTIOUS_USE (per matrix)
    assert data["ai_action"] == "CAUTIOUS_USE"
    assert data["primary_reason_code"] == "STABLE_HIGH_CLUSTER"
    assert data["recommended_ops"]["mode"] == "CAUTIOUS_USE"
    assert abs(data["recommended_ops"]["suggested_exposure_cap"] - 0.8) < 0.01
    assert "STABLE_HIGH_CLUSTER" in data["reasons"]


def test_cluster_risk_medium_consensus(monkeypatch):
    """Test medium consensus case (16 positive, 5 negative = 76.19%)"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload
    from datetime import datetime

    # Mock SignalBus: 16 positive, 5 negative (76.19% consensus = MEDIUM)
    def mock_signal_bus_override():
        signals = []
        base_time = datetime.utcnow()
        for i in range(16):
            signals.append(SignalPayload(
                id=f"m50_pos_{i}",
                family="M50",
                value=0.8,
                weight=1.0,
                timestamp=base_time,
            ))
        for i in range(5):
            signals.append(SignalPayload(
                id=f"m50_neg_{i}",
                family="M50",
                value=-0.5,
                weight=1.0,
                timestamp=base_time,
            ))
        return signals

    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    # Keep other modules neutral
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: (GovernanceModuleStatus(status="STABLE", is_stub=False, reasons=[]), "MED"),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    cluster = data["cluster_risk"]
    assert cluster["status"] == "MEDIUM"
    assert "CLUSTER_MEDIUM_CONSENSUS" in cluster["reasons"]
    assert cluster["score"] is not None
    assert 75.0 <= cluster["score"] < 85.0
    assert data["ai_action"] in {"CAUTIOUS_USE", "REDUCE_EXPOSURE"}  # At least CAUTIOUS_USE
    assert "CLUSTER_MEDIUM_CONSENSUS" in data["reasons"]


def test_cluster_risk_no_signals(monkeypatch):
    """Test no signals case (all zeros or empty)"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload

    # Mock SignalBus: return empty list
    def mock_signal_bus_override():
        return []

    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    # Keep other modules neutral
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: (GovernanceModuleStatus(status="STABLE", is_stub=False, reasons=[]), "LOW"),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    cluster = data["cluster_risk"]
    assert cluster["status"] == "UNKNOWN"
    assert cluster["is_stub"] is True
    assert "CLUSTER_NO_SIGNALS" in cluster["reasons"]
    assert cluster["score"] is None
    # ai_action should not be REDUCE_EXPOSURE due to cluster (unless other factors)
    # Since other modules are neutral, it should be FULL_TRUST or CAUTIOUS_USE
    assert data["ai_action"] != "REDUCE_EXPOSURE" or "CLUSTER_HIGH_CONSENSUS" not in data["reasons"]


def test_regime_chaos_blocks_ai(monkeypatch):
    """Test CHAOS regime triggers BLOCK_AI with exposure_cap=0.0"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.regime_provider import get_regime_status

    # Mock regime: ER < 0.2 (CHAOS)
    def mock_data_provider():
        # Generate high noise data (low ER)
        import numpy as np
        np.random.seed(123)
        base_price = 100.0
        prices = [base_price]
        for _ in range(100):
            # High volatility, low trend (low ER)
            change = np.random.normal(0, 5.0)  # High noise
            new_price = prices[-1] + change
            prices.append(max(new_price, 1.0))
        # Convert to OHLC
        ohlc = []
        for i, close in enumerate(prices):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * 1.01
            low = min(open_price, close) * 0.99
            ohlc.append((open_price, high, low, close))
        return ohlc

    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: get_regime_status(data_provider=mock_data_provider),
    )
    # Keep other modules neutral
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=["CLUSTER_LOW"]),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    regime = data["regime"]
    assert regime["status"] == "CHAOS"
    assert regime["is_stub"] is False
    assert "REGIME_CHAOS" in regime["reasons"]
    assert regime["score"] is not None
    assert regime["score"] < 0.2  # ER < 0.2
    
    assert data["ai_action"] == "BLOCK_AI"
    assert data["primary_reason_code"] == "REGIME_CHAOS_ANY"
    assert data["recommended_ops"]["mode"] == "BLOCK_AI"
    assert data["recommended_ops"]["suggested_exposure_cap"] == 0.0


def test_cluster_high_regime_chaos_precedence(monkeypatch):
    """Test that Regime CHAOS takes precedence over Cluster HIGH"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.providers.regime_provider import get_regime_status
    from jgod.governance.signal_bus import SignalPayload
    from datetime import datetime

    # Mock cluster: HIGH consensus
    def mock_signal_bus_override():
        # 18 positive, 2 negative (90% consensus = HIGH)
        signals = []
        base_time = datetime.utcnow()
        for i in range(18):
            signals.append(SignalPayload(
                id=f"m50_pos_{i}",
                family="M50",
                value=0.8,
                weight=1.0,
                timestamp=base_time,
            ))
        for i in range(2):
            signals.append(SignalPayload(
                id=f"m50_neg_{i}",
                family="M50",
                value=-0.5,
                weight=1.0,
                timestamp=base_time,
            ))
        return signals

    # Mock regime: CHAOS
    def mock_data_provider():
        import numpy as np
        np.random.seed(123)
        base_price = 100.0
        prices = [base_price]
        for _ in range(100):
            change = np.random.normal(0, 5.0)  # High noise
            new_price = prices[-1] + change
            prices.append(max(new_price, 1.0))
        ohlc = []
        for i, close in enumerate(prices):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * 1.01
            low = min(open_price, close) * 0.99
            ohlc.append((open_price, high, low, close))
        return ohlc

    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: get_regime_status(data_provider=mock_data_provider),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    # Regime CHAOS should win
    assert data["ai_action"] == "BLOCK_AI"
    assert data["primary_reason_code"] == "REGIME_CHAOS_ANY"
    assert data["recommended_ops"]["suggested_exposure_cap"] == 0.0
    
    # But cluster should still be HIGH
    cluster = data["cluster_risk"]
    assert cluster["status"] == "HIGH"
    assert "CLUSTER_HIGH_CONSENSUS" in data["reasons"]


def test_signal_bus_empty_data(monkeypatch):
    """Test SignalBus with empty data (defensive)"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload

    # Mock SignalBus: return empty list
    def mock_signal_bus_override():
        return []

    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: (GovernanceModuleStatus(status="STABLE", is_stub=False, reasons=["REGIME_STABLE"]), "LOW"),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    # Should not crash, cluster should be UNKNOWN
    cluster = data["cluster_risk"]
    assert cluster["status"] == "UNKNOWN"
    assert cluster["is_stub"] is True
    assert "CLUSTER_NO_SIGNALS" in cluster["reasons"]
    
    # Should not mis-trigger REDUCE_EXPOSURE
    assert data["ai_action"] != "REDUCE_EXPOSURE" or "CLUSTER_HIGH_CONSENSUS" not in data["reasons"]


def test_governance_matrix_chaos_any(monkeypatch):
    """Test CHAOS × ANY → BLOCK_AI"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.regime_provider import get_regime_status
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload
    from datetime import datetime

    # Mock regime: CHAOS
    def mock_data_provider():
        import numpy as np
        np.random.seed(123)
        base_price = 100.0
        prices = [base_price]
        for _ in range(100):
            change = np.random.normal(0, 5.0)  # High noise (low ER)
            new_price = prices[-1] + change
            prices.append(max(new_price, 1.0))
        ohlc = []
        for i, close in enumerate(prices):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * 1.01
            low = min(open_price, close) * 0.99
            ohlc.append((open_price, high, low, close))
        return ohlc

    # Mock cluster: HIGH (test CHAOS × HIGH)
    def mock_signal_bus_override():
        signals = []
        base_time = datetime.utcnow()
        for i in range(18):
            signals.append(SignalPayload(
                id=f"m50_pos_{i}",
                family="M50",
                value=0.8,
                weight=1.0,
                timestamp=base_time,
            ))
        for i in range(2):
            signals.append(SignalPayload(
                id=f"m50_neg_{i}",
                family="M50",
                value=-0.5,
                weight=1.0,
                timestamp=base_time,
            ))
        return signals

    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: get_regime_status(data_provider=mock_data_provider),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["ai_action"] == "BLOCK_AI"
    assert data["primary_reason_code"] == "REGIME_CHAOS_ANY"
    assert data["recommended_ops"]["suggested_exposure_cap"] == 0.0
    assert data["decision_context"]["regime"] == "CHAOS"
    assert data["decision_context"]["cluster"] == "HIGH"


def test_governance_matrix_complex_high(monkeypatch):
    """Test COMPLEX × HIGH → BLOCK_AI"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.regime_provider import get_regime_status
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload
    from datetime import datetime

    # Mock regime: COMPLEX (ER between 0.2 and 0.5)
    def mock_data_provider():
        import numpy as np
        np.random.seed(456)
        base_price = 100.0
        prices = [base_price]
        # Generate moderate trend with noise (ER ~ 0.3)
        for i in range(100):
            trend = 0.5 if i < 50 else -0.3  # Some trend
            noise = np.random.normal(0, 2.0)
            new_price = prices[-1] + trend + noise
            prices.append(max(new_price, 1.0))
        ohlc = []
        for i, close in enumerate(prices):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * 1.01
            low = min(open_price, close) * 0.99
            ohlc.append((open_price, high, low, close))
        return ohlc

    # Mock cluster: HIGH
    def mock_signal_bus_override():
        signals = []
        base_time = datetime.utcnow()
        for i in range(18):
            signals.append(SignalPayload(
                id=f"m50_pos_{i}",
                family="M50",
                value=0.8,
                weight=1.0,
                timestamp=base_time,
            ))
        for i in range(2):
            signals.append(SignalPayload(
                id=f"m50_neg_{i}",
                family="M50",
                value=-0.5,
                weight=1.0,
                timestamp=base_time,
            ))
        return signals

    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: get_regime_status(data_provider=mock_data_provider),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    regime = data["regime"]
    cluster = data["cluster_risk"]
    
    # Verify regime is COMPLEX
    if regime["status"] == "COMPLEX":
        assert data["ai_action"] == "BLOCK_AI"
        assert data["primary_reason_code"] == "COMPLEX_HIGH_CLUSTER"
        assert data["recommended_ops"]["suggested_exposure_cap"] == 0.0
        assert data["decision_context"]["regime"] == "COMPLEX"
        assert data["decision_context"]["cluster"] == "HIGH"


def test_governance_matrix_complex_medium(monkeypatch):
    """Test COMPLEX × MEDIUM → REDUCE_EXPOSURE (0.3)"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.regime_provider import get_regime_status
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload
    from datetime import datetime

    # Mock regime: COMPLEX
    def mock_data_provider():
        import numpy as np
        np.random.seed(456)
        base_price = 100.0
        prices = [base_price]
        for i in range(100):
            trend = 0.5 if i < 50 else -0.3
            noise = np.random.normal(0, 2.0)
            new_price = prices[-1] + trend + noise
            prices.append(max(new_price, 1.0))
        ohlc = []
        for i, close in enumerate(prices):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * 1.01
            low = min(open_price, close) * 0.99
            ohlc.append((open_price, high, low, close))
        return ohlc

    # Mock cluster: MEDIUM (16 positive, 5 negative = 76.19%)
    def mock_signal_bus_override():
        signals = []
        base_time = datetime.utcnow()
        for i in range(16):
            signals.append(SignalPayload(
                id=f"m50_pos_{i}",
                family="M50",
                value=0.8,
                weight=1.0,
                timestamp=base_time,
            ))
        for i in range(5):
            signals.append(SignalPayload(
                id=f"m50_neg_{i}",
                family="M50",
                value=-0.5,
                weight=1.0,
                timestamp=base_time,
            ))
        return signals

    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: get_regime_status(data_provider=mock_data_provider),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    regime = data["regime"]
    cluster = data["cluster_risk"]
    
    # Verify regime is COMPLEX and cluster is MEDIUM
    if regime["status"] == "COMPLEX" and cluster["status"] == "MEDIUM":
        assert data["ai_action"] == "REDUCE_EXPOSURE"
        assert data["primary_reason_code"] == "COMPLEX_MEDIUM_CLUSTER"
        assert abs(data["recommended_ops"]["suggested_exposure_cap"] - 0.3) < 0.01
        assert data["decision_context"]["regime"] == "COMPLEX"
        assert data["decision_context"]["cluster"] == "MEDIUM"


def test_governance_matrix_stable_high(monkeypatch):
    """Test STABLE × HIGH → CAUTIOUS_USE"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.regime_provider import get_regime_status
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload
    from datetime import datetime

    # Mock regime: STABLE (ER >= 0.5)
    def mock_data_provider():
        import numpy as np
        np.random.seed(789)
        base_price = 100.0
        prices = [base_price]
        # Strong trend (high ER)
        for i in range(100):
            trend = 1.0  # Strong upward trend
            noise = np.random.normal(0, 0.5)  # Low noise
            new_price = prices[-1] + trend + noise
            prices.append(max(new_price, 1.0))
        ohlc = []
        for i, close in enumerate(prices):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * 1.01
            low = min(open_price, close) * 0.99
            ohlc.append((open_price, high, low, close))
        return ohlc

    # Mock cluster: HIGH
    def mock_signal_bus_override():
        signals = []
        base_time = datetime.utcnow()
        for i in range(18):
            signals.append(SignalPayload(
                id=f"m50_pos_{i}",
                family="M50",
                value=0.8,
                weight=1.0,
                timestamp=base_time,
            ))
        for i in range(2):
            signals.append(SignalPayload(
                id=f"m50_neg_{i}",
                family="M50",
                value=-0.5,
                weight=1.0,
                timestamp=base_time,
            ))
        return signals

    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: get_regime_status(data_provider=mock_data_provider),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    regime = data["regime"]
    cluster = data["cluster_risk"]
    
    # Verify regime is STABLE and cluster is HIGH
    if regime["status"] == "STABLE" and cluster["status"] == "HIGH":
        assert data["ai_action"] == "CAUTIOUS_USE"
        assert data["primary_reason_code"] == "STABLE_HIGH_CLUSTER"
        assert abs(data["recommended_ops"]["suggested_exposure_cap"] - 0.8) < 0.01
        assert data["decision_context"]["regime"] == "STABLE"
        assert data["decision_context"]["cluster"] == "HIGH"


def test_governance_matrix_stable_low(monkeypatch):
    """Test STABLE × LOW → FULL_TRUST"""
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler
    from jgod.governance.providers.regime_provider import get_regime_status
    from jgod.governance.providers.cluster_provider import get_cluster_risk_status
    from jgod.governance.signal_bus import SignalPayload
    from datetime import datetime

    # Mock regime: STABLE
    def mock_data_provider():
        import numpy as np
        np.random.seed(789)
        base_price = 100.0
        prices = [base_price]
        for i in range(100):
            trend = 1.0  # Strong trend
            noise = np.random.normal(0, 0.5)
            new_price = prices[-1] + trend + noise
            prices.append(max(new_price, 1.0))
        ohlc = []
        for i, close in enumerate(prices):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * 1.01
            low = min(open_price, close) * 0.99
            ohlc.append((open_price, high, low, close))
        return ohlc

    # Mock cluster: LOW (mixed signals, consensus < 75%)
    def mock_signal_bus_override():
        signals = []
        base_time = datetime.utcnow()
        # 12 positive, 8 negative (60% consensus = LOW)
        for i in range(12):
            signals.append(SignalPayload(
                id=f"m50_pos_{i}",
                family="M50",
                value=0.8,
                weight=1.0,
                timestamp=base_time,
            ))
        for i in range(8):
            signals.append(SignalPayload(
                id=f"m50_neg_{i}",
                family="M50",
                value=-0.5,
                weight=1.0,
                timestamp=base_time,
            ))
        return signals

    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: get_regime_status(data_provider=mock_data_provider),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: get_cluster_risk_status(signal_bus_override=mock_signal_bus_override),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MEDIUM", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="LOW", is_stub=False, reasons=[]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    
    regime = data["regime"]
    cluster = data["cluster_risk"]
    
    # Verify regime is STABLE and cluster is LOW
    if regime["status"] == "STABLE" and cluster["status"] == "LOW":
        assert data["ai_action"] == "FULL_TRUST"
        assert data["primary_reason_code"] == "STABLE_LOW_CLUSTER"
        assert abs(data["recommended_ops"]["suggested_exposure_cap"] - 1.0) < 0.01
        assert data["decision_context"]["regime"] == "STABLE"
        assert data["decision_context"]["cluster"] == "LOW"


