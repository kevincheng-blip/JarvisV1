"""
Test Oracle Scorecard Summary MVP.
"""
import json
import tempfile
from pathlib import Path

import pytest

from jgod.oracle.scorecard_summary import calculate_summary, calculate_spearman_rank_ic, calculate_star_reliability_index


def test_spearman_rank_ic():
    """Test Spearman rank IC calculation."""
    # Perfect positive correlation
    pred = [1.0, 2.0, 3.0, 4.0, 5.0]
    realized = [1.0, 2.0, 3.0, 4.0, 5.0]
    ic = calculate_spearman_rank_ic(pred, realized)
    assert abs(ic - 1.0) < 0.01
    
    # Perfect negative correlation
    realized_neg = [5.0, 4.0, 3.0, 2.0, 1.0]
    ic_neg = calculate_spearman_rank_ic(pred, realized_neg)
    assert abs(ic_neg - (-1.0)) < 0.01
    
    # No correlation
    realized_random = [3.0, 1.0, 5.0, 2.0, 4.0]
    ic_random = calculate_spearman_rank_ic(pred, realized_random)
    assert abs(ic_random) < 0.5  # Should be low


def test_star_reliability_index():
    """Test star reliability index calculation."""
    # Perfect monotonic
    cal1 = [
        {"star": 1, "count": 10, "hit_rate": 0.3, "mae": 5.0},
        {"star": 2, "count": 10, "hit_rate": 0.4, "mae": 4.0},
        {"star": 3, "count": 10, "hit_rate": 0.5, "mae": 3.0},
        {"star": 4, "count": 10, "hit_rate": 0.6, "mae": 2.0},
        {"star": 5, "count": 10, "hit_rate": 0.7, "mae": 1.0},
    ]
    reliability1 = calculate_star_reliability_index(cal1)
    assert reliability1 == 1.0
    
    # One violation
    cal2 = [
        {"star": 1, "count": 10, "hit_rate": 0.3, "mae": 5.0},
        {"star": 2, "count": 10, "hit_rate": 0.5, "mae": 4.0},  # Higher than star 1
        {"star": 3, "count": 10, "hit_rate": 0.4, "mae": 3.0},  # Lower than star 2 (violation)
        {"star": 4, "count": 10, "hit_rate": 0.6, "mae": 2.0},
    ]
    reliability2 = calculate_star_reliability_index(cal2)
    assert reliability2 == 0.75  # 1.0 - 0.25


def test_summary_structure():
    """Test summary structure and fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create fake scorecard data
        scorecard_data = [
            {
                "schema_version": "or-os.v1",
                "score_id": "test1",
                "prophecy_id": "prop1",
                "as_of_date": "2025-12-16",
                "symbol": "2330",
                "top_bucket": "UP",
                "rank_in_bucket": 1,
                "horizon": "T1",
                "baseline_price": 100.0,
                "baseline_source": "sqlite",
                "truth_price": 102.0,
                "truth_source": "sqlite",
                "pred_direction": "UP",
                "pred_target_return": 2.0,
                "pred_star": 3,
                "pred_confidence": "MED",
                "realized_return": 2.0,
                "hit_direction": True,
                "abs_error": 0.0,
                "signed_error": 0.0,
                "context": {"regime_status": "STABLE", "cluster_status": "LOW", "drift_status": "LOW"},
                "explain": {},
                "attribution_stub": {},
            },
            {
                "schema_version": "or-os.v1",
                "score_id": "test2",
                "prophecy_id": "prop2",
                "as_of_date": "2025-12-16",
                "symbol": "2317",
                "top_bucket": "DOWN",
                "rank_in_bucket": 1,
                "horizon": "T1",
                "baseline_price": 100.0,
                "baseline_source": "stub",
                "truth_price": 98.0,
                "truth_source": "stub",
                "pred_direction": "DOWN",
                "pred_target_return": -2.0,
                "pred_star": 4,
                "pred_confidence": "HIGH",
                "realized_return": -2.0,
                "hit_direction": True,
                "abs_error": 0.0,
                "signed_error": 0.0,
                "context": {"regime_status": "COMPLEX", "cluster_status": "MEDIUM", "drift_status": "MEDIUM"},
                "explain": {},
                "attribution_stub": {},
            },
        ]
        
        # Write scorecard
        scorecard_path = tmp_path / "scorecard_2025-12-16_T1.jsonl"
        with open(scorecard_path, 'w') as f:
            for row in scorecard_data:
                f.write(json.dumps(row) + '\n')
        
        # Calculate summary
        summary = calculate_summary(
            scorecard_paths={"T1": scorecard_path},
            as_of_date="2025-12-16",
            universe="TOP50"
        )
        
        # Verify structure
        assert summary["schema_version"] == "or-os.v1"
        assert summary["as_of_date"] == "2025-12-16"
        assert summary["universe"] == "TOP50"
        assert "data_quality" in summary
        assert "forecast_quality_by_horizon" in summary
        
        # Data quality
        assert "baseline_source_counts" in summary["data_quality"]
        assert "sqlite" in summary["data_quality"]["baseline_source_counts"]
        assert "stub" in summary["data_quality"]["baseline_source_counts"]
        
        # Forecast quality
        t1_quality = summary["forecast_quality_by_horizon"]["T1"]
        assert "hit_rate" in t1_quality
        assert "hit_rate_by_bucket" in t1_quality
        assert "mae" in t1_quality
        assert "rmse" in t1_quality
        assert "rank_ic_overall" in t1_quality
        assert "star_calibration" in t1_quality
        assert "star_reliability_index" in t1_quality
        assert "context_attribution" in t1_quality
        
        # Star calibration structure
        assert len(t1_quality["star_calibration"]) > 0
        for cal in t1_quality["star_calibration"]:
            assert "star" in cal
            assert "count" in cal
            assert "hit_rate" in cal
            assert "mae" in cal
        
        # Sanity checks
        assert "sanity_checks" in summary
        assert "scale_check" in summary["sanity_checks"]
        assert "source_check" in summary["sanity_checks"]
        assert summary["sanity_checks"]["scale_check"]["status"] in ["OK", "SUSPECT"]
        assert summary["sanity_checks"]["source_check"]["status"] in ["OK", "SUSPECT"]
        assert "sqlite_ratio_baseline" in summary["sanity_checks"]["source_check"]


def test_summary_sanity_check_scale_suspect():
    """Test sanity check detects scale issues."""
    import json
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create fake scorecard with high MAE (scale issue)
        scorecard_data = [
            {
                "schema_version": "or-os.v1",
                "score_id": "test1",
                "prophecy_id": "prop1",
                "as_of_date": "2025-12-16",
                "symbol": "2330",
                "top_bucket": "UP",
                "rank_in_bucket": 1,
                "horizon": "T1",
                "baseline_price": 100.0,
                "baseline_source": "stub",
                "truth_price": 102.0,
                "truth_source": "stub",
                "pred_direction": "UP",
                "pred_target_return": 2.0,
                "pred_star": 3,
                "pred_confidence": "MED",
                "realized_return": 2.0,
                "hit_direction": True,
                "abs_error": 35.0,  # Artificially high (scale issue)
                "signed_error": 0.0,
                "context": {},
                "explain": {},
                "attribution_stub": {},
            },
        ]
        
        scorecard_path = tmp_path / "scorecard_2025-12-16_T1.jsonl"
        with open(scorecard_path, 'w') as f:
            for row in scorecard_data:
                f.write(json.dumps(row) + '\n')
        
        summary = calculate_summary(
            scorecard_paths={"T1": scorecard_path},
            as_of_date="2025-12-16",
            universe="TOP50"
        )
        
        # Should detect scale issue
        scale_check = summary["sanity_checks"]["scale_check"]
        assert scale_check["status"] == "SUSPECT"
        assert len(scale_check["reasons"]) > 0
