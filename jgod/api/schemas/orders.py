"""
Orders API Schemas

定義 Orders 相關的 API 資料結構
"""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

from jgod.api.schemas.predictions import DoctrineFlag


class FinalOrderItem(BaseModel):
    """Final Order Item DTO
    
    對應前端 FinalOrder 型別
    """
    symbol: str = Field(..., description="股票代號")
    name: str = Field(..., description="股票名稱")
    action: str = Field(..., description="動作: BUY / SELL / HOLD", pattern="^(BUY|SELL|HOLD)$")
    quantity: float = Field(..., description="數量（股數或標準化單位）")
    final_score: float = Field(..., description="Final Score（經 Decision Layer 仲裁後）")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心度 (0~1)")
    doctrine_flags: List[DoctrineFlag] = Field(default_factory=list, description="Doctrine 風險標籤")
    status: Optional[str] = Field(None, description="狀態: PENDING / EXECUTED / CANCELLED")

