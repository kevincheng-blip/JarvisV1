"""
Predictions API Schemas

定義 Predictions 相關的 API 資料結構
與前端 warRoom.ts 型別對應
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DoctrineFlag(BaseModel):
    """Doctrine Flag DTO
    
    與前端 warRoom.ts DoctrineFlag 型別對應
    """
    code: str = Field(..., description="Flag 代碼，例如 'over_concentration'")
    severity: str = Field(..., description="嚴重程度: info / warning / critical", pattern="^(info|warning|critical)$")
    message: str = Field(..., description="短文字說明")
    doctrine_refs: List[str] = Field(default_factory=list, description="Doctrine 引用，例如 ['Book_03#S12', 'Book_08#R21']")


class TopLongItem(BaseModel):
    """Top Long Item DTO
    
    與前端 warRoom.ts TopLongItem 型別對應
    """
    symbol: str = Field(..., description="股票代號")
    name: str = Field(..., description="股票名稱")
    final_score: float = Field(..., description="Final Score（經 Decision Layer 仲裁後）")
    raw_score: float = Field(..., description="Raw Score（原始量化分數）")
    win_prob: Optional[float] = Field(None, ge=0.0, le=1.0, description="勝率估計 (0~1)")
    expected_return: Optional[float] = Field(None, description="預期報酬率")
    risk_level: Optional[str] = Field(None, description="風險等級: low / mid / high", pattern="^(low|mid|high)$")
    doctrine_flags: List[DoctrineFlag] = Field(default_factory=list, description="Doctrine 風險標籤")


class TopShortItem(BaseModel):
    """Top Short Item DTO
    
    與前端 warRoom.ts TopShortItem 型別對應
    結構與 TopLongItem 相同，語意上為空頭/避險
    """
    symbol: str = Field(..., description="股票代號")
    name: str = Field(..., description="股票名稱")
    final_score: float = Field(..., description="Final Score（經 Decision Layer 仲裁後）")
    raw_score: float = Field(..., description="Raw Score（原始量化分數）")
    risk_level: Optional[str] = Field(None, description="風險等級: low / mid / high", pattern="^(low|mid|high)$")
    doctrine_flags: List[DoctrineFlag] = Field(default_factory=list, description="Doctrine 風險標籤")

