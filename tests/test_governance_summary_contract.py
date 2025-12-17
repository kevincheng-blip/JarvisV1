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
    assert data["primary_reason_code"] == "REGIME_CHAOS"
    spec = REASON_CATALOG["REGIME_CHAOS"]
    assert data["human_sentence"] == spec.human_sentence
    assert data["recommended_human_action"] == spec.recommended_human_action
    assert data["recommended_ops"]["mode"] == "BLOCK_AI"
    assert data["recommended_ops"]["suggested_exposure_cap"] is None or data["recommended_ops"]["suggested_exposure_cap"] <= 0.1


def test_ai_action_drift_and_cluster_high(monkeypatch):
    from jgod import governance
    from jgod.api.schemas.governance_summary import GovernanceModuleStatus
    from jgod.governance import assembler

    monkeypatch.setattr(
        governance.providers,
        "get_cluster_risk_status",
        lambda: GovernanceModuleStatus(status="HIGH", is_stub=False, reasons=["CLUSTER_HIGH"]),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_execution_rigor_status",
        lambda: GovernanceModuleStatus(status="MED", is_stub=False, reasons=["EXEC_MEDIUM"]),
    )
    monkeypatch.setattr(
        governance.providers,
        "get_market_regime_status",
        lambda: (GovernanceModuleStatus(status="RANGE", is_stub=False, reasons=["REGIME_STUB"]), "MED"),
    )
    monkeypatch.setattr(
        assembler,
        "_get_drift_status",
        lambda: GovernanceModuleStatus(status="HIGH", is_stub=False, reasons=["DRIFT_HIGH"]),
    )

    resp = client.get("/api/v1/governance/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_action"] == "BLOCK_AI"
    assert data["primary_reason_code"] in {"DRIFT_HIGH", "CLUSTER_HIGH"}


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


