"""
J-GOD AI Policy Service v1 API Router

提供 Policy Log Reader 和 Policy Writer 的 HTTP API 介面。
"""

from datetime import date, datetime
from pathlib import Path
from typing import List, Optional
import logging

from fastapi import APIRouter, HTTPException, Query

from jgod.policy import (
    PolicyScoreConfig,
    PolicyExperimentSummary,
    PolicyLogReaderV1,
    PolicySuggestion,
    PolicyWriterV1,
)
from jgod.decision.risk_config_loader import load_risk_config
from jgod.api.schemas.policy import PolicyExperimentHistoryItem, PolicyActiveConfig

logger = logging.getLogger(__name__)

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


@router.get(
    "/experiments/history",
    response_model=List[PolicyExperimentHistoryItem],
    summary="Get policy experiment history",
    description="Retrieves a list of historical backtest experiments for policy evolution analysis.",
)
async def get_policy_experiments_history(
    start_date: Optional[str] = Query(None, description="Filter experiments starting from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter experiments ending by this date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of experiments to return"),
    order_by: str = Query("timestamp", description="Sort order: 'timestamp', 'score', or 'sharpe'"),
):
    """
    取得政策實驗歷史
    
    用於 Policy Evolution Panel，返回一段時間內的實驗列表。
    """
    try:
        # 初始化 PolicyLogReaderV1
        project_root = Path(__file__).parent.parent.parent
        log_path = project_root / "data" / "path_a_backtest_logs.jsonl"
        
        if not log_path.exists():
            return []
        
        # 構建 PolicyScoreConfig（用於計算 score）
        score_config = PolicyScoreConfig()
        
        reader = PolicyLogReaderV1(log_path=str(log_path), score_config=score_config)
        
        # 載入所有 log records
        try:
            raw_logs = reader.load_logs()
        except Exception as e:
            logger.warning(f"Failed to load logs: {e}")
            return []
        
        if not raw_logs:
            return []
        
        # 轉換為 PolicyExperimentSummary 並計算 score
        summaries = []
        for raw_log in raw_logs:
            try:
                exp_summary = reader.to_experiment_summary(raw_log)
                if not exp_summary.is_valid:
                    continue
                
                # 計算 score
                score = reader.compute_score(exp_summary)
                exp_summary.score = score
                
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
                
                summaries.append(exp_summary)
            
            except Exception as e:
                logger.warning(f"Failed to convert log record to summary: {e}")
                continue
        
        # 排序
        if order_by == "score":
            summaries.sort(key=lambda x: x.score, reverse=True)
        elif order_by == "sharpe":
            summaries.sort(key=lambda x: x.sharpe_ratio, reverse=True)
        else:  # timestamp (default)
            summaries.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 取前 N 筆
        summaries = summaries[:limit]
        
        # 轉換為 PolicyExperimentHistoryItem
        result_items = []
        for summary in summaries:
            # 從原始 log 中取得 tag（如果有的話）
            tag = None
            try:
                raw_log = next((log for log in raw_logs if log.get("run_id") == summary.run_id), None)
                if raw_log:
                    tag = raw_log.get("experiment_tag")
            except Exception:
                pass
            
            item = PolicyExperimentHistoryItem(
                run_id=summary.run_id,
                timestamp=summary.timestamp,
                start_date=summary.start_date,
                end_date=summary.end_date,
                score=summary.score,
                sharpe_ratio=summary.sharpe_ratio,
                max_drawdown=summary.max_drawdown,
                total_return=summary.total_return,
                win_rate=summary.win_rate,
                num_days=summary.num_days,
                num_trades=summary.num_long_trades + summary.num_short_trades,
                long_budget=summary.long_budget,
                short_budget=summary.short_budget,
                max_weight_per_symbol=summary.max_weight_per_symbol,
                min_score=summary.min_score,
                allow_short=summary.allow_short,
                tag=tag,
            )
            result_items.append(item)
        
        return result_items
    
    except Exception as e:
        logger.exception(f"Unexpected error in get_policy_experiments_history: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while reading experiment history"
        )


@router.get(
    "/risk-config/active",
    response_model=PolicyActiveConfig,
    summary="Get active RiskConfig",
    description="Returns the currently active RiskConfig from YAML file.",
)
async def get_active_risk_config(
    file: Optional[str] = Query(None, description="RiskConfig file path (default: policy/risk_config_suggested_v1.yaml)"),
):
    """
    取得當前生效的 RiskConfig
    
    從指定的 YAML 檔案載入 RiskConfig，若未指定則使用預設檔案。
    """
    try:
        project_root = Path(__file__).parent.parent.parent
        
        # 預設檔案路徑
        if file is None:
            file = "policy/risk_config_suggested_v1.yaml"
        
        file_path = project_root / file
        
        # 檢查檔案是否存在
        if not file_path.exists():
            return PolicyActiveConfig(
                file_path=str(file_path.relative_to(project_root)),
                exists=False,
            )
        
        # 嘗試載入 YAML
        try:
            config_dict = load_risk_config(str(file_path))
        except Exception as e:
            logger.warning(f"Failed to load RiskConfig from {file_path}: {e}")
            return PolicyActiveConfig(
                file_path=str(file_path.relative_to(project_root)),
                exists=True,
                # 其他欄位留 None
            )
        
        if not config_dict:
            return PolicyActiveConfig(
                file_path=str(file_path.relative_to(project_root)),
                exists=True,
            )
        
        # 嘗試從檔案內容讀取更多資訊（source, metrics 等）
        # 由於我們的簡易 YAML parser 可能無法解析完整的 YAML 結構
        # 這裡我們只提取 config 區塊的參數
        # 如果未來需要更完整的資訊，可以改進 YAML parser
        
        # 嘗試讀取檔案內容以取得 source 資訊
        source_run_id = None
        source_start_date = None
        source_end_date = None
        source_sharpe = None
        source_maxdd = None
        source_return = None
        source_winrate = None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # 簡易解析 source 和 metrics 區塊
                import re
                
                # 提取 run_id
                run_id_match = re.search(r'run_id:\s*["\']?([a-f0-9]+)', content)
                if run_id_match:
                    source_run_id = run_id_match.group(1)
                
                # 提取日期
                start_date_match = re.search(r'start_date:\s*["\']?(\d{4}-\d{2}-\d{2})', content)
                if start_date_match:
                    source_start_date = start_date_match.group(1)
                
                end_date_match = re.search(r'end_date:\s*["\']?(\d{4}-\d{2}-\d{2})', content)
                if end_date_match:
                    source_end_date = end_date_match.group(1)
                
                # 提取 metrics
                sharpe_match = re.search(r'sharpe_ratio:\s*([\d.]+)', content)
                if sharpe_match:
                    source_sharpe = float(sharpe_match.group(1))
                
                maxdd_match = re.search(r'max_drawdown:\s*([\d.]+)', content)
                if maxdd_match:
                    source_maxdd = float(maxdd_match.group(1))
                
                return_match = re.search(r'total_return:\s*([\d.]+)', content)
                if return_match:
                    source_return = float(return_match.group(1))
                
                winrate_match = re.search(r'win_rate:\s*([\d.]+)', content)
                if winrate_match:
                    source_winrate = float(winrate_match.group(1))
        except Exception as e:
            logger.debug(f"Failed to extract additional info from YAML: {e}")
        
        # 構建回應
        return PolicyActiveConfig(
            file_path=str(file_path.relative_to(project_root)),
            exists=True,
            risk_version=1,  # 預設為 v1
            run_id=source_run_id,
            start_date=source_start_date,
            end_date=source_end_date,
            long_budget=config_dict.get("long_budget"),
            short_budget=config_dict.get("short_budget"),
            max_weight_per_symbol=config_dict.get("max_weight_per_symbol"),
            min_score=config_dict.get("min_score"),
            allow_short=config_dict.get("allow_short"),
            sharpe_ratio=source_sharpe,
            max_drawdown=source_maxdd,
            total_return=source_return,
            win_rate=source_winrate,
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error in get_active_risk_config: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while reading active RiskConfig"
        )
