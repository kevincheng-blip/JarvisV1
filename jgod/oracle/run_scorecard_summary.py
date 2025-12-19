"""
CLI: Generate Oracle Scorecard Summary.
"""
import argparse
import json
import logging
from pathlib import Path

from jgod.oracle.scorecard_summary import calculate_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate Oracle Scorecard Summary")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--horizons", required=True, help="Horizons (comma-separated, e.g., T1,T5,T10,T20,TM)")
    parser.add_argument("--scorecard-dir", default="data/oracle/scorecards", help="Scorecard directory")
    parser.add_argument("--out", default="data/oracle/scorecards", help="Output directory")
    parser.add_argument("--universe", default="TOP50", help="Universe name")
    
    args = parser.parse_args()
    
    scorecard_dir = Path(args.scorecard_dir)
    output_dir = Path(args.out)
    
    # Parse horizons
    horizons = [h.strip() for h in args.horizons.split(",")]
    
    # Build scorecard paths
    scorecard_paths = {}
    for horizon in horizons:
        path = scorecard_dir / f"scorecard_{args.date}_{horizon}.jsonl"
        if path.exists():
            scorecard_paths[horizon] = path
        else:
            logger.warning(f"Scorecard not found: {path}")
    
    if not scorecard_paths:
        logger.error(f"No scorecards found for date {args.date}")
        return
    
    logger.info(f"Calculating summary for {len(scorecard_paths)} horizons")
    
    # Calculate summary
    summary = calculate_summary(
        scorecard_paths=scorecard_paths,
        as_of_date=args.date,
        universe=args.universe
    )
    
    # Write summary
    output_path = output_dir / f"scorecard_summary_{args.date}.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Summary written to {output_path}")


if __name__ == "__main__":
    main()
