"""
Orders API Router

提供 Final Orders API（整合 Decision Layer）
"""

import logging
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException
try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = None  # Fallback if SQLAlchemy not available

from jgod.api.schemas.orders import FinalOrderItem
from jgod.api.schemas.predictions import DoctrineFlag
from jgod.decision.models import DecisionOutput, DoctrineFlag as DecisionDoctrineFlag
from jgod.decision.config import DecisionConfig
from jgod.decision.integration_policy import generate_final_predictions_for_date
from jgod.council_chamber.knowledge_gateway import get_knowledge_brain
from jgod.api.routers.predictions import _fetch_raw_scores_from_prediction_engine

# Database dependencies
try:
    from jgod.api.dependencies import get_db
except ImportError:
    try:
        from jgod.storage.db import get_session as get_db
    except ImportError:
        # Fallback: create a dummy get_db
        def get_db():
            yield None

logger = logging.getLogger(__name__)

router = APIRouter()


def _determine_action(final_score: float, raw_score: float, doctrine_flags: List[DecisionDoctrineFlag]) -> str:
    """根據 Final Score 和 Doctrine Flags 決定 action
    
    v1.0 簡單規則：
    - final_score > 0.7 → BUY
    - final_score < -0.7 → SELL
    - 其他 → HOLD
    
    若有 critical Doctrine flags，強制 HOLD
    """
    # 檢查是否有 critical flags
    has_critical = any(flag.severity == "critical" for flag in doctrine_flags)
    if has_critical:
        return "HOLD"
    
    if final_score > 0.7:
        return "BUY"
    elif final_score < -0.7:
        return "SELL"
    else:
        return "HOLD"


def _calculate_quantity(final_score: float, action: str) -> float:
    """計算數量（v1.0 mock 實作）
    
    TODO: v1.0 後應根據：
    - 資本配置
    - 風險限制
    - 目前部位
    來計算實際數量
    """
    if action == "HOLD":
        return 0.0
    
    # Mock：根據 final_score 的絕對值計算標準化數量
    abs_score = abs(final_score)
    base_quantity = 100.0  # 基礎數量
    
    # 簡單線性映射：score 0.7 -> 70, score 1.0 -> 100
    quantity = base_quantity * abs_score
    
    return round(quantity, 2)


def _calculate_confidence(final_score: float, raw_score: float) -> float:
    """計算信心度（v1.0 mock 實作）
    
    TODO: v1.0 後應根據：
    - final_score 與 raw_score 的差異（correction_factor）
    - 策略一致性
    - 市場環境
    來計算實際信心度
    """
    # Mock：簡單規則
    # 如果 final_score 和 raw_score 差異小（correction_factor 接近 1.0），信心度高
    if raw_score == 0:
        return 0.5
    
    correction_factor = final_score / raw_score if raw_score != 0 else 1.0
    
    # correction_factor 在 0.9 ~ 1.1 之間時，信心度較高
    if 0.9 <= correction_factor <= 1.1:
        base_confidence = 0.8
    else:
        base_confidence = 0.6
    
    # 根據 final_score 的絕對值調整
    abs_score = abs(final_score)
    confidence = min(1.0, base_confidence + (abs_score - 0.5) * 0.4)
    
    return round(confidence, 2)


def _convert_decision_output_to_final_order(
    output: DecisionOutput,
    name: str = ""
) -> FinalOrderItem:
    """將 DecisionOutput 轉換為 FinalOrderItem"""
    
    # 決定 action
    action = _determine_action(output.final_score, output.raw_score, output.doctrine_flags)
    
    # 計算 quantity
    quantity = _calculate_quantity(output.final_score, action)
    
    # 計算 confidence
    confidence = _calculate_confidence(output.final_score, output.raw_score)
    
    # 轉換 DoctrineFlags
    doctrine_flags = [
        DoctrineFlag(
            code=flag.code,
            severity=flag.severity,
            message=flag.message,
            doctrine_refs=flag.doctrine_refs
        )
        for flag in output.doctrine_flags
    ]
    
    return FinalOrderItem(
        symbol=output.symbol,
        name=name or "",
        action=action,
        quantity=quantity,
        final_score=output.final_score,
        confidence=confidence,
        doctrine_flags=doctrine_flags,
        status=None  # v1.0 先不實作 status
    )


@router.get(
    "/final",
    response_model=List[FinalOrderItem],
    summary="Get Final Orders",
    description="取得當日最終指令（經 Decision Layer 仲裁後）"
)
async def get_final_orders(
    date: Optional[str] = Query(None, description="交易日期 (YYYY-MM-DD)，預設為今日"),
) -> List[FinalOrderItem]:
    """取得 Final Orders"""
    
    # 解析日期
    if date:
        try:
            trade_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        trade_date = date.today()
    
    # 取得資料庫連線（如果可用）
    try:
        db_gen = get_db()
        db = next(db_gen) if db_gen else None
    except Exception:
        db = None
    
    try:
        # 1. 取得 Raw Scores（所有候選，不分多空）
        raw_items = _fetch_raw_scores_from_prediction_engine(trade_date, db)
        
        if not raw_items:
            logger.info(f"No raw scores found for date {trade_date}")
            return []
        
        # 2. 只處理有顯著分數的項目（過濾掉接近 0 的）
        significant_items = [
            item for item in raw_items
            if abs(item.raw_score) > 0.3  # 只處理分數絕對值 > 0.3 的
        ]
        
        if not significant_items:
            logger.info(f"No significant raw scores found for date {trade_date}")
            return []
        
        # 3. 呼叫 Decision Layer
        config = DecisionConfig()
        knowledge_brain = get_knowledge_brain()
        
        decision_outputs = generate_final_predictions_for_date(
            trade_date=trade_date,
            raw_items=significant_items,
            config=config,
            knowledge_brain=knowledge_brain
        )
        
        # 4. 轉換為 FinalOrderItem
        # 建立 symbol -> name 映射
        name_map = {}
        for item in raw_items:
            if item.name:
                name_map[item.symbol] = item.name
        
        # 如果 name_map 為空，嘗試從 universe 或 Stock 模型取得
        if not name_map and db:
            try:
                from jgod.storage.models import Stock
                symbols = [item.symbol for item in raw_items]
                stocks = db.query(Stock).filter(Stock.symbol.in_(symbols)).all()
                for stock in stocks:
                    name_map[stock.symbol] = getattr(stock, 'name_zh', None) or getattr(stock, 'name', None) or ""
            except Exception:
                pass
        
        final_orders = []
        for output in decision_outputs:
            name = name_map.get(output.symbol, "")
            order_item = _convert_decision_output_to_final_order(output, name)
            final_orders.append(order_item)
        
        # 5. 排序：按 final_score 絕對值降序
        final_orders.sort(key=lambda x: abs(x.final_score), reverse=True)
        
        logger.info(f"Returning {len(final_orders)} final orders for date {trade_date}")
        return final_orders
    
    except Exception as e:
        logger.error(f"Error in get_final_orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

