"""
J-GOD AI Policy Service v1 - Log Reader / 實驗分析組件

純後端、純 Python 的「Path A 回測 Log 分析器」，
作為未來 AI Policy Service 的基礎。

功能：
- 讀取 data/path_a_backtest_logs.jsonl（JSON Lines）
- 分析與排名回測實驗
- 計算綜合分數（Sharpe Ratio + Max Drawdown）
- 過濾與排序（依交易日數、交易次數、日期區間等）

設計原則：
- 只讀不回寫（不修改任何 Log 檔案）
- 不動任何既有模組（Feature / Strategy / Decision / Path A）
- 不做「自動調參」，先做排序與分析的 MVP
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PolicyScoreConfig:
    """
    Policy 評分配置
    
    用來決定如何計算綜合分數與過濾實驗
    """
    sharpe_weight: float = 0.7  # Sharpe Ratio 權重（預設 0.7）
    max_dd_weight: float = 0.3  # Max Drawdown 權重（預設 0.3）
    min_days: int = 60  # 最少交易日數（少於這個就忽略）
    min_trades: int = 30  # 最少總交易次數（少於這個就忽略）
    
    def __post_init__(self):
        """驗證權重總和為 1.0"""
        total_weight = self.sharpe_weight + self.max_dd_weight
        if abs(total_weight - 1.0) > 1e-6:
            logger.warning(
                f"PolicyScoreConfig weights sum to {total_weight}, not 1.0. "
                f"Normalizing to 1.0."
            )
            # 正規化權重
            self.sharpe_weight = self.sharpe_weight / total_weight
            self.max_dd_weight = self.max_dd_weight / total_weight


@dataclass
class PolicyExperimentSummary:
    """
    一筆回測實驗 + 評分結果
    
    包含原始 log record 的所有欄位，加上衍生欄位（score, is_valid, reason）
    """
    run_id: str
    timestamp: str
    start_date: str
    end_date: str
    initial_capital: float
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_commission: float
    num_long_trades: int
    num_short_trades: int
    num_days: int
    final_capital: float
    
    # 衍生欄位
    score: float = 0.0  # 依 config 計算出來的綜合分數
    is_valid: bool = True  # 是否通過基本過濾
    reason: str = ""  # 若無效，簡短說明
    
    # Decision / 回測設定（從原始 log 來的）
    long_budget: Optional[float] = None
    short_budget: Optional[float] = None
    max_weight_per_symbol: Optional[float] = None
    min_score: Optional[float] = None
    allow_short: Optional[bool] = None
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": self.initial_capital,
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "annualized_volatility": self.annualized_volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "total_commission": self.total_commission,
            "num_long_trades": self.num_long_trades,
            "num_short_trades": self.num_short_trades,
            "num_days": self.num_days,
            "final_capital": self.final_capital,
            "score": self.score,
            "is_valid": self.is_valid,
            "reason": self.reason,
            "long_budget": self.long_budget,
            "short_budget": self.short_budget,
            "max_weight_per_symbol": self.max_weight_per_symbol,
            "min_score": self.min_score,
            "allow_short": self.allow_short,
        }


class PolicyLogReaderV1:
    """
    Policy Log Reader v1
    
    核心功能：
    - 讀取 Path A 回測 Log（JSON Lines）
    - 轉換為 PolicyExperimentSummary
    - 計算綜合分數
    - 過濾與排序實驗
    """
    
    def __init__(
        self,
        log_path: str = "data/path_a_backtest_logs.jsonl",
        score_config: Optional[PolicyScoreConfig] = None,
    ):
        """
        初始化 Policy Log Reader
        
        Args:
            log_path: Log 檔案路徑
            score_config: 評分配置（如果為 None，使用預設配置）
        """
        self.log_path = Path(log_path)
        self.score_config = score_config or PolicyScoreConfig()
    
    def load_logs(self) -> List[dict]:
        """
        從 log_path 讀取 JSON Lines
        
        每行 json.loads，失敗就略過並記錄警告（用 logging）
        
        Returns:
            List[dict]: 原始 dict list，不丟例外（除非檔案不存在）
        
        Raises:
            FileNotFoundError: 如果 log 檔案不存在
        """
        if not self.log_path.exists():
            raise FileNotFoundError(f"Log file not found: {self.log_path}")
        
        logs = []
        failed_lines = 0
        
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        logs.append(record)
                    except json.JSONDecodeError as e:
                        failed_lines += 1
                        logger.warning(
                            f"Failed to parse JSON at line {line_num} in {self.log_path}: {e}"
                        )
        
        except Exception as e:
            logger.error(f"Error reading log file {self.log_path}: {e}")
            raise
        
        if failed_lines > 0:
            logger.warning(f"Skipped {failed_lines} invalid lines in {self.log_path}")
        
        logger.info(f"Loaded {len(logs)} log records from {self.log_path}")
        return logs
    
    def to_experiment_summary(self, raw_record: dict) -> PolicyExperimentSummary:
        """
        從一筆原始 log record 轉成 PolicyExperimentSummary
        
        Args:
            raw_record: 原始 log record（從 JSON Lines 讀取的 dict）
        
        Returns:
            PolicyExperimentSummary: 轉換後的摘要物件
        
        安全處理：
        - 缺少欄位 → is_valid=False，reason 填上 "missing_field: xxx"
        - NaN / None / 無法轉 float 的數字 → is_valid=False
        """
        # 檢查必填欄位
        required_fields = [
            "run_id", "timestamp", "start_date", "end_date",
            "initial_capital", "total_return", "annualized_return",
            "annualized_volatility", "sharpe_ratio", "max_drawdown",
            "win_rate", "total_commission", "num_long_trades",
            "num_short_trades", "num_days", "final_capital",
        ]
        
        missing_fields = [f for f in required_fields if f not in raw_record]
        if missing_fields:
            # 建立一個部分填滿的 summary，但標記為無效
            try:
                return PolicyExperimentSummary(
                    run_id=raw_record.get("run_id", "unknown"),
                    timestamp=raw_record.get("timestamp", ""),
                    start_date=raw_record.get("start_date", ""),
                    end_date=raw_record.get("end_date", ""),
                    initial_capital=0.0,
                    total_return=0.0,
                    annualized_return=0.0,
                    annualized_volatility=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    total_commission=0.0,
                    num_long_trades=0,
                    num_short_trades=0,
                    num_days=0,
                    final_capital=0.0,
                    is_valid=False,
                    reason=f"missing_field: {', '.join(missing_fields)}",
                    long_budget=raw_record.get("long_budget"),
                    short_budget=raw_record.get("short_budget"),
                    max_weight_per_symbol=raw_record.get("max_weight_per_symbol"),
                    min_score=raw_record.get("min_score"),
                    allow_short=raw_record.get("allow_short"),
                )
            except Exception as e:
                logger.warning(f"Failed to create PolicyExperimentSummary: {e}")
                return PolicyExperimentSummary(
                    run_id="unknown",
                    timestamp="",
                    start_date="",
                    end_date="",
                    initial_capital=0.0,
                    total_return=0.0,
                    annualized_return=0.0,
                    annualized_volatility=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    total_commission=0.0,
                    num_long_trades=0,
                    num_short_trades=0,
                    num_days=0,
                    final_capital=0.0,
                    is_valid=False,
                    reason=f"parse_error: {str(e)}",
                )
        
        # 安全轉換數值欄位
        def safe_float(value, default=0.0):
            if value is None:
                return default
            try:
                result = float(value)
                if not (result == result):  # Check for NaN
                    return default
                return result
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=0):
            if value is None:
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        def safe_bool(value, default=False):
            if value is None:
                return default
            return bool(value)
        
        # 轉換所有欄位
        try:
            summary = PolicyExperimentSummary(
                run_id=str(raw_record["run_id"]),
                timestamp=str(raw_record["timestamp"]),
                start_date=str(raw_record["start_date"]),
                end_date=str(raw_record["end_date"]),
                initial_capital=safe_float(raw_record["initial_capital"]),
                total_return=safe_float(raw_record["total_return"]),
                annualized_return=safe_float(raw_record["annualized_return"]),
                annualized_volatility=safe_float(raw_record["annualized_volatility"]),
                sharpe_ratio=safe_float(raw_record["sharpe_ratio"]),
                max_drawdown=safe_float(raw_record["max_drawdown"]),
                win_rate=safe_float(raw_record["win_rate"]),
                total_commission=safe_float(raw_record["total_commission"]),
                num_long_trades=safe_int(raw_record["num_long_trades"]),
                num_short_trades=safe_int(raw_record["num_short_trades"]),
                num_days=safe_int(raw_record["num_days"]),
                final_capital=safe_float(raw_record["final_capital"]),
                long_budget=raw_record.get("long_budget"),
                short_budget=raw_record.get("short_budget"),
                max_weight_per_symbol=raw_record.get("max_weight_per_symbol"),
                min_score=raw_record.get("min_score"),
                allow_short=raw_record.get("allow_short"),
            )
        except Exception as e:
            logger.warning(f"Failed to create PolicyExperimentSummary: {e}")
            return PolicyExperimentSummary(
                run_id=str(raw_record.get("run_id", "unknown")),
                timestamp=str(raw_record.get("timestamp", "")),
                start_date=str(raw_record.get("start_date", "")),
                end_date=str(raw_record.get("end_date", "")),
                initial_capital=0.0,
                total_return=0.0,
                annualized_return=0.0,
                annualized_volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_commission=0.0,
                num_long_trades=0,
                num_short_trades=0,
                num_days=0,
                final_capital=0.0,
                is_valid=False,
                reason=f"parse_error: {str(e)}",
            )
        
        # 檢查資料有效性
        if summary.sharpe_ratio <= 0 or summary.max_drawdown <= 0:
            summary.is_valid = False
            summary.reason = "invalid_metrics: sharpe_ratio or max_drawdown <= 0"
        
        return summary
    
    def compute_score(self, summary: PolicyExperimentSummary) -> float:
        """
        使用 score_config 計算綜合分數
        
        Args:
            summary: PolicyExperimentSummary（會修改 summary.score）
        
        Returns:
            float: 計算出的分數
        
        公式：
        - normalized_sharpe = sharpe_ratio（越大越好）
        - normalized_max_dd = 1.0 - max_drawdown（假設 max_drawdown 在 0~1 之間，越小越好）
        - score = sharpe_weight * normalized_sharpe + max_dd_weight * normalized_max_dd
        """
        # 若 summary.is_valid 為 False → 回傳非常小的分數
        if not summary.is_valid:
            summary.score = -1e9
            return summary.score
        
        # 處理安全性：若 sharpe_ratio 或 max_drawdown 缺失或 <= 0 → is_valid=False
        if summary.sharpe_ratio <= 0 or summary.max_drawdown <= 0:
            summary.is_valid = False
            summary.reason = "invalid_metrics: sharpe_ratio or max_drawdown <= 0"
            summary.score = -1e9
            return summary.score
        
        # 確保 max_drawdown 在合理範圍（0~1）
        max_dd_clamped = max(0.0, min(1.0, summary.max_drawdown))
        
        # 計算 normalized 值
        normalized_sharpe = summary.sharpe_ratio  # 越大越好，可以不用再標準化
        normalized_max_dd = 1.0 - max_dd_clamped  # 越小越好（drawdown 越小 → normalized 越大）
        
        # 計算綜合分數
        score = (
            self.score_config.sharpe_weight * normalized_sharpe +
            self.score_config.max_dd_weight * normalized_max_dd
        )
        
        summary.score = score
        return score
    
    def filter_and_rank(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        top_n: int = 20,
    ) -> List[PolicyExperimentSummary]:
        """
        主要流程：過濾與排序實驗
        
        Args:
            start_date: 開始日期（選填，字串 YYYY-MM-DD）
            end_date: 結束日期（選填，字串 YYYY-MM-DD）
            top_n: 回傳前 N 筆（預設 20）
        
        Returns:
            List[PolicyExperimentSummary]: 排序後的實驗摘要列表
        """
        # 1. 讀取 logs
        try:
            raw_logs = self.load_logs()
        except FileNotFoundError:
            logger.error(f"Log file not found: {self.log_path}")
            return []
        
        if not raw_logs:
            logger.warning("No log records found")
            return []
        
        # 2. 轉成 PolicyExperimentSummary list
        summaries = []
        for raw_record in raw_logs:
            summary = self.to_experiment_summary(raw_record)
            summaries.append(summary)
        
        # 3. 依 score_config.min_days、min_trades 過濾
        for summary in summaries:
            if summary.num_days < self.score_config.min_days:
                summary.is_valid = False
                summary.reason = f"too_few_days: {summary.num_days} < {self.score_config.min_days}"
            
            num_trades = summary.num_long_trades + summary.num_short_trades
            if num_trades < self.score_config.min_trades:
                summary.is_valid = False
                summary.reason = f"too_few_trades: {num_trades} < {self.score_config.min_trades}"
        
        # 4. 日期區間過濾（如有 start_date / end_date 參數）
        if start_date:
            summaries = [
                s for s in summaries
                if s.start_date >= start_date
            ]
        
        if end_date:
            summaries = [
                s for s in summaries
                if s.end_date <= end_date
            ]
        
        # 5. 對每個 summary 呼叫 compute_score
        for summary in summaries:
            self.compute_score(summary)
        
        # 6. 只保留 is_valid=True 的
        valid_summaries = [s for s in summaries if s.is_valid]
        
        # 7. 依 score 由高到低排序
        valid_summaries.sort(key=lambda x: x.score, reverse=True)
        
        # 8. 回傳前 top_n 筆
        return valid_summaries[:top_n]

