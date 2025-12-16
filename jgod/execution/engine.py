"""
Execution Engine: Real-time event-driven execution

v0.6.11-A11: Main execution engine for real-time trading
Replaces WalkForwardRunner as the primary execution core.
"""

import logging
import threading
import time
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum

from jgod.data.data_service_interface import DataServiceInterface
from jgod.data.data_service import DefaultDataService
from jgod.decision_v3.engine import DecisionEngineV3
from jgod.config.doctrine import load_doctrine, DoctrineConfig
from jgod.broker.interface import BrokerAdapterInterface, OrderRequest
from jgod.execution.order_engine import OrderGenerationEngine

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Execution engine status."""
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


class ExecutionEngine:
    """
    Execution Engine: Real-time event-driven execution.
    
    v0.6.11-A11: Main execution engine for real-time trading.
    Replaces WalkForwardRunner as the primary execution core.
    
    Behavior:
    - Singleton pattern (one instance per process)
    - Event-driven tick loop (fixed interval or data-driven)
    - Each tick: get_latest_data → decide → generate_orders → broker.place_order
    """
    
    _instance: Optional['ExecutionEngine'] = None
    _lock = threading.Lock()
    
    def __init__(
        self,
        data_service: Optional[DataServiceInterface] = None,
        broker: Optional[BrokerAdapterInterface] = None,
        *,
        tick_interval: float = 5.0,  # Seconds
        doctrine_version: str = "v1.0",
        feature_version: str = "v1.0",
    ):
        """
        Initialize Execution Engine.
        
        v0.6.12-A12: Added state_store, metrics_logger, alerting_service.
        
        Args:
            data_service: DataServiceInterface (if None, creates DefaultDataService)
            broker: BrokerAdapterInterface (if None, creates PaperTradingAdapter)
            tick_interval: Tick interval in seconds (for fixed interval mode)
            doctrine_version: Doctrine version
            feature_version: Feature version
        """
        if data_service is None:
            self.data_service = DefaultDataService(use_mock_mdts=False)
        else:
            self.data_service = data_service
        
        if broker is None:
            from jgod.broker.paper_adapter import PaperTradingAdapter
            self.broker = PaperTradingAdapter(initial_cash=1_000_000.0)
        else:
            self.broker = broker
        
        self.tick_interval = tick_interval
        self.doctrine_version = doctrine_version
        self.feature_version = feature_version
        
        self.decision_engine = DecisionEngineV3()
        self.order_engine = OrderGenerationEngine()
        
        # v0.6.12-A12: State persistence and monitoring
        self.state_store = ExecutionStateStore()
        self.metrics_logger = MetricsLogger()
        self.alerting_service = AlertingService()
        
        # State
        self.status = ExecutionStatus.STOPPED
        self._tick_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._symbols: List[str] = []
        self._last_tick_time: Optional[str] = None
        
        # Subscribe to fills
        self.broker.subscribe_fills(self._on_fill)
    
    @classmethod
    def get_instance(cls) -> 'ExecutionEngine':
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def start(self, symbols: List[str]) -> bool:
        """
        Start execution engine.
        
        v0.6.12-A12: Loads state from state_store before starting.
        
        Args:
            symbols: List of symbols to trade
            
        Returns:
            True if started successfully
        """
        if self.status == ExecutionStatus.RUNNING:
            logger.warning("Execution engine already running")
            return False
        
        # v0.6.12-A12: Load state before starting
        saved_state = self.state_store.load_state()
        if saved_state:
            self._last_tick_time = saved_state.get("last_tick_time")
            logger.info(f"Restored state: last_tick_time={self._last_tick_time}")
        
        self._symbols = symbols
        self.status = ExecutionStatus.RUNNING
        self._stop_event.clear()
        
        # Start tick loop thread
        self._tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._tick_thread.start()
        
        logger.info(f"Execution engine started for symbols: {symbols}")
        
        # v0.6.13-A13: Write intelligence status - ExecutionEngine ONLINE
        self._update_intelligence_status_on_start()
        
        # Save state
        self._save_state()
        
        return True
    
    def stop(self) -> bool:
        """
        Stop execution engine.
        
        Returns:
            True if stopped successfully
        """
        if self.status == ExecutionStatus.STOPPED:
            logger.warning("Execution engine already stopped")
            return False
        
        self.status = ExecutionStatus.STOPPED
        self._stop_event.set()
        
        if self._tick_thread and self._tick_thread.is_alive():
            self._tick_thread.join(timeout=5.0)
        
        logger.info("Execution engine stopped")
        return True
    
    def get_status(self) -> Dict:
        """
        Get execution engine status.
        
        Returns:
            Status dict
        """
        return {
            "status": self.status.value,
            "symbols": self._symbols,
            "tick_interval": self.tick_interval,
            "doctrine_version": self.doctrine_version,
            "feature_version": self.feature_version,
        }
    
    def _tick_loop(self) -> None:
        """
        Main tick loop (runs in separate thread).
        
        v0.6.12-A12: Added try/except guard to prevent thread termination.
        """
        logger.info("Tick loop started")
        
        while not self._stop_event.is_set() and self.status == ExecutionStatus.RUNNING:
            tick_start = time.time()
            
            try:
                self._tick()
                
                # Log successful tick
                tick_duration_ms = (time.time() - tick_start) * 1000
                self.metrics_logger.log_timer("tick_duration_ms", tick_duration_ms)
                self.metrics_logger.increment_counter("ticks_success")
                
                # Update last tick time
                self._last_tick_time = datetime.now().isoformat()
                
                # v0.6.13-A13: Update intelligence status - tick success
                self._update_intelligence_status_tick_success()
                
            except Exception as e:
                # v0.6.12-A12: Critical error - alert but continue
                tick_duration_ms = (time.time() - tick_start) * 1000
                self.metrics_logger.log_timer("tick_duration_ms", tick_duration_ms)
                self.metrics_logger.increment_counter("ticks_error")
                
                self.alerting_service.send_alert(
                    level="CRITICAL",
                    message=f"Tick error: {str(e)}",
                    context={
                        "symbols": self._symbols,
                        "tick_duration_ms": tick_duration_ms,
                    },
                )
                
                logger.error(f"Tick error (continuing): {e}", exc_info=True)
                # Continue - do not set status to ERROR or terminate thread
            
            # Save state after each tick
            self._save_state()
            
            # Wait for next tick (fixed interval)
            self._stop_event.wait(timeout=self.tick_interval)
        
        logger.info("Tick loop stopped")
    
    def _tick(self) -> None:
        """
        Execute one tick.
        
        v0.6.12-A12: Added metrics logging and alerting.
        
        Flow:
        1. get_latest_data
        2. decide()
        3. generate_orders()
        4. broker.place_order()
        5. receive fills (callback)
        6. ledger update (handled by broker)
        """
        current_time = datetime.now()
        date_str = current_time.strftime("%Y-%m-%d")
        
        # Load doctrine
        doctrine_config = load_doctrine(self.doctrine_version)
        if doctrine_config is None:
            doctrine_config = DoctrineConfig(version=self.doctrine_version)
        
        # Process each symbol
        for symbol in self._symbols:
            try:
                # Step 1: Get latest data (v0.6.12-A12: handle None gracefully)
                features = self.data_service.get_latest_data(symbol, current_time)
                if not features:
                    self.alerting_service.send_alert(
                        level="WARN",
                        message=f"No data for {symbol} at {current_time}",
                        context={"symbol": symbol, "date": date_str},
                    )
                    logger.warning(f"No data for {symbol} at {current_time}")
                    continue  # Skip tick, do not raise
                
                # Step 2: Compute decision (v0.6.12-A12: log latency)
                decide_start = time.time()
                decision_result = self.decision_engine.decide(
                    symbol=symbol,
                    mode="performance",
                    limit=60,
                    k=5,
                    as_of_date=current_time.date(),
                    features=features,
                    doctrine_config=doctrine_config,
                    feature_subset=None,
                )
                decide_latency_ms = (time.time() - decide_start) * 1000
                self.metrics_logger.log_timer("decide_latency_ms", decide_latency_ms, tags={"symbol": symbol})
                
                # Alert if decide() is slow
                if decide_latency_ms > 100:
                    self.alerting_service.send_alert(
                        level="WARN",
                        message=f"decide() latency > 100ms: {decide_latency_ms:.2f}ms",
                        context={"symbol": symbol, "latency_ms": decide_latency_ms},
                    )
                
                # Step 3: Generate orders (v0.6.11-A11: uses broker, not FillEngine)
                # Get account balance for order generation
                account_balance = self.broker.get_account_balance()
                positions = self.broker.get_positions()
                
                # Get current price
                ohlcv_dict = self.data_service.get_ohlcv(symbol, date_str)
                if not ohlcv_dict:
                    continue
                current_price = ohlcv_dict.get("close", 0.0)
                
                # Generate order request
                order_request = self.order_engine.generate_orders(
                    decision=decision_result,
                    ledger=None,  # v0.6.11-A11: No direct ledger access
                    price=current_price,
                    account_balance=account_balance,
                    positions=positions,
                )
                
                # Step 4: Place order via broker (v0.6.12-A12: alert on broker exception)
                if order_request and order_request.side != "HOLD":
                    try:
                        order_id = self.broker.place_order(order_request)
                        logger.debug(f"Placed order {order_id} for {symbol}: {order_request.side} {order_request.qty}")
                    except Exception as broker_error:
                        self.alerting_service.send_alert(
                            level="CRITICAL",
                            message=f"Broker exception for {symbol}: {str(broker_error)}",
                            context={"symbol": symbol, "order_request": str(order_request)},
                        )
                        raise  # Re-raise to be caught by outer try/except
                
            except Exception as e:
                # v0.6.12-A12: Log error but let _tick_loop handle it
                logger.error(f"Tick error for {symbol}: {e}", exc_info=True)
                raise  # Re-raise to be caught by _tick_loop
    
    def _save_state(self) -> None:
        """Save execution state to state_store."""
        state = {
            "engine_status": self.status.value,
            "last_tick_time": self._last_tick_time,
            "symbols": self._symbols,
            "tick_interval": self.tick_interval,
            "doctrine_version": self.doctrine_version,
            "feature_version": self.feature_version,
            "broker_status": "connected",  # Simplified for now
        }
        self.state_store.save_state(state)
    
    def _on_fill(self, fill) -> None:
        """
        Handle fill callback.
        
        Args:
            fill: Fill object from broker
        """
        logger.info(f"Fill received: {fill.symbol} {fill.side} {fill.qty} @ {fill.price}")

