"""
Test Oracle Price Sources (SQLite).
"""
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import pytest

from jgod.oracle.data_sources import SQLitePriceSource, get_baseline_price, get_truth_price


def test_sqlite_price_source_discovery():
    """Test SQLite table discovery."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Create test DB with tw_stock_daily table
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE tw_stock_daily (
                trade_date TEXT,
                stock_id TEXT,
                close REAL,
                PRIMARY KEY (trade_date, stock_id)
            )
        """)
        conn.execute("""
            INSERT INTO tw_stock_daily (trade_date, stock_id, close)
            VALUES ('2025-12-16', '2330', 550.0)
        """)
        conn.commit()
        conn.close()
        
        # Test discovery
        source = SQLitePriceSource(db_path)
        price, source_name, explain = source.get_close("2330", "2025-12-16")
        
        assert price == 550.0
        assert source_name == "sqlite"
        assert explain.get("exact_match") is True
        assert "tw_stock_daily" in explain.get("table", "")
        assert explain.get("col_date") == "trade_date"
        assert explain.get("col_symbol") == "stock_id"
        assert explain.get("col_close") == "close"
    finally:
        Path(db_path).unlink()


def test_sqlite_date_format_detection():
    """Test date format detection (YYYY-MM-DD vs YYYYMMDD)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE tw_stock_daily (
                trade_date TEXT,
                stock_id TEXT,
                close REAL
            )
        """)
        # Insert with YYYYMMDD format
        conn.execute("""
            INSERT INTO tw_stock_daily (trade_date, stock_id, close)
            VALUES ('20251216', '2330', 600.0)
        """)
        conn.commit()
        conn.close()
        
        source = SQLitePriceSource(db_path)
        # Query with YYYY-MM-DD format, should still find it
        price, source_name, explain = source.get_close("2330", "2025-12-16")
        
        assert price == 600.0
        assert source_name == "sqlite"
        assert explain.get("date_format_used") in ["yyyymmdd", "yyyy_mm_dd"]
    finally:
        Path(db_path).unlink()


def test_sqlite_fallback_to_recent_trading_day():
    """Test fallback to recent trading day when exact date not found."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE tw_stock_daily (
                trade_date TEXT,
                stock_id TEXT,
                close REAL,
                PRIMARY KEY (trade_date, stock_id)
            )
        """)
        # Insert data for 2025-12-15 (1 day before)
        conn.execute("""
            INSERT INTO tw_stock_daily (trade_date, stock_id, close)
            VALUES ('2025-12-15', '2330', 545.0)
        """)
        conn.commit()
        conn.close()
        
        source = SQLitePriceSource(db_path)
        price, source_name, explain = source.get_close("2330", "2025-12-16", max_lookback_days=7)
        
        assert price == 545.0
        assert source_name == "sqlite"
        assert explain.get("exact_match") is False
        assert explain.get("lookback_days") == 1
    finally:
        Path(db_path).unlink()


def test_sqlite_fallback_to_stub():
    """Test fallback to stub when SQLite has no data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE tw_stock_daily (
                trade_date TEXT,
                stock_id TEXT,
                close REAL
            )
        """)
        conn.commit()
        conn.close()
        
        # No data in DB
        price, source_name, explain = get_baseline_price("2330", "2025-12-16", db_path)
        
        assert price > 0
        assert source_name == "stub"
        # Should have sqlite_fallback reason (from fallback logic)
        assert explain.get("reason") == "sqlite_fallback"
    finally:
        Path(db_path).unlink()


def test_sqlite_source_counts():
    """Test that source counts are tracked correctly."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE tw_stock_daily (
                trade_date TEXT,
                stock_id TEXT,
                close REAL
            )
        """)
        conn.execute("""
            INSERT INTO tw_stock_daily (trade_date, stock_id, close)
            VALUES ('2025-12-16', '2330', 550.0)
        """)
        conn.commit()
        conn.close()
        
        # Test baseline (should get SQLite)
        price1, source1, _ = get_baseline_price("2330", "2025-12-16", db_path)
        assert source1 == "sqlite"
        assert price1 == 550.0
        
        # Test truth for non-existent date (should get stub after lookback fails)
        # Use a date far in the future (2026-01-01) - but lookback might find 2025-12-16
        # So use a symbol that doesn't exist in DB
        price2, source2, _ = get_truth_price("9999", "2026-01-01", db_path)
        assert source2 == "stub"
        assert price2 > 0  # Stub price should be positive
    finally:
        Path(db_path).unlink()
