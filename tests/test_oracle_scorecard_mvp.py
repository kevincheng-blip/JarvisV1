"""
Test Oracle Scorecard MVP.
"""
import json
from pathlib import Path
import tempfile

import pytest

from jgod.oracle.schemas import Prophecy, ScorecardRow, ForecastHorizon, TruthData
from jgod.oracle.archive_writer import write_prophecy_archive
from jgod.oracle.scorecard_grader import grade_prophecy, grade_archive, calculate_horizon_date


def test_horizon_date_calculation():
    """Test horizon date calculation."""
    assert calculate_horizon_date("2025-12-16", "T1") == "2025-12-17"
    assert calculate_horizon_date("2025-12-16", "T5") == "2025-12-21"
    assert calculate_horizon_date("2025-12-16", "T10") == "2025-12-26"
    assert calculate_horizon_date("2025-12-16", "T20") == "2026-01-05"


def test_grade_prophecy():
    """Test grading a single prophecy."""
    # Create test prophecy
    forecast_matrix = {
        "T1": ForecastHorizon(direction="UP", target_return=2.0, star=3, confidence="MED"),
    }
    
    prophecy_dict = {
        "schema_version": "or-os.v1",
        "prophecy_id": "test_prophecy_123" + "0" * 51,  # 64 chars
        "as_of_date": "2025-12-16",
        "symbol": "2330",
        "universe": "TOP50",
        "t0": {
            "timestamp": "2025-12-16T14:00:00+08:00",
            "baseline_price": 100.0,
            "baseline_source": "stub",
        },
        "top_bucket": "UP",
        "rank_in_bucket": 1,
        "resonance_tag": "STRONG",
        "conflict_score": 0.0,
        "forecast_matrix": {k: v.model_dump() for k, v in forecast_matrix.items()},
        "decision_footprint": {
            "B": {"raw_score": 0.7, "signals_used": []},
            "C": {"tags": [], "blocked": False, "reasons": []},
            "D": {"event_tags": [], "impact_vector": {}},
            "A": {"mutual_answer_summary": "Test", "key_conflicts": []},
        },
        "versions": {
            "oracle_core_version": "v1",
            "toolset_version": "v1",
            "doctrine_version": "v2",
        },
        "immutable_hash": "0" * 64,
    }
    
    prophecy = Prophecy(**prophecy_dict)
    
    # Grade
    scorecard = grade_prophecy(prophecy, "T1")
    
    assert scorecard.schema_version == "or-os.v1"
    assert scorecard.prophecy_id == prophecy_dict["prophecy_id"]
    assert scorecard.horizon == "T1"
    assert scorecard.symbol == "2330"
    assert scorecard.top_bucket == "UP"
    assert scorecard.rank_in_bucket == 1
    assert scorecard.pred_direction == "UP"
    assert scorecard.pred_target_return == 2.0
    assert scorecard.pred_star == 3
    assert scorecard.hit_direction is not None
    assert isinstance(scorecard.abs_error, float)
    assert isinstance(scorecard.signed_error, float)
    assert scorecard.baseline_price > 0
    assert scorecard.baseline_source in ["sqlite", "stub", "none"]
    assert scorecard.truth_price > 0
    assert scorecard.truth_source in ["sqlite", "stub", "none"]
    assert "regime_status" in scorecard.context


def test_grade_archive():
    """Test grading entire archive."""
    from jgod.oracle.run_archive import run_archive
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Generate archive
        run_archive("2025-12-16", "top50", tmp_path)
        archive_path = tmp_path / "prophecies_2025-12-16.jsonl"
        assert archive_path.exists()
        
        # Grade archive
        output_path = tmp_path / "scorecard_T1.jsonl"
        scorecard_rows = grade_archive(archive_path, "T1", output_path, db_path=None)
        
        assert len(scorecard_rows) == 100  # All prophecies should be graded
        assert output_path.exists()
        
        # Verify scorecard structure (new flat schema)
        for row in scorecard_rows:
            assert row.schema_version == "or-os.v1"
            assert row.horizon == "T1"
            assert row.score_id
            assert len(row.score_id) == 64  # SHA256 hex
            assert row.prophecy_id
            assert row.symbol
            assert row.top_bucket in ["UP", "DOWN"]
            assert row.rank_in_bucket >= 1
            assert isinstance(row.hit_direction, bool)
            assert isinstance(row.abs_error, float)
            assert isinstance(row.signed_error, float)
            assert row.baseline_price > 0
            assert row.baseline_source in ["sqlite", "stub", "none"]
            assert row.truth_price > 0
            assert row.truth_source in ["sqlite", "stub", "none"]
            assert row.pred_direction in ["UP", "DOWN", "SIDE"]
            assert isinstance(row.pred_target_return, float)
            assert row.pred_star >= 1 and row.pred_star <= 5
        
        # Load and verify JSONL
        loaded_rows = []
        with open(output_path, 'r') as f:
            for line in f:
                if line.strip():
                    loaded_rows.append(json.loads(line))
        
        assert len(loaded_rows) == 100
