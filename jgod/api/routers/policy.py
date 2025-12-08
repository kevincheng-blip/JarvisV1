"""
J-GOD AI Policy Service v1 API Router

提供 Policy Log Reader 和 Policy Writer 的 HTTP API 介面。
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from jgod.policy import (
    PolicyScoreConfig,
    PolicyExperimentSummary,
    PolicyLogReaderV1,
    PolicySuggestion,
    PolicyWriterV1,
)

router = APIRouter()


@router.get("/experiments/best")
async def get_best_experiments(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    top_n: int = Query(20, ge=1, le=100, description="Number of top experiments to return"),
    min_days: int = Query(60, ge=1, description="Minimum number of trading days"),
    min_trades: int = Query(30, ge=1, description="Minimum number of trades"),
    sharpe_weight: float = Query(0.7, ge=0.0, le=1.0, description="Weight for Sharpe ratio in scoring"),
    maxdd_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for Max Drawdown in scoring"),
    log_path: str = Query("data/path_a_backtest_logs.jsonl", description="Path to backtest log file"),
) -> List[dict]:
    """
    查詢最佳回測實驗
    
    根據指定的日期範圍和篩選條件，返回排名前 N 的實驗結果。
    """
    try:
        # 構建 PolicyScoreConfig
        score_config = PolicyScoreConfig(
            sharpe_weight=sharpe_weight,
            max_dd_weight=maxdd_weight,
            min_days=min_days,
            min_trades=min_trades,
        )
        
        # 構建 PolicyLogReaderV1
        reader = PolicyLogReaderV1(log_path=log_path, score_config=score_config)
        
        # 調用 filter_and_rank
        experiments = reader.filter_and_rank(
            start_date=start_date,
            end_date=end_date,
            top_n=top_n,
        )
        
        # 轉換為字典列表
        result = []
        for exp in experiments:
            result.append({
                "run_id": exp.run_id,
                "timestamp": exp.timestamp,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "initial_capital": exp.initial_capital,
                "final_capital": exp.final_capital,
                "total_return": exp.total_return,
                "annualized_return": exp.annualized_return,
                "annualized_volatility": exp.annualized_volatility,
                "sharpe_ratio": exp.sharpe_ratio,
                "max_drawdown": exp.max_drawdown,
                "win_rate": exp.win_rate,
                "total_commission": exp.total_commission,
                "num_long_trades": exp.num_long_trades,
                "num_short_trades": exp.num_short_trades,
                "num_days": exp.num_days,
                "num_trades": exp.num_long_trades + exp.num_short_trades,
                "long_budget": exp.long_budget,
                "short_budget": exp.short_budget,
                "max_weight_per_symbol": exp.max_weight_per_symbol,
                "min_score": exp.min_score,
                "allow_short": exp.allow_short,
                "score": exp.score,
                "is_valid": exp.is_valid,
                "reason": exp.reason,
            })
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load experiments: {str(e)}")


@router.get("/risk-config/suggest")
async def get_suggested_risk_config(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    top_k: int = Query(3, ge=1, le=10, description="Number of top experiments to consider"),
    min_days: int = Query(60, ge=1, description="Minimum number of trading days"),
    min_trades: int = Query(30, ge=1, description="Minimum number of trades"),
    sharpe_weight: float = Query(0.7, ge=0.0, le=1.0, description="Weight for Sharpe ratio in scoring"),
    maxdd_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for Max Drawdown in scoring"),
    log_path: str = Query("data/path_a_backtest_logs.jsonl", description="Path to backtest log file"),
) -> dict:
    """
    取得建議的 RiskConfig
    
    基於最佳實驗結果，生成建議的風險配置參數。
    此端點不會寫入檔案，只返回 JSON 格式的建議配置。
    """
    try:
        # 構建 PolicyScoreConfig
        score_config = PolicyScoreConfig(
            sharpe_weight=sharpe_weight,
            max_dd_weight=maxdd_weight,
            min_days=min_days,
            min_trades=min_trades,
        )
        
        # 構建 PolicyWriterV1
        writer = PolicyWriterV1(
            log_path=log_path,
            score_config=score_config,
            min_days=min_days,
            min_trades=min_trades,
        )
        
        # 調用 generate_suggestion
        suggestion = writer.generate_suggestion(
            start_date=start_date,
            end_date=end_date,
            top_k=top_k,
        )
        
        if suggestion is None:
            raise HTTPException(
                status_code=404,
                detail="No valid experiments found. Please run Path A v1 backtests first or relax filter criteria."
            )
        
        # 構建回應（排除 output_path）
        # 處理 created_at（可能是 datetime 或字串）
        created_at_str = suggestion.created_at
        if hasattr(suggestion.created_at, 'isoformat'):
            created_at_str = suggestion.created_at.isoformat()
        elif isinstance(suggestion.created_at, str):
            created_at_str = suggestion.created_at
        
        suggestion_dict = {
            "run_id": suggestion.run_id,
            "created_at": created_at_str,
            "source_log_path": suggestion.source_log_path,
            "start_date": suggestion.start_date,
            "end_date": suggestion.end_date,
            "score": suggestion.score,
            "sharpe_ratio": suggestion.sharpe_ratio,
            "max_drawdown": suggestion.max_drawdown,
            "total_return": suggestion.total_return,
            "win_rate": suggestion.win_rate,
            "num_days": suggestion.num_days,
            "num_trades": suggestion.num_trades,
            "long_budget": suggestion.long_budget,
            "short_budget": suggestion.short_budget,
            "max_weight_per_symbol": suggestion.max_weight_per_symbol,
            "min_score": suggestion.min_score,
            "allow_short": suggestion.allow_short,
        }
        
        # 構建 config 區塊
        config_dict = {
            "long_budget": suggestion.long_budget,
            "short_budget": suggestion.short_budget,
            "max_weight_per_symbol": suggestion.max_weight_per_symbol,
            "min_score": suggestion.min_score,
            "allow_short": suggestion.allow_short,
        }
        
        return {
            "suggestion": suggestion_dict,
            "config": config_dict,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestion: {str(e)}")

