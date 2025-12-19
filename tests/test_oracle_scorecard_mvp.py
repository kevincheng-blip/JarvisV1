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
        "prophecy_id": "test_prophecy_123",
        "as_of_date": "2025-12-16",
        "t0": {
            "timestamp": "2025-12-16T14:00:00+08:00",
            "baseline_price": 100.0,
            "baseline_source": "stub",
            "symbol": "2330",
            "universe": "TOP50",
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
        "immutable_hash": "test_hash_64_chars_" + "0" * 40,
    }
    
    prophecy = Prophecy(**prophecy_dict)
    
    # Grade
    scorecard = grade_prophecy(prophecy, "T1")
    
    assert scorecard.schema_version == "or-os.v1"
    assert scorecard.prophecy_id == "test_prophecy_123"
    assert scorecard.horizon == "T1"
    assert scorecard.symbol == "2330"
    assert scorecard.pred["direction"] == "UP"
    assert scorecard.pred["target_return"] == 2.0
    assert "hit_direction" in scorecard.metrics
    assert "abs_error" in scorecard.metrics
    assert "signed_error" in scorecard.metrics
    assert isinstance(scorecard.metrics["abs_error"], float)
    assert isinstance(scorecard.metrics["hit_direction"], bool)
    assert scorecard.truth.tN_date == "2025-12-17"
    assert scorecard.truth.tN_price > 0
    assert "regime" in scorecard.context


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
        scorecard_rows = grade_archive(archive_path, "T1", output_path)
        
        assert len(scorecard_rows) == 100  # All prophecies should be graded
        assert output_path.exists()
        
        # Verify scorecard structure
        for row in scorecard_rows:
            assert row.schema_version == "or-os.v1"
            assert row.horizon == "T1"
            assert row.score_id
            assert row.prophecy_id
            assert row.symbol
            assert "hit_direction" in row.metrics
            assert "abs_error" in row.metrics
            assert "signed_error" in row.metrics
            assert isinstance(row.metrics["abs_error"], (int, float))
            assert isinstance(row.metrics["hit_direction"], bool)
            assert row.truth.tN_price > 0
            assert row.truth.realized_return is not None
        
        # Load and verify JSONL
        loaded_rows = []
        with open(output_path, 'r') as f:
            for line in f:
                if line.strip():
                    loaded_rows.append(json.loads(line))
        
        assert len(loaded_rows) == 100
