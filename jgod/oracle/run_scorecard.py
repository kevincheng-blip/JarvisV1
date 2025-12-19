"""
CLI: Run Oracle Scorecard grading.
"""
import argparse
import logging
from pathlib import Path

from jgod.oracle.scorecard_grader import grade_archive

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate Oracle Scorecard")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--horizon", required=True, help="Horizon (T1, T5, T10, T20, TM)")
    parser.add_argument("--in", dest="input_dir", required=True, help="Input directory (prophecy archives)")
    parser.add_argument("--out", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.out)
    
    # Find archive file for date
    archive_path = input_dir / f"prophecies_{args.date}.jsonl"
    
    if not archive_path.exists():
        logger.error(f"Archive not found: {archive_path}")
        return
    
    # Output path
    output_path = output_dir / f"scorecard_{args.date}_{args.horizon}.jsonl"
    
    logger.info(f"Grading archive {archive_path} for horizon {args.horizon}")
    
    # Grade archive
    scorecard_rows = grade_archive(
        archive_path=archive_path,
        horizon=args.horizon,
        output_path=output_path,
        governance_snapshot=None,  # MVP: no governance snapshot
    )
    
    logger.info(f"Generated {len(scorecard_rows)} scorecard rows to {output_path}")


if __name__ == "__main__":
    main()
