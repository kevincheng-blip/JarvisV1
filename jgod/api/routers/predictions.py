"""
Predictions API Router

提供 TopN Predictions API（整合 Decision Layer）
"""

import logging
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException
from sqlalchemy.orm import Session

from jgod.api.schemas.predictions import TopLongItem, TopShortItem, DoctrineFlag
from jgod.decision.models import RawScoreItem, DecisionOutput, DoctrineFlag as DecisionDoctrineFlag
from jgod.decision.config import DecisionConfig
from jgod.decision.integration_policy import generate_final_predictions_for_date
from jgod.council_chamber.knowledge_gateway import get_knowledge_brain
try:
    try:
    from jgod.api.dependencies import get_db
except ImportError:
    # Fallback if dependencies module doesn't exist
    def get_db():
        yield None
except ImportError:
    # Fallback if dependencies module doesn't exist
    def get_db():
        yield None

logger = logging.getLogger(__name__)

router = APIRouter()


def _convert_decision_output_to_top_long_item(output: DecisionOutput) -> TopLongItem:
    """將 DecisionOutput 轉換為 TopLongItem"""
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
    
    # 判斷 risk_level（基於 doctrine_flags 的 severity）
    risk_level = None
    if output.doctrine_flags:
        severities = [f.severity for f in output.doctrine_flags]
        if "critical" in severities:
            risk_level = "high"
        elif "warning" in severities:
            risk_level = "mid"
        else:
            risk_level = "low"
    
    return TopLongItem(
        symbol=output.symbol,
        name="",  # 將從 RawScoreItem 取得，這裡先留空
        final_score=output.final_score,
        raw_score=output.raw_score,
        win_prob=None,  # 可由上層計算或從 RawScoreItem 取得
        expected_return=None,
        risk_level=risk_level,
        doctrine_flags=doctrine_flags
    )


def _convert_decision_output_to_top_short_item(output: DecisionOutput) -> TopShortItem:
    """將 DecisionOutput 轉換為 TopShortItem"""
    doctrine_flags = [
        DoctrineFlag(
            code=flag.code,
            severity=flag.severity,
            message=flag.message,
            doctrine_refs=flag.doctrine_refs
        )
        for flag in output.doctrine_flags
    ]
    
    risk_level = None
    if output.doctrine_flags:
        severities = [f.severity for f in output.doctrine_flags]
        if "critical" in severities:
            risk_level = "high"
        elif "warning" in severities:
            risk_level = "mid"
        else:
            risk_level = "low"
    
    return TopShortItem(
        symbol=output.symbol,
        name="",
        final_score=output.final_score,
        raw_score=output.raw_score,
        risk_level=risk_level,
        doctrine_flags=doctrine_flags
    )


def _fetch_raw_scores_from_prediction_engine(trade_date: date, db: Session) -> List[RawScoreItem]:
    """從 Prediction Engine 或資料庫取得 Raw Scores
    
    TODO: 這個函式需要根據實際的 Prediction Engine 實作來調整
    目前提供一個 mock/placeholder 實作
    """
    try:
        # 嘗試從資料庫取得預測結果
        # 假設有 PredictionSnapshot 或類似模型
        from jgod.database.models import PredictionSnapshot  # 如果存在
        
        predictions = db.query(PredictionSnapshot).filter(
            PredictionSnapshot.date == trade_date
        ).all()
        
        raw_items = []
        for pred in predictions:
            # 假設 PredictionSnapshot 有以下欄位
            raw_items.append(RawScoreItem(
                symbol=pred.symbol,
                name=getattr(pred, 'name', None),
                date=trade_date,
                raw_score=getattr(pred, 'score', 0.0) or getattr(pred, 'raw_score', 0.0),
                strategy_scores=getattr(pred, 'strategy_scores', {}),
                risk_metrics=getattr(pred, 'risk_metrics', {}),
                context_tags=getattr(pred, 'tags', [])
            ))
        
        logger.info(f"Fetched {len(raw_items)} raw scores from database for date {trade_date}")
        return raw_items
    
    except ImportError:
        # 如果沒有 PredictionSnapshot 模型，使用 mock 資料
        logger.warning("PredictionSnapshot model not found, using mock data")
        # 返回空列表或 mock 資料（依需求）
        return []
    except Exception as e:
        logger.error(f"Error fetching raw scores: {e}", exc_info=True)
        return []


@router.get(
    "/top-n/long",
    response_model=List[TopLongItem],
    summary="Get Top N Long Predictions",
    description="取得經 Decision Layer 仲裁後的 Final Score 多頭排行榜"
)
async def get_top_n_long(
    date: Optional[str] = Query(None, description="交易日期 (YYYY-MM-DD)，預設為今日"),
    limit: int = Query(30, ge=1, le=200, description="回傳筆數，預設 30，最大 200"),
    sort_by: str = Query("final_score", description="排序欄位: final_score 或 raw_score"),
) -> List[TopLongItem]:
    """取得 Top N Long Predictions"""
    
    # 解析日期
    if date:
        try:
            trade_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        trade_date = date.today()
    
    if db is None:
        db = next(get_db())
    
    try:
        # 1. 取得 Raw Scores
        raw_items = _fetch_raw_scores_from_prediction_engine(trade_date, db)
        
        if not raw_items:
            logger.info(f"No raw scores found for date {trade_date}")
            return []
        
        # 2. 過濾出多頭候選（raw_score > 0 或策略看多）
        long_candidates = [
            item for item in raw_items
            if item.raw_score > 0  # 簡單規則：raw_score > 0 視為多頭
        ]
        
        if not long_candidates:
            logger.info(f"No long candidates found for date {trade_date}")
            return []
        
        # 3. 呼叫 Decision Layer
        config = DecisionConfig()  # 可從設定檔或環境變數讀取
        knowledge_brain = get_knowledge_brain()
        
        decision_outputs = generate_final_predictions_for_date(
            trade_date=trade_date,
            raw_items=long_candidates,
            config=config,
            knowledge_brain=knowledge_brain
        )
        
        # 4. 轉換為 TopLongItem
        top_items = []
        name_map = {item.symbol: item.name for item in raw_items if item.name}
        
        for output in decision_outputs:
            item = _convert_decision_output_to_top_long_item(output)
            # 填入 name
            if output.symbol in name_map:
                item.name = name_map[output.symbol]
            top_items.append(item)
        
        # 5. 排序
        if sort_by == "final_score":
            top_items.sort(key=lambda x: x.final_score, reverse=True)
        elif sort_by == "raw_score":
            top_items.sort(key=lambda x: x.raw_score, reverse=True)
        
        # 6. 取前 N 筆
        result = top_items[:limit]
        
        logger.info(f"Returning {len(result)} top long predictions for date {trade_date}")
        return result
    
    except Exception as e:
        logger.error(f"Error in get_top_n_long: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/top-n/short",
    response_model=List[TopShortItem],
    summary="Get Top N Short Predictions",
    description="取得經 Decision Layer 仲裁後的 Final Score 空頭/避險排行榜"
)
async def get_top_n_short(
    date: Optional[str] = Query(None, description="交易日期 (YYYY-MM-DD)，預設為今日"),
    limit: int = Query(30, ge=1, le=200, description="回傳筆數，預設 30，最大 200"),
    sort_by: str = Query("final_score", description="排序欄位: final_score 或 raw_score"),
) -> List[TopShortItem]:
    """取得 Top N Short Predictions"""
    
    # 解析日期
    if date:
        try:
            trade_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        trade_date = date.today()
    
    if db is None:
        db = next(get_db())
    
    try:
        # 1. 取得 Raw Scores
        raw_items = _fetch_raw_scores_from_prediction_engine(trade_date, db)
        
        if not raw_items:
            logger.info(f"No raw scores found for date {trade_date}")
            return []
        
        # 2. 過濾出空頭候選（raw_score < 0 或策略看空）
        short_candidates = [
            item for item in raw_items
            if item.raw_score < 0  # 簡單規則：raw_score < 0 視為空頭
        ]
        
        if not short_candidates:
            logger.info(f"No short candidates found for date {trade_date}")
            return []
        
        # 3. 呼叫 Decision Layer
        config = DecisionConfig()
        knowledge_brain = get_knowledge_brain()
        
        decision_outputs = generate_final_predictions_for_date(
            trade_date=trade_date,
            raw_items=short_candidates,
            config=config,
            knowledge_brain=knowledge_brain
        )
        
        # 4. 轉換為 TopShortItem
        top_items = []
        name_map = {item.symbol: item.name for item in raw_items if item.name}
        
        for output in decision_outputs:
            item = _convert_decision_output_to_top_short_item(output)
            if output.symbol in name_map:
                item.name = name_map[output.symbol]
            top_items.append(item)
        
        # 5. 排序（空頭：final_score 越低越好，所以升序）
        if sort_by == "final_score":
            top_items.sort(key=lambda x: x.final_score, reverse=False)  # 升序
        elif sort_by == "raw_score":
            top_items.sort(key=lambda x: x.raw_score, reverse=False)  # 升序
        
        # 6. 取前 N 筆
        result = top_items[:limit]
        
        logger.info(f"Returning {len(result)} top short predictions for date {trade_date}")
        return result
    
    except Exception as e:
        logger.error(f"Error in get_top_n_short: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
