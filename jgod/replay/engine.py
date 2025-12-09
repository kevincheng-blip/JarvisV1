"""Error Replay Engine v1

Core engine for building replay reports from error events.
"""

import logging
from datetime import datetime, date
from typing import Optional
from pathlib import Path

from jgod.replay.models import (
    ReplayMeta,
    PricePoint,
    FactorPoint,
    TradePoint,
    ReplayDiagnosis,
    ReplayReport,
)
from jgod.replay.data_access import (
    ReplayNotFoundError,
    _load_error_event,
    _load_price_series,
    _load_factor_series,
    _load_trades,
)

logger = logging.getLogger(__name__)


class ErrorReplayEngineV1:
    """Error Replay Engine v1
    
    Builds comprehensive replay reports for error events, including
    price series, factor data, trade records, and diagnostic analysis.
    """
    
    def __init__(self, db_session=None, knowledge_brain=None):
        """Initialize Error Replay Engine
        
        Args:
            db_session: SQLAlchemy database session (optional)
            knowledge_brain: KnowledgeBrain instance (optional, for Doctrine refs)
        """
        self.db_session = db_session
        self.knowledge_brain = knowledge_brain
    
    def build_replay_report(self, error_id: str, error_reports_path: Optional[Path] = None) -> ReplayReport:
        """Build a complete replay report for an error event
        
        High-level entry point:
        1. Load error event by error_id
        2. Extract symbol, date, error_type, human_summary
        3. Load price series, factor series, trades
        4. Generate diagnosis
        5. Return ReplayReport
        
        Args:
            error_id: Unique identifier for the error event
            error_reports_path: Path to error_reports.jsonl (optional)
        
        Returns:
            ReplayReport object
        
        Raises:
            ReplayNotFoundError: If error event not found
        """
        # Step 1: Load error event
        error_record = _load_error_event(error_id, error_reports_path)
        
        # Step 2: Extract metadata
        symbol = error_record.get("symbol", "")
        error_type = error_record.get("error_type")
        pnl_impact = error_record.get("pnl")
        
        # Parse timestamp to get date
        timestamp_str = error_record.get("timestamp", "")
        error_date = date.today()  # Default fallback
        
        if timestamp_str:
            try:
                if isinstance(timestamp_str, str):
                    error_datetime = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    error_date = error_datetime.date()
            except Exception as e:
                logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}, using today")
        
        # Extract human_summary from analysis
        analysis = error_record.get("analysis", {})
        human_summary = None
        if analysis:
            # Try to build summary from analysis fields
            summary_parts = []
            if analysis.get("knowledge_gap_notes"):
                summary_parts.extend(analysis["knowledge_gap_notes"][:1])
            if analysis.get("utilization_gap_reasons"):
                summary_parts.extend(analysis["utilization_gap_reasons"][:1])
            if summary_parts:
                human_summary = " ".join(summary_parts)
            else:
                human_summary = error_record.get("notes") or error_record.get("human_summary")
        
        meta = ReplayMeta(
            error_id=error_id,
            symbol=symbol,
            date=error_date,
            timeframe=error_record.get("timeframe", "daily"),
            error_type=error_type,
            human_summary=human_summary,
            pnl_impact=pnl_impact
        )
        
        # Step 3: Load data series
        price_series = _load_price_series(symbol, error_date, self.db_session)
        factor_series = _load_factor_series(symbol, error_date, self.db_session)
        trades = _load_trades(symbol, error_date, self.db_session)
        
        # Step 4: Build diagnosis
        diagnosis = self._build_diagnosis(error_record, price_series, factor_series, trades)
        
        # Step 5: Build and return report
        report = ReplayReport(
            meta=meta,
            price_series=price_series,
            factor_series=factor_series,
            trades=trades,
            diagnosis=diagnosis
        )
        
        logger.info(f"Built replay report for error {error_id}: {len(price_series)} price points, "
                   f"{len(factor_series)} factor points, {len(trades)} trades")
        
        return report
    
    def _build_diagnosis(
        self,
        error_record: dict,
        price_series: list[PricePoint],
        factor_series: list[FactorPoint],
        trades: list[TradePoint]
    ) -> ReplayDiagnosis:
        """Build diagnostic analysis
        
        v1 uses rule-based logic + Doctrine suggestions (if available).
        Future versions can add LLM-based analysis.
        
        Args:
            error_record: Error event dictionary
            price_series: List of price points
            factor_series: List of factor points
            trades: List of trade points
        
        Returns:
            ReplayDiagnosis object
        """
        error_type = error_record.get("error_type", "")
        analysis = error_record.get("analysis", {})
        
        # Rule-based root cause
        root_cause = "Unknown error type"
        contributing_factors = []
        missed_signals = []
        
        if error_type == "stop_loss_too_late":
            root_cause = "停損太慢，價格破底後才出場"
            contributing_factors.append("停損點位設定過寬")
            contributing_factors.append("未及時反應價格變化")
            if price_series:
                # Check if price dropped significantly
                if len(price_series) >= 2:
                    first_close = price_series[0].close
                    last_close = price_series[-1].close
                    if last_close < first_close * 0.95:
                        missed_signals.append(f"價格跌幅超過 5% ({first_close:.2f} → {last_close:.2f})")
        
        elif error_type == "direction":
            root_cause = "方向判斷錯誤"
            contributing_factors.append("趨勢判斷失準")
            if factor_series:
                factor_point = factor_series[0] if factor_series else None
                if factor_point and factor_point.raw_score:
                    if factor_point.raw_score > 0:
                        missed_signals.append("系統給出正向分數，但實際走勢相反")
        
        elif error_type == "timing":
            root_cause = "進出場時機不佳"
            contributing_factors.append("時機判斷錯誤")
        
        else:
            # Generic fallback
            root_cause = f"錯誤類型: {error_type or 'UNKNOWN'}"
            if analysis.get("knowledge_gap_notes"):
                contributing_factors.extend(analysis["knowledge_gap_notes"][:3])
        
        # Extract Doctrine references from analysis
        doctrine_refs = []
        if analysis:
            doctrine_suggestions = analysis.get("doctrine_suggestions", [])
            for suggestion in doctrine_suggestions:
                book_id = suggestion.get("book_id", "")
                section_id = suggestion.get("section_id", "")
                if book_id and section_id:
                    doctrine_refs.append(f"{book_id}#{section_id}")
        
        # If no trades, note it
        if not trades:
            contributing_factors.append("本日無實際下單紀錄")
        
        return ReplayDiagnosis(
            root_cause=root_cause,
            contributing_factors=contributing_factors,
            missed_signals=missed_signals,
            doctrine_refs=doctrine_refs
        )

