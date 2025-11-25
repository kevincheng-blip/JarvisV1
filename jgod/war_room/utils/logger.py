"""
戰情室日誌記錄器
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class WarRoomLogger:
    """戰情室專用日誌記錄器"""
    
    def __init__(self, log_dir: str = "logs/war_room"):
        """
        初始化日誌記錄器
        
        Args:
            log_dir: 日誌目錄
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 設定 logger
        self.logger = logging.getLogger("war_room")
        self.logger.setLevel(logging.INFO)
        
        # 如果還沒有 handler，則新增
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # File handler
            log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def log_execution(
        self,
        mode: str,
        enabled_providers: list,
        question: str,
        execution_time: float,
        results: Dict[str, Any],
    ):
        """
        記錄戰情室執行資訊
        
        Args:
            mode: 模式
            enabled_providers: 啟用的 Provider 列表
            question: 問題
            execution_time: 執行時間
            results: 結果字典
        """
        self.logger.info("=" * 60)
        self.logger.info("War Room Execution")
        self.logger.info(f"Mode: {mode}")
        self.logger.info(f"Enabled Providers: {enabled_providers}")
        self.logger.info(f"Question: {question}")
        self.logger.info(f"Execution Time: {execution_time:.2f} seconds")
        self.logger.info(f"Results: {list(results.keys())}")
        self.logger.info("=" * 60)
    
    def log_role_complete(self, role_name: str, success: bool, execution_time: float):
        """記錄角色完成"""
        status = "✅" if success else "❌"
        self.logger.info(f"{status} Role {role_name} completed in {execution_time:.2f}s")
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """記錄錯誤"""
        self.logger.error(f"Error in {context or {}}: {error}", exc_info=True)

