"""
Execution API Schemas

Pydantic schemas for Execution API responses.
"""

from typing import Optional, Dict, Literal
from pydantic import BaseModel, Field


class LedgerPositionSchema(BaseModel):
    """Schema for ledger position."""
    qty: int = Field(0, description="Position quantity")
    avg_cost: float = Field(0.0, description="Average cost")
    market_value: float = Field(0.0, description="Market value")
    unrealized_pnl: float = Field(0.0, description="Unrealized P&L")


class LedgerSnapshotSchema(BaseModel):
    """Schema for ledger snapshot."""
    symbol: str = Field(..., description="Stock symbol")
    cash: float = Field(0.0, description="Cash balance")
    position: LedgerPositionSchema = Field(default_factory=lambda: LedgerPositionSchema(), description="Position state")
    realized_pnl: float = Field(0.0, description="Realized P&L")
    unrealized_pnl: float = Field(0.0, description="Unrealized P&L")
    nav: float = Field(0.0, description="Net Asset Value")
    last_price: float = Field(0.0, description="Last market price")
    updated_at: str = Field("", description="Last update timestamp (ISO format)")


class OrderRequestSchema(BaseModel):
    """Schema for order request."""
    symbol: str = Field(..., description="Stock symbol")
    side: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Order side")
    qty: int = Field(0, description="Order quantity")
    reason: str = Field("", description="Order reason (Traditional Chinese)")
    target_position_scale: float = Field(0.0, description="Target position scale")
    current_position_scale: float = Field(0.0, description="Current position scale")


class ExecutionSimulateResponseSchema(BaseModel):
    """Response schema for order simulation."""
    symbol: str = Field(..., description="Stock symbol")
    ledger: LedgerSnapshotSchema = Field(..., description="Ledger snapshot")
    decision_v3: Dict = Field(default_factory=dict, description="Decision V3 result")
    order_request: OrderRequestSchema = Field(..., description="Generated order request")
    price: float = Field(0.0, description="Price used for simulation")
    has_data: bool = Field(False, description="Whether simulation has valid data")


class LedgerResponseSchema(BaseModel):
    """Response schema for ledger latest/recompute."""
    snapshot_id: str = Field("", description="Snapshot ID (empty if default)")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    symbol: str = Field(..., description="Stock symbol")
    ledger: LedgerSnapshotSchema = Field(..., description="Ledger snapshot")
    is_default: bool = Field(False, description="Whether this is a default (empty) ledger")

