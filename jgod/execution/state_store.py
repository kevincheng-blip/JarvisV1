"""
Execution State Store: Persistence for ExecutionEngine state

v0.6.12-A12: State persistence and recovery for production resilience
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutionStateStore:
    """
    Execution State Store: Persists and recovers ExecutionEngine state.
    
    v0.6.12-A12: Uses JSONL / local file (simulates Firestore for now).
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize ExecutionStateStore.
        
        Args:
            storage_path: Optional custom storage path (default: data/execution/state.json)
        """
        if storage_path is None:
            project_root = Path(__file__).resolve().parents[2]
            storage_dir = project_root / "data" / "execution"
            storage_dir.mkdir(parents=True, exist_ok=True)
            storage_path = storage_dir / "state.json"
        
        self.storage_path = storage_path
    
    def save_state(self, state: Dict) -> None:
        """
        Save execution state.
        
        Args:
            state: State dict with engine_status, last_tick_time, broker_status, etc.
        """
        # Add timestamp
        state["updated_at"] = datetime.now().isoformat()
        
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save execution state: {e}", exc_info=True)
            raise
    
    def load_state(self) -> Optional[Dict]:
        """
        Load execution state.
        
        Returns:
            State dict or None if not found
        """
        if not self.storage_path.exists():
            return None
        
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state
        except Exception as e:
            logger.error(f"Failed to load execution state: {e}", exc_info=True)
            return None
    
    def clear_state(self) -> None:
        """Clear execution state (for testing)."""
        if self.storage_path.exists():
            self.storage_path.unlink()

