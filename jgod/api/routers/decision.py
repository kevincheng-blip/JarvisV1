"""
Decision API Router

Endpoints for Decision & Risk Engine v1.

用途：
- 提供目標部位配置表給 Path A / War Room / Execution Service 使用
- 這是「決策層」API，介於 Strategy Signals 跟真正下單之間
- 與 /api/v1/strategy/signals 的關係：signals 是多空信號清單，decision/portfolio 是權重分配後的目標部位配置
"""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from jgod.decision import DecisionEngineV1

router = APIRouter()

# Decision Engine 實例（單例模式）
_decision_engine = DecisionEngineV1()


@router.get("/v1/decision/portfolio")
async def get_portfolio_plan(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    universe: Optional[str] = Query(None, description="Universe name (optional, comma-separated symbols)"),
    long_budget: float = Query(0.6, description="Long budget (default: 0.6 = 60%%)"),
    short_budget: float = Query(0.2, description="Short budget (default: 0.2 = 20%%)"),
    max_weight_per_symbol: float = Query(0.10, description="Max weight per symbol (default: 0.10 = 10%%)"),
    min_score: float = Query(0.0, description="Minimum score threshold"),
    allow_short: bool = Query(True, description="Allow short positions"),
):
    """
    Get portfolio plan for a specific date.
    
    **用途**：
    - 專門給 Path A 回測、War Room UI、Execution Service 使用
    - 回傳當日的目標部位配置表（權重分配後的多空清單）
    
    **與 /api/v1/strategy/signals 的關係**：
    - `/api/v1/strategy/signals`：多空信號清單（策略層）
    - `/api/v1/decision/portfolio`：權重分配後的目標部位配置表（決策層）
    - 這是「決策層」，介於 Strategy Signals 跟真正下單之間
    
    **查詢參數**：
    - date: 日期（必填，格式：YYYY-MM-DD）
    - universe: 股票池（選填，comma-separated symbols）
    - long_budget: Long 總預算（預設 0.6 = 60%%）
    - short_budget: Short 總預算（預設 0.2 = 20%%）
    - max_weight_per_symbol: 單檔最大權重（預設 0.10 = 10%%）
    - min_score: 最低分數門檻（預設 0.0）
    - allow_short: 是否允許放空（預設 True）
    
    Returns:
        PortfolioPlan JSON（包含 date, universe_size, params, positions, summary）
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
        # Generate portfolio plan
        portfolio_plan = _decision_engine.generate_portfolio_for_date(
            date=as_of_date,
            universe=universe_list,
            long_budget=long_budget,
            short_budget=short_budget,
            max_weight_per_symbol=max_weight_per_symbol,
            min_score=min_score,
            allow_short=allow_short,
        )
        
        if portfolio_plan.universe_size == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No prediction data found for {date}",
            )
        
        if not portfolio_plan.positions:
            raise HTTPException(
                status_code=404,
                detail=f"No positions generated for {date}. Possible reasons: no candidates meet min_score threshold or all candidates have insufficient scores.",
            )
        
        # Return PortfolioPlan as JSON
        return portfolio_plan.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating portfolio plan: {str(e)}",
        )

