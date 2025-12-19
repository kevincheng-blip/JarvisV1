"""
Test Oracle Archive Schema.
"""
import json
from pathlib import Path
import tempfile

import pytest

from jgod.oracle.schemas import Prophecy, ForecastHorizon
from jgod.oracle.archive_writer import write_prophecy_archive, load_prophecy_archive, compute_immutable_hash


def test_prophecy_schema():
    """Test Prophecy schema validation."""
    forecast_matrix = {
        "T1": ForecastHorizon(direction="UP", target_return=2.0, star=3, confidence="MED"),
        "T5": ForecastHorizon(direction="UP", target_return=3.5, star=3, confidence="MED"),
        "T10": ForecastHorizon(direction="UP", target_return=5.0, star=3, confidence="MED"),
        "T20": ForecastHorizon(direction="UP", target_return=7.0, star=3, confidence="MED"),
        "TM": ForecastHorizon(direction="UP", target_return=9.0, star=3, confidence="MED"),
    }
    
    prophecy_dict = {
        "schema_version": "or-os.v1",
        "prophecy_id": "test_id_123",
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
        "immutable_hash": "test_hash",
    }
    
    prophecy = Prophecy(**prophecy_dict)
    assert prophecy.schema_version == "or-os.v1"
    assert prophecy.prophecy_id == "test_id_123"
    assert prophecy.top_bucket == "UP"
    assert len(prophecy.forecast_matrix) == 5
    assert "T1" in prophecy.forecast_matrix
    assert "T5" in prophecy.forecast_matrix
    assert "T10" in prophecy.forecast_matrix
    assert "T20" in prophecy.forecast_matrix
    assert "TM" in prophecy.forecast_matrix


def test_archive_write_and_load():
    """Test writing and loading archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_archive.jsonl"
        
        # Create test prophecies
        prophecies = []
        for i in range(5):
            forecast_matrix = {
                "T1": ForecastHorizon(direction="UP", target_return=2.0, star=3, confidence="MED"),
                "T5": ForecastHorizon(direction="UP", target_return=3.5, star=3, confidence="MED"),
                "T10": ForecastHorizon(direction="UP", target_return=5.0, star=3, confidence="MED"),
                "T20": ForecastHorizon(direction="UP", target_return=7.0, star=3, confidence="MED"),
                "TM": ForecastHorizon(direction="UP", target_return=9.0, star=3, confidence="MED"),
            }
            
            prophecy_dict = {
                "schema_version": "or-os.v1",
                "prophecy_id": f"test_id_{i}" + "0" * (64 - len(f"test_id_{i}")),  # 64 chars
                "as_of_date": "2025-12-16",
                "symbol": f"233{i}",
                "universe": "TOP50",
                "t0": {
                    "timestamp": "2025-12-16T14:00:00+08:00",
                    "baseline_price": 100.0 + i,
                    "baseline_source": "stub",
                },
                "top_bucket": "UP" if i < 3 else "DOWN",
                "rank_in_bucket": i + 1,
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
            }
            
            # Compute hash
            immutable_hash = compute_immutable_hash(prophecy_dict)
            prophecy_dict["immutable_hash"] = immutable_hash
            
            prophecies.append(Prophecy(**prophecy_dict))
        
        # Write
        write_prophecy_archive(prophecies, output_path)
        assert output_path.exists()
        
        # Load
        loaded = load_prophecy_archive(output_path)
        assert len(loaded) == 5
        
        # Verify immutable_hash and deterministic prophecy_id
        for prophecy in loaded:
            assert prophecy.immutable_hash
            assert len(prophecy.immutable_hash) == 64  # SHA256 hex = 64 chars
            assert len(prophecy.prophecy_id) == 64  # Deterministic SHA256 (64 hex)
            assert prophecy.symbol  # Normalized from t0
            assert prophecy.universe  # Normalized from t0


def test_prophecy_id_deterministic():
    """Test that prophecy_id is deterministic."""
    from jgod.oracle.archive_writer import generate_prophecy_id
    
    id1 = generate_prophecy_id("2025-12-16", "2330", "or-os.v1", "stub", "stub")
    id2 = generate_prophecy_id("2025-12-16", "2330", "or-os.v1", "stub", "stub")
    id3 = generate_prophecy_id("2025-12-16", "2331", "or-os.v1", "stub", "stub")
    
    assert id1 == id2  # Same inputs = same ID
    assert id1 != id3  # Different symbol = different ID
    assert len(id1) == 64  # SHA256 hex = 64 chars


def test_prophecy_backward_compat():
    """Test backward compat: t0.symbol/universe normalized to top level."""
    # Old format with symbol in t0
    old_dict = {
        "schema_version": "or-os.v1",
        "prophecy_id": "test" * 16,  # 64 chars
        "as_of_date": "2025-12-16",
        "t0": {
            "timestamp": "2025-12-16T14:00:00+08:00",
            "baseline_price": 100.0,
            "baseline_source": "stub",
            "symbol": "2330",  # Old: in t0
            "universe": "TOP50",  # Old: in t0
        },
        "top_bucket": "UP",
        "rank_in_bucket": 1,
        "resonance_tag": "STRONG",
        "conflict_score": 0.0,
        "forecast_matrix": {},
        "decision_footprint": {},
        "versions": {},
        "immutable_hash": "0" * 64,
    }
    
    # Should normalize using from_dict
    prophecy = Prophecy.from_dict(old_dict)
    assert prophecy.symbol == "2330"  # Moved to top level
    assert prophecy.universe == "TOP50"  # Moved to top level
    assert "symbol" not in prophecy.t0  # Removed from t0
    assert "universe" not in prophecy.t0  # Removed from t0


def test_archive_top100_structure():
    """Test archive has Top50Up + Top50Down structure."""
    from jgod.oracle.run_archive import run_archive
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        run_archive("2025-12-16", "top50", output_dir)
        
        archive_path = output_dir / "prophecies_2025-12-16.jsonl"
        assert archive_path.exists()
        
        prophecies = load_prophecy_archive(archive_path)
        assert len(prophecies) == 100
        
        # Check buckets
        up_count = sum(1 for p in prophecies if p.top_bucket == "UP")
        down_count = sum(1 for p in prophecies if p.top_bucket == "DOWN")
        assert up_count == 50
        assert down_count == 50
        
        # Check ranks
        up_ranks = [p.rank_in_bucket for p in prophecies if p.top_bucket == "UP"]
        down_ranks = [p.rank_in_bucket for p in prophecies if p.top_bucket == "DOWN"]
        assert sorted(up_ranks) == list(range(1, 51))
        assert sorted(down_ranks) == list(range(1, 51))
        
        # Check all have T1/T5/T10/T20/TM
        for prophecy in prophecies:
            assert "T1" in prophecy.forecast_matrix
            assert "T5" in prophecy.forecast_matrix
            assert "T10" in prophecy.forecast_matrix
            assert "T20" in prophecy.forecast_matrix
            assert "TM" in prophecy.forecast_matrix
            assert prophecy.immutable_hash
            assert len(prophecy.immutable_hash) == 64
