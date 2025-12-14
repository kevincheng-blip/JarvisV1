"""
Walk-Forward Runner: Daily cycle orchestrator

v0.6.8-A8: Walk-Forward Runner & Learning Layers
v0.6.9-A9: Auto-Pilot Activation & Guard Rails (Conditional Self-Evolution + Async Learning)
Strictly uses only T-1 data, triggers learning cycles, writes append-only logs.
"""

import logging
import concurrent.futures
from typing import List, Dict, Optional
from datetime import datetime, timedelta, date

from jgod.data.feature_service import FeatureService
from jgod.data.market_data_service import MarketDataService
from jgod.data.data_service_interface import DataServiceInterface
from jgod.data.data_service import DefaultDataService
from jgod.execution.virtual_ledger import VirtualLedger
from jgod.execution.order_engine import OrderGenerationEngine
from jgod.execution.fill_engine import FillEngine
from jgod.decision_v3.engine import DecisionEngineV3
from jgod.config.doctrine import DoctrineConfig, load_doctrine, apply_patch
from jgod.research.storage import save_daily_log, load_daily_logs, save_snapshot, save_notification
from jgod.research.snapshot import create_snapshot_payload
from jgod.learning.models import PatchStatus

logger = logging.getLogger(__name__)


class WalkForwardRunner:
    """
    Walk-Forward Runner: Orchestrates daily cycles and triggers learning layers.
    
    v0.6.8-A8: Strictly uses only T-1 data, no future data leakage.
    """
    
    def __init__(
        self,
        use_mock_mdts: bool = False,
        *,
        autopilot_enabled: bool = False,
        autopilot_apply_only_when_status_auto: bool = True,
        async_learning_enabled: bool = True,
        data_service: Optional[DataServiceInterface] = None,
    ):
        """
        Initialize WalkForwardRunner.
        
        v0.6.9-A9: Added feature flags for auto-pilot and async learning.
        v0.6.10-A10: Added data_service parameter for portfolio coordination.
        
        Args:
            use_mock_mdts: If True, use mock MDTS (for testing)
            autopilot_enabled: If True, enable auto-apply for AUTO_APPLY patches
            autopilot_apply_only_when_status_auto: If True, only auto-apply when status is AUTO_APPLY
            async_learning_enabled: If True, run learning layers asynchronously
            data_service: Optional DataServiceInterface (if None, creates default)
        """
        if data_service is None:
            self.data_service = DefaultDataService(use_mock_mdts=use_mock_mdts)
        else:
            self.data_service = data_service
        
        # Keep legacy services for backward compatibility
        self.mdts = MarketDataService(use_mock=use_mock_mdts)
        self.feature_service = FeatureService(use_mock_mdts=use_mock_mdts)
        self.decision_engine = DecisionEngineV3()
        self.autopilot_enabled = autopilot_enabled
        self.autopilot_apply_only_when_status_auto = autopilot_apply_only_when_status_auto
        self.async_learning_enabled = async_learning_enabled
        
        # v0.6.10-A10: Time sync tracking
        self._current_date: Optional[str] = None
    
    def run_daily_cycle(
        self,
        symbol: str,
        date_str: str,
        *,
        doctrine_version: str = "v1.0",
        feature_version: str = "v1.0",
        feature_lookback: int = 60,
        feature_subset: Optional[List[str]] = None,
    ) -> Dict:
        """
        Run daily walkforward cycle for a symbol and date.
        
        Strictly uses only T-1 data (no future data leakage).
        
        Args:
            symbol: Stock symbol
            date_str: Date string (YYYY-MM-DD)
            doctrine_version: Doctrine version to use
            feature_version: Feature version to use
            feature_lookback: Feature lookback days
            feature_subset: Optional feature subset (from Method Layer)
            
        Returns:
            Dict with daily cycle result (nav, decision, order, fill, etc.)
        """
        # Step 1: Load doctrine config
        doctrine_config = load_doctrine(doctrine_version)
        if doctrine_config is None:
            logger.warning(f"Doctrine version {doctrine_version} not found, using default")
            doctrine_config = DoctrineConfig(version=doctrine_version)
        
        # v0.6.10-A10: Time sync check
        if self._current_date is not None and self._current_date != date_str:
            error_msg = f"Time sync error: runner date mismatch ({self._current_date} vs {date_str})"
            logger.error(error_msg)
            raise ValueError(error_msg)
        self._current_date = date_str
        
        # Step 2: Get features from DataService (v0.6.10-A10: use data_service)
        features = self.data_service.get_features(
            symbol=symbol,
            date=date_str,
            version=feature_version,
            lookback=feature_lookback,
        )
        
        # Step 3: Get OHLCV for the date (v0.6.10-A10: use data_service)
        ohlcv_dict = self.data_service.get_ohlcv(symbol, date_str)
        if ohlcv_dict is None:
            logger.warning(f"No OHLCV data for {symbol} on {date_str}")
            return {
                "symbol": symbol,
                "date": date_str,
                "error": "No OHLCV data",
                "nav": 0.0,
            }
        
        # Convert dict to OHLCVSnapshot-like object for compatibility
        from jgod.data.market_data_service import OHLCVSnapshot
        ohlcv = OHLCVSnapshot(
            symbol=symbol,
            date=ohlcv_dict["date"],
            open=ohlcv_dict["open"],
            high=ohlcv_dict["high"],
            low=ohlcv_dict["low"],
            close=ohlcv_dict["close"],
            volume=ohlcv_dict["volume"],
        )
        
        # Step 4: Compute decision (with features and doctrine)
        try:
            decision_result = self.decision_engine.decide(
                symbol=symbol,
                mode="performance",
                limit=60,
                k=5,
                as_of_date=date.fromisoformat(date_str),
                features=features,  # v0.6.10-A10: use features from data_service
                doctrine_config=doctrine_config,
                feature_subset=feature_subset,
            )
        except Exception as e:
            logger.error(f"Failed to compute decision for {symbol} on {date_str}: {e}", exc_info=True)
            # Return error state
            return {
                "symbol": symbol,
                "date": date_str,
                "error": f"Decision computation failed: {str(e)}",
                "nav": 0.0,
            }
        
        # Step 5: Initialize or load ledger state
        # v0.6.10-A10: For portfolio mode, ledger should be passed in or loaded from previous state
        # For now, create new ledger if not in portfolio mode
        # In portfolio mode, PortfolioManager manages ledgers
        if not hasattr(self, '_ledger') or self._ledger is None:
            self._ledger = VirtualLedger(symbol=symbol, cash=1_000_000.0)
        ledger = self._ledger
        
        # Step 6: Mark to market
        ledger.mark_to_market(symbol, ohlcv.close)
        
        # Step 7: Generate order
        order = OrderGenerationEngine.generate_orders(
            decision=decision_result,
            ledger=ledger,
            price=ohlcv.close,
        )
        
        # Step 8: Execute fill
        fill = FillEngine.execute(order=order, ohlcv=ohlcv)
        
        # Step 9: Apply fill to ledger
        ledger.apply_fill(fill)
        
        # Step 10: Mark to market again
        ledger.mark_to_market(symbol, ohlcv.close)
        
        # Step 11: Create daily log entry
        pos = ledger.positions.get(symbol)
        log_entry = {
            "symbol": symbol,
            "date": date_str,
            "nav": ledger.nav,
            "cash": ledger.cash,
            "position": {
                "qty": pos.qty if pos else 0,
                "avg_cost": pos.avg_cost if pos else 0.0,
            },
            "realized_pnl": ledger.realized_pnl,
            "unrealized_pnl": ledger.unrealized_pnl,
            "ohlcv": {
                "open": ohlcv.open,
                "high": ohlcv.high,
                "low": ohlcv.low,
                "close": ohlcv.close,
                "volume": ohlcv.volume,
            },
            "features_summary": {
                "SMA_5": features.get("SMA_5"),
                "SMA_20": features.get("SMA_20"),
                "RSI_14": features.get("RSI_14"),
                "RET_1D": features.get("RET_1D"),
            },
            "decision": {
                "primary_strategy": decision_result.selected_primary_strategy,
                "position_scale": decision_result.risk_plan.position_scale if decision_result.risk_plan else 0.0,
                "risk_state": decision_result.risk_plan.risk_state if decision_result.risk_plan else "RISK_OFF",
                "confidence": decision_result.confidence,
            },
            "order": {
                "side": order.side,
                "qty": order.qty,
                "reason": order.reason,
            },
            "fill": {
                "qty_executed": fill.qty_executed,
                "fill_price": fill.fill_price,
                "fee": fill.fee,
                "tax": fill.tax,
                "slippage": fill.slippage,
            },
            "doctrine_version": doctrine_version,
            "feature_version": feature_version,
        }
        
        # Step 12: Save daily log
        save_daily_log(log_entry)
        
        # Step 13: Check if learning cycle should be triggered
        learning_triggers = self._check_learning_triggers(symbol, date_str)
        log_entry["learning_triggers"] = learning_triggers
        
        # Step 14: Trigger learning layers if needed (v0.6.9-A9: with snapshot and async)
        if learning_triggers.get("thought_5d"):
            self._trigger_thought_layer(symbol, date_str, doctrine_version, feature_version)
        
        if learning_triggers.get("method_10d") or learning_triggers.get("method_20d"):
            window = 20 if learning_triggers.get("method_20d") else 10
            if self.async_learning_enabled:
                # Run asynchronously (non-blocking)
                self._trigger_method_layer_async(symbol, date_str, window, doctrine_version, feature_version)
            else:
                self._trigger_method_layer(symbol, date_str, window, doctrine_version, feature_version)
        
        if learning_triggers.get("strategy_60d"):
            if self.async_learning_enabled:
                # Run asynchronously (non-blocking)
                self._trigger_strategy_layer_async(symbol, date_str, doctrine_version, feature_version)
            else:
                self._trigger_strategy_layer(symbol, date_str, doctrine_version, feature_version)
        
        return log_entry
    
    def _trigger_thought_layer(
        self,
        symbol: str,
        date_str: str,
        doctrine_version: str = "v1.0",
        feature_version: str = "v1.0",
    ) -> None:
        """Trigger Thought Layer (5-day tuning advisor)."""
        try:
            from jgod.learning.tuning_advisor import analyze_and_suggest_patch, save_tuning_patch
            
            # v0.6.9-A9: Create snapshot
            start_date = (datetime.strptime(date_str, "%Y-%m-%d").date() - timedelta(days=5)).strftime("%Y-%m-%d")
            snapshot_payload = create_snapshot_payload(
                symbol=symbol,
                start_date=start_date,
                end_date=date_str,
                doctrine_version=doctrine_version,
                feature_version=feature_version,
                window=5,
                layer="thought",
            )
            save_snapshot(snapshot_payload)
            snapshot_id = snapshot_payload["snapshot_id"]
            
            patch = analyze_and_suggest_patch(symbol, date_str, window=5, snapshot_id=snapshot_id)
            if patch:
                save_tuning_patch(patch)
                
                # v0.6.9-A9: Auto-apply if enabled and status is AUTO_APPLY
                if (self.autopilot_enabled and
                    self.autopilot_apply_only_when_status_auto and
                    patch.status == PatchStatus.AUTO_APPLY):
                    try:
                        # Generate new version
                        new_version = f"{doctrine_version}.{patch.patch_id.split('-')[-1]}"
                        apply_patch(
                            base_version=doctrine_version,
                            patch={
                                "target": patch.target,
                                "changes": patch.changes,
                            },
                            new_version=new_version,
                            patch_id=patch.patch_id,
                            snapshot_id=snapshot_id,
                            layer="thought",
                        )
                        save_notification({
                            "event": "AUTO_APPLY",
                            "layer": "thought",
                            "patch_id": patch.patch_id,
                            "snapshot_id": snapshot_id,
                            "new_version": new_version,
                            "symbol": symbol,
                            "date": date_str,
                        })
                        logger.info(f"Auto-applied patch {patch.patch_id} -> {new_version}")
                    except Exception as e:
                        logger.error(f"Failed to auto-apply patch {patch.patch_id}: {e}", exc_info=True)
                else:
                    # Save notification for PENDING or REJECTED
                    save_notification({
                        "event": "PENDING" if patch.status == PatchStatus.PENDING_APPROVAL else "REJECTED",
                        "layer": "thought",
                        "patch_id": patch.patch_id,
                        "snapshot_id": snapshot_id,
                        "quality_score": patch.quality_score,
                        "symbol": symbol,
                        "date": date_str,
                    })
                
                logger.info(f"Thought Layer generated patch suggestion: {patch.patch_id} (status: {patch.status.value})")
        except Exception as e:
            logger.error(f"Failed to trigger Thought Layer for {symbol} on {date_str}: {e}", exc_info=True)
    
    def _trigger_method_layer(
        self,
        symbol: str,
        date_str: str,
        window: int,
        doctrine_version: str = "v1.0",
        feature_version: str = "v1.0",
    ) -> None:
        """Trigger Method Layer (10/20-day feature selector)."""
        try:
            from jgod.learning.feature_selector import analyze_and_suggest_subset, save_feature_subset
            
            # v0.6.9-A9: Create snapshot
            start_date = (datetime.strptime(date_str, "%Y-%m-%d").date() - timedelta(days=window)).strftime("%Y-%m-%d")
            snapshot_payload = create_snapshot_payload(
                symbol=symbol,
                start_date=start_date,
                end_date=date_str,
                doctrine_version=doctrine_version,
                feature_version=feature_version,
                window=window,
                layer="method",
            )
            save_snapshot(snapshot_payload)
            snapshot_id = snapshot_payload["snapshot_id"]
            
            subset = analyze_and_suggest_subset(symbol, date_str, window=window, snapshot_id=snapshot_id)
            if subset:
                save_feature_subset(subset)
                save_notification({
                    "event": subset.status.value,
                    "layer": "method",
                    "snapshot_id": snapshot_id,
                    "quality_score": subset.quality_score,
                    "symbol": symbol,
                    "date": date_str,
                })
                logger.info(f"Method Layer generated feature subset suggestion for {symbol} (status: {subset.status.value})")
        except Exception as e:
            logger.error(f"Failed to trigger Method Layer for {symbol} on {date_str}: {e}", exc_info=True)
    
    def _trigger_method_layer_async(
        self,
        symbol: str,
        date_str: str,
        window: int,
        doctrine_version: str = "v1.0",
        feature_version: str = "v1.0",
    ) -> None:
        """Trigger Method Layer asynchronously (non-blocking)."""
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            self._trigger_method_layer,
            symbol, date_str, window, doctrine_version, feature_version
        )
        # Don't wait for completion (fire and forget)
        logger.debug(f"Method Layer task submitted for {symbol} on {date_str}")
    
    def _trigger_strategy_layer(
        self,
        symbol: str,
        date_str: str,
        doctrine_version: str = "v1.0",
        feature_version: str = "v1.0",
    ) -> None:
        """Trigger Strategy Layer (60-day strategy allocator)."""
        try:
            from jgod.learning.strategy_allocator import analyze_and_suggest_allocation, save_strategy_allocation
            
            # v0.6.9-A9: Create snapshot
            start_date = (datetime.strptime(date_str, "%Y-%m-%d").date() - timedelta(days=60)).strftime("%Y-%m-%d")
            snapshot_payload = create_snapshot_payload(
                symbol=symbol,
                start_date=start_date,
                end_date=date_str,
                doctrine_version=doctrine_version,
                feature_version=feature_version,
                window=60,
                layer="strategy",
            )
            save_snapshot(snapshot_payload)
            snapshot_id = snapshot_payload["snapshot_id"]
            
            allocation = analyze_and_suggest_allocation(symbol, date_str, window=60, snapshot_id=snapshot_id)
            if allocation:
                save_strategy_allocation(allocation)
                save_notification({
                    "event": allocation.status.value,
                    "layer": "strategy",
                    "snapshot_id": snapshot_id,
                    "quality_score": allocation.quality_score,
                    "symbol": symbol,
                    "date": date_str,
                })
                logger.info(f"Strategy Layer generated allocation suggestion for {symbol} (status: {allocation.status.value})")
        except Exception as e:
            logger.error(f"Failed to trigger Strategy Layer for {symbol} on {date_str}: {e}", exc_info=True)
    
    def _trigger_strategy_layer_async(
        self,
        symbol: str,
        date_str: str,
        doctrine_version: str = "v1.0",
        feature_version: str = "v1.0",
    ) -> None:
        """Trigger Strategy Layer asynchronously (non-blocking)."""
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            self._trigger_strategy_layer,
            symbol, date_str, doctrine_version, feature_version
        )
        # Don't wait for completion (fire and forget)
        logger.debug(f"Strategy Layer task submitted for {symbol} on {date_str}")
    
    def _check_learning_triggers(
        self,
        symbol: str,
        date_str: str
    ) -> Dict:
        """
        Check if learning cycles should be triggered.
        
        Args:
            symbol: Stock symbol
            date_str: Current date (YYYY-MM-DD)
            
        Returns:
            Dict with trigger flags: {thought_5d, method_10d, method_20d, strategy_60d}
        """
        current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Load recent logs
        start_date = (current_date - timedelta(days=60)).strftime("%Y-%m-%d")
        logs = load_daily_logs(symbol, start_date, date_str, limit=100)
        
        if not logs:
            return {
                "thought_5d": False,
                "method_10d": False,
                "method_20d": False,
                "strategy_60d": False,
            }
        
        # Check if we have enough days
        log_dates = sorted(set(log.get("date") for log in logs if log.get("date")))
        
        # Thought Layer: Every 5 days
        thought_5d = len(log_dates) >= 5 and len(log_dates) % 5 == 0
        
        # Method Layer: Every 10/20 days
        method_10d = len(log_dates) >= 10 and len(log_dates) % 10 == 0
        method_20d = len(log_dates) >= 20 and len(log_dates) % 20 == 0
        
        # Strategy Layer: Every 60 days (quarterly)
        strategy_60d = len(log_dates) >= 60 and len(log_dates) % 60 == 0
        
        return {
            "thought_5d": thought_5d,
            "method_10d": method_10d,
            "method_20d": method_20d,
            "strategy_60d": strategy_60d,
        }
    
    def run_range(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        *,
        doctrine_version: str = "v1.0",
        feature_version: str = "v1.0",
        feature_lookback: int = 60,
        feature_subset: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Run walkforward for a date range.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            doctrine_version: Doctrine version
            feature_version: Feature version
            feature_lookback: Feature lookback days
            feature_subset: Optional feature subset
            
        Returns:
            List of daily log entries
        """
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        results = []
        current = start
        
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            
            try:
                log_entry = self.run_daily_cycle(
                    symbol=symbol,
                    date_str=date_str,
                    doctrine_version=doctrine_version,
                    feature_version=feature_version,
                    feature_lookback=feature_lookback,
                    feature_subset=feature_subset,
                )
                results.append(log_entry)
            except Exception as e:
                logger.error(f"Failed to run daily cycle for {symbol} on {date_str}: {e}", exc_info=True)
                results.append({
                    "symbol": symbol,
                    "date": date_str,
                    "error": str(e),
                })
            
            current += timedelta(days=1)
        
        return results

