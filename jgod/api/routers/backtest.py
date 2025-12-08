"""
J-GOD Backtest Service v1 - API Router

提供 Path A 回測的 HTTP API 介面。

Endpoints:
- POST /api/v1/backtest/path-a/run-sync: 執行同步回測
- GET  /api/v1/backtest/path-a/experiments/recent: 讀取最近實驗記錄
"""

import json
import logging
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from jgod.api.schemas.backtest import (
    PathABacktestRequest,
    PathABacktestResponse,
    PathABacktestSummary,
)
from jgod.decision.risk_config_loader import load_risk_config
from jgod.path_a.path_a_engine_v1 import PathAEngineV1
from jgod.policy.policy_log_reader_v1 import PolicyLogReaderV1

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])


def _backtest_result_to_summary(
    result,
    start_date: date,
    end_date: date,
    run_id: Optional[str] = None,
) -> PathABacktestSummary:
    """
    將 BacktestResult 轉換為 PathABacktestSummary
    
    Args:
        result: BacktestResult 物件
        start_date: 回測開始日期
        end_date: 回測結束日期
        run_id: 可選的 run_id
    
    Returns:
        PathABacktestSummary 物件
    """
    metrics = result.metrics
    
    return PathABacktestSummary(
        run_id=run_id,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        initial_capital=result.initial_capital,
        final_capital=result.final_capital,
        total_return=metrics.total_return,
        annualized_return=metrics.annualized_return,
        annualized_volatility=metrics.annualized_volatility,
        sharpe_ratio=metrics.sharpe_ratio,
        max_drawdown=metrics.max_drawdown,
        win_rate=metrics.win_rate,
        num_days=len(result.daily_equity_curve),
        num_trades=metrics.num_long_trades + metrics.num_short_trades,
        long_trades=metrics.num_long_trades,
        short_trades=metrics.num_short_trades,
    )


@router.post(
    "/path-a/run-sync",
    response_model=PathABacktestResponse,
    summary="執行 Path A 同步回測",
    description="執行 Path A 回測並立即返回結果。回測結果會自動寫入 JSONL log。",
)
async def run_path_a_backtest_sync(request: PathABacktestRequest):
    """
    執行 Path A 同步回測
    
    流程：
    1. 解析日期與參數
    2. 載入 RiskConfig（若提供）
    3. 初始化 PathAEngineV1
    4. 執行回測
    5. 寫入 JSONL log
    6. 返回結果摘要
    """
    try:
        # 解析日期
        try:
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}"
            )
        
        if start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )
        
        # 構建 Decision Config
        decision_config = {
            "long_budget": request.long_budget,
            "short_budget": request.short_budget,
            "max_weight_per_symbol": request.max_weight_per_symbol,
            "min_score": request.min_score,
            "allow_short": request.allow_short,
        }
        
        # 載入 RiskConfig（若提供）
        if request.risk_config_file:
            try:
                risk_config_dict = load_risk_config(request.risk_config_file)
                if risk_config_dict:
                    # YAML 值覆蓋請求參數
                    decision_config["long_budget"] = risk_config_dict.get(
                        "long_budget", decision_config["long_budget"]
                    )
                    decision_config["short_budget"] = risk_config_dict.get(
                        "short_budget", decision_config["short_budget"]
                    )
                    decision_config["max_weight_per_symbol"] = risk_config_dict.get(
                        "max_weight_per_symbol", decision_config["max_weight_per_symbol"]
                    )
                    decision_config["min_score"] = risk_config_dict.get(
                        "min_score", decision_config["min_score"]
                    )
                    decision_config["allow_short"] = risk_config_dict.get(
                        "allow_short", decision_config["allow_short"]
                    )
                    logger.info(f"RiskConfig loaded from YAML: {request.risk_config_file}")
            except FileNotFoundError:
                raise HTTPException(
                    status_code=400,
                    detail=f"RiskConfig file not found: {request.risk_config_file}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to load RiskConfig: {str(e)}"
                )
        
        # 初始化 Path A Engine
        try:
            engine = PathAEngineV1(
                initial_capital=request.capital,
                **decision_config
            )
        except Exception as e:
            logger.exception(f"Failed to initialize PathAEngineV1: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize backtest engine"
            )
        
        # 執行回測
        try:
            result = engine.run_backtest(start_date=start_date, end_date=end_date)
        except Exception as e:
            logger.exception(f"Backtest execution failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Backtest execution failed: {str(e)}"
            )
        
        # 檢查是否有交易日期
        if not result.daily_equity_curve:
            raise HTTPException(
                status_code=400,
                detail=f"No trading dates found in range {request.start_date} to {request.end_date}"
            )
        
        # 寫入 JSONL log（模擬 run_path_a_v1.py 的邏輯）
        run_id = uuid.uuid4().hex
        
        try:
            config_params = {
                "initial_capital": request.capital,
                "long_budget": decision_config["long_budget"],
                "short_budget": decision_config["short_budget"],
                "max_weight_per_symbol": decision_config["max_weight_per_symbol"],
                "min_score": decision_config["min_score"],
                "allow_short": decision_config["allow_short"],
            }
            
            log_record = engine.generate_log_record(
                run_id=run_id,
                config_params=config_params,
                backtest_result=result,
            )
            
            # 如果有 tag，加入到 log_record
            if request.tag:
                log_record["experiment_tag"] = request.tag
            
            # 寫入 JSON Lines 檔案
            project_root = Path(__file__).parent.parent.parent
            log_file_path = project_root / "data" / "path_a_backtest_logs.jsonl"
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file_path, "a", encoding="utf-8") as f:
                json_line = json.dumps(log_record, ensure_ascii=False)
                f.write(json_line + "\n")
            
            logger.info(f"Backtest log written: run_id={run_id}")
        
        except Exception as e:
            # Log 寫入失敗不影響 API 回應，只記錄警告
            logger.warning(f"Failed to write backtest log: {e}")
            run_id = None
        
        # 組裝回應
        summary = _backtest_result_to_summary(
            result=result,
            start_date=start_date,
            end_date=end_date,
            run_id=run_id,
        )
        
        return PathABacktestResponse(
            request=request,
            summary=summary,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in run_path_a_backtest_sync: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@router.get(
    "/path-a/experiments/recent",
    response_model=List[PathABacktestSummary],
    summary="讀取最近 Path A 回測實驗記錄",
    description="從 JSONL log 讀取最近 N 筆實驗記錄（只讀，不重跑）。",
)
async def get_recent_backtest_experiments(
    start_date: Optional[str] = Query(None, description="篩選開始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="篩選結束日期 (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100, description="返回筆數上限"),
):
    """
    讀取最近 Path A 回測實驗記錄
    
    流程：
    1. 使用 PolicyLogReaderV1 讀取 JSONL log
    2. 過濾日期範圍（若提供）
    3. 排序（按 timestamp 由新到舊）
    4. 轉換為 PathABacktestSummary
    5. 返回前 N 筆
    """
    try:
        # 初始化 PolicyLogReaderV1
        project_root = Path(__file__).parent.parent.parent
        log_path = project_root / "data" / "path_a_backtest_logs.jsonl"
        
        if not log_path.exists():
            return []
        
        try:
            reader = PolicyLogReaderV1(log_path=str(log_path))
        except Exception as e:
            logger.warning(f"Failed to initialize PolicyLogReaderV1: {e}")
            return []
        
        # 讀取所有 log records
        try:
            raw_logs = reader.load_logs()
        except Exception as e:
            logger.warning(f"Failed to load logs: {e}")
            return []
        
        if not raw_logs:
            return []
        
        # 轉換為 PolicyExperimentSummary（使用 reader 的轉換方法）
        summaries = []
        for raw_log in raw_logs:
            try:
                exp_summary = reader.to_experiment_summary(raw_log)
                if not exp_summary.is_valid:
                    continue
                
                # 過濾日期範圍（若提供）
                if start_date:
                    try:
                        filter_start = datetime.strptime(start_date, "%Y-%m-%d").date()
                        exp_start = datetime.strptime(exp_summary.start_date, "%Y-%m-%d").date()
                        if exp_start < filter_start:
                            continue
                    except ValueError:
                        pass
                
                if end_date:
                    try:
                        filter_end = datetime.strptime(end_date, "%Y-%m-%d").date()
                        exp_end = datetime.strptime(exp_summary.end_date, "%Y-%m-%d").date()
                        if exp_end > filter_end:
                            continue
                    except ValueError:
                        pass
                
                # 轉換為 PathABacktestSummary
                backtest_summary = PathABacktestSummary(
                    run_id=exp_summary.run_id,
                    start_date=exp_summary.start_date,
                    end_date=exp_summary.end_date,
                    initial_capital=exp_summary.initial_capital,
                    final_capital=exp_summary.final_capital,
                    total_return=exp_summary.total_return,
                    annualized_return=exp_summary.annualized_return,
                    annualized_volatility=exp_summary.annualized_volatility,
                    sharpe_ratio=exp_summary.sharpe_ratio,
                    max_drawdown=exp_summary.max_drawdown,
                    win_rate=exp_summary.win_rate,
                    num_days=exp_summary.num_days,
                    num_trades=exp_summary.num_long_trades + exp_summary.num_short_trades,
                    long_trades=exp_summary.num_long_trades,
                    short_trades=exp_summary.num_short_trades,
                )
                
                summaries.append((exp_summary.timestamp, backtest_summary))
            
            except Exception as e:
                logger.warning(f"Failed to convert log record to summary: {e}")
                continue
        
        # 按 timestamp 排序（由新到舊）
        summaries.sort(key=lambda x: x[0], reverse=True)
        
        # 取前 N 筆
        result_summaries = [summary for _, summary in summaries[:limit]]
        
        return result_summaries
    
    except Exception as e:
        logger.exception(f"Unexpected error in get_recent_backtest_experiments: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while reading experiments"
        )

