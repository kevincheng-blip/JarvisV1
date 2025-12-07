#!/usr/bin/env python
"""
Temporary debug script to check database data for 2330 in date range 2024-06-01 to 2024-06-15
"""

import sqlite3
import sys
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent
db_path = project_root / "data" / "jgod_tw_stock.db"

if not db_path.exists():
    print(f"❌ Database file not found: {db_path}")
    sys.exit(1)

print("=" * 70)
print(f"📊 Checking database: {db_path}")
print("=" * 70)
print()

# Connect to database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Query parameters
symbol = "2330"
start_date = "2024-06-01"
end_date = "2024-06-15"

print(f"Symbol: {symbol}")
print(f"Date range: {start_date} to {end_date}")
print()

# (A) Daily bars count
print("(A) Daily Bars Count:")
print("-" * 70)
query_a = """
    SELECT COUNT(*) FROM daily_bars
    WHERE symbol = ?
    AND date BETWEEN ? AND ?;
"""
cursor.execute(query_a, (symbol, start_date, end_date))
count_a = cursor.fetchone()[0]
print(f"   COUNT(*) = {count_a}")
print()

# (B) Indicator snapshots count
print("(B) Indicator Snapshots Count:")
print("-" * 70)
query_b = """
    SELECT COUNT(*) FROM indicator_snapshots
    WHERE symbol = ?
    AND date BETWEEN ? AND ?;
"""
cursor.execute(query_b, (symbol, start_date, end_date))
count_b = cursor.fetchone()[0]
print(f"   COUNT(*) = {count_b}")
print()

# (C) Prediction snapshots count
print("(C) Prediction Snapshots Count:")
print("-" * 70)
query_c = """
    SELECT COUNT(*) FROM prediction_snapshots
    WHERE symbol = ?
    AND date BETWEEN ? AND ?;
"""
cursor.execute(query_c, (symbol, start_date, end_date))
count_c = cursor.fetchone()[0]
print(f"   COUNT(*) = {count_c}")
print()

# Summary
print("=" * 70)
print("📋 Summary:")
print("=" * 70)
print(f"  Daily Bars:        {count_a}")
print(f"  Indicator Snapshots: {count_b}")
print(f"  Prediction Snapshots: {count_c}")
print("=" * 70)

# Close connection
conn.close()

