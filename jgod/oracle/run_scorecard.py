"""
CLI: Run Oracle Scorecard grading (multi-horizon support).
"""
import argparse
import logging
from pathlib import Path

from jgod.oracle.scorecard_grader import grade_archive_multi_horizon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate Oracle Scorecard (multi-horizon)")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--horizons", required=True, help="Horizons (comma-separated, e.g., T1,T5,T10,T20,TM)")
    parser.add_argument("--in", dest="input_dir", required=True, help="Input directory (prophecy archives)")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--db-path", help="SQLite database path (optional)")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.out)
    
    # Find archive file for date
    archive_path = input_dir / f"prophecies_{args.date}.jsonl"
    
    if not archive_path.exists():
        logger.error(f"Archive not found: {archive_path}")
        return
    
    # Parse horizons
    horizons = [h.strip() for h in args.horizons.split(",")]
    logger.info(f"Grading archive {archive_path} for horizons: {horizons}")
    
    # Grade archive for all horizons
    results = grade_archive_multi_horizon(
        archive_path=archive_path,
        horizons=horizons,
        output_dir=output_dir,
        db_path=args.db_path,
        governance_snapshot=None,  # MVP: no governance snapshot
    )
    
    total_rows = sum(len(rows) for rows in results.values())
    logger.info(f"Generated {total_rows} total scorecard rows across {len(horizons)} horizons")


if __name__ == "__main__":
    main()
