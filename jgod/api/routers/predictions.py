"""
Predictions API Router

提供 TopN Predictions API（整合 Decision Layer）
"""

import logging
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException
try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = None  # Fallback if SQLAlchemy not available

from jgod.api.schemas.predictions import TopLongItem, TopShortItem, DoctrineFlag
from jgod.decision.models import RawScoreItem, DecisionOutput, DoctrineFlag as DecisionDoctrineFlag
from jgod.decision.config import DecisionConfig
from jgod.decision.integration_policy import generate_final_predictions_for_date
from jgod.council_chamber.knowledge_gateway import get_knowledge_brain

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


def _fetch_raw_scores_from_prediction_engine(trade_date: date, db) -> List[RawScoreItem]:
    """從 Prediction Engine 或資料庫取得 Raw Scores
    
    TODO: 這個函式需要根據實際的 Prediction Engine 實作來調整
    目前提供一個實作，從 PredictionSnapshot 資料庫模型取得
    """
    if db is None:
        logger.warning(f"Database not available, returning empty raw scores for date {trade_date}")
        return []
    
    try:
        # 嘗試從資料庫取得預測結果
        from jgod.storage.models import PredictionSnapshot
        from jgod.storage.db import get_session
        
        # 如果 db 是 generator，取得 session
        if hasattr(db, '__next__'):
            session = next(db)
        else:
            session = db
        
        predictions = session.query(PredictionSnapshot).filter(
            PredictionSnapshot.date == trade_date
        ).all()
        
        raw_items = []
        for pred in predictions:
            # 取得 score（優先使用 score，否則用 total_score）
            score_value = pred.score if hasattr(pred, 'score') and pred.score is not None else (pred.total_score or 0.0)
            
            # 嘗試解析 strategy_scores（如果是 JSON）
            strategy_scores = {}
            if hasattr(pred, 'strategy_scores_json') and pred.strategy_scores_json:
                try:
                    import json
                    if isinstance(pred.strategy_scores_json, str):
                        strategy_scores = json.loads(pred.strategy_scores_json)
                    elif isinstance(pred.strategy_scores_json, dict):
                        strategy_scores = pred.strategy_scores_json
                except Exception:
                    pass
            
            # 嘗試取得 risk_metrics
            risk_metrics = {}
            if hasattr(pred, 'risk_metrics_json') and pred.risk_metrics_json:
                try:
                    import json
                    if isinstance(pred.risk_metrics_json, str):
                        risk_metrics = json.loads(pred.risk_metrics_json)
                    elif isinstance(pred.risk_metrics_json, dict):
                        risk_metrics = pred.risk_metrics_json
                except Exception:
                    pass
            
            # 嘗試取得 context_tags
            context_tags = []
            if hasattr(pred, 'tags') and pred.tags:
                if isinstance(pred.tags, list):
                    context_tags = pred.tags
                elif isinstance(pred.tags, str):
                    context_tags = [tag.strip() for tag in pred.tags.split(",")]
            
            raw_items.append(RawScoreItem(
                symbol=pred.symbol,
                name=None,  # PredictionSnapshot 可能沒有 name，需從其他地方取得
                date=trade_date,
                raw_score=float(score_value),
                strategy_scores=strategy_scores,
                risk_metrics=risk_metrics,
                context_tags=context_tags
            ))
        
        logger.info(f"Fetched {len(raw_items)} raw scores from database for date {trade_date}")
        return raw_items
    
    except ImportError as e:
        logger.warning(f"PredictionSnapshot model not found: {e}. Returning empty list.")
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
    
    # 取得資料庫連線（如果可用）
    db = None
    try:
        db_gen = get_db()
        if db_gen:
            db = next(db_gen)
    except Exception as e:
        logger.debug(f"Could not get database session: {e}")
        db = None
    
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
        # 建立 symbol -> name 映射
        name_map = {}
        for item in raw_items:
            if item.name:
                name_map[item.symbol] = item.name
        
        # 如果 name_map 為空，嘗試從 universe 或 Stock 模型取得
        if not name_map and db:
            try:
                from jgod.storage.models import Stock
                stocks = db.query(Stock).filter(Stock.stock_id.in_([item.symbol for item in raw_items])).all()
                for stock in stocks:
                    name_map[stock.stock_id] = getattr(stock, 'name_zh', None) or getattr(stock, 'name', None) or ""
            except Exception:
                pass
        
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
