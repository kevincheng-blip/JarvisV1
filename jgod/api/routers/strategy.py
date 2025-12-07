"""
Strategy API Router

Endpoints for Strategy & Signal Engine v1.

用途：
- 提供標準化的多空信號清單給 War Room / Path A 前端使用
- 這是「策略層」API，不是「原始預測層」API
- 與 /api/predictions/... 的關係：predictions 是單檔股票的預測結果，strategy/signals 是整日的多空清單匯總
"""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from jgod.strategy import StrategyEngineV1

router = APIRouter()

# Strategy Engine 實例（單例模式）
_strategy_engine = StrategyEngineV1()


@router.get("/v1/strategy/signals")
async def get_strategy_signals(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    universe: Optional[str] = Query(None, description="Universe name (optional, e.g., 'tw_top50_2024')"),
    long_limit: int = Query(30, description="Long candidates limit"),
    short_limit: int = Query(30, description="Short candidates limit"),
    min_score: float = Query(0.0, description="Minimum score threshold"),
    allow_short: bool = Query(True, description="Allow short list generation"),
):
    """
    Get strategy signals for a specific date.
    
    **用途**：
    - 專門給策略引擎、回測系統（Path A）、War Room UI 使用
    - 回傳當日的多空候選清單（Long Top N / Short Top N）
    
    **與 /api/predictions/... 的關係**：
    - `/api/predictions/...`：單檔股票的預測結果（原始層）
    - `/api/v1/strategy/signals`：整日的多空清單匯總（策略層）
    
    **查詢參數**：
    - date: 日期（必填，格式：YYYY-MM-DD）
    - universe: 股票池（選填，如果為 None 則取得所有有預測的股票）
    - long_limit: Long 候選清單上限（預設 30）
    - short_limit: Short 候選清單上限（預設 30）
    - min_score: 最低分數門檻（預設 0.0）
    - allow_short: 是否允許放空（預設 True）
    
    Returns:
        DailySignalSet JSON（包含 date, universe_size, params, long_candidates, short_candidates）
    """
    # Parse date
    try:
        as_of_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date}. Use YYYY-MM-DD")
    
    # Parse universe (if provided, split by comma)
    universe_list = None
    if universe:
        universe_list = [s.strip() for s in universe.split(",")]
    
    try:
        # Generate signals
        signal_set = _strategy_engine.generate_signals_for_date(
            date=as_of_date,
            universe=universe_list,
            long_limit=long_limit,
            short_limit=short_limit,
            min_score=min_score,
            allow_short=allow_short,
        )
        
        if signal_set.universe_size == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No prediction data found for {date}",
            )
        
        # Return DailySignalSet as JSON
        return signal_set.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating strategy signals: {str(e)}",
        )

