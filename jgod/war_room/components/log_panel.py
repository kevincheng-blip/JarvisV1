"""
戰情室紀錄面板
"""
from datetime import datetime
from pathlib import Path
from typing import Dict
import streamlit as st
import logging

from jgod.war_room.providers.base_provider import ProviderResult

# 設定日誌
logger = logging.getLogger("war_room")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def save_war_room_log(
    question: str,
    role_results: Dict[str, ProviderResult],
    strategist_result: ProviderResult,
    mode: str = "Unknown",
    enabled_providers: list = None,
) -> str:
    """
    儲存戰情室會議紀錄
    
    Args:
        question: 原始問題
        role_results: 各角色結果
        strategist_result: Strategist 總結
        mode: 模式（Lite/Pro/God）
        enabled_providers: 啟用的 Provider 列表
    
    Returns:
        檔案路徑
    """
    log_dir = Path("logs/war_room")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    log_file = log_dir / f"{timestamp}.md"
    
    # 建立 Markdown 內容
    content = f"""# J-GOD 戰情室會議紀錄

**時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**模式**: {mode}
**啟用的 Provider**: {', '.join(enabled_providers) if enabled_providers else 'Unknown'}

## 原始問題

{question}

## 各角色意見

"""
    
    for role_name, result in role_results.items():
        content += f"### {role_name}\n\n"
        content += f"**Provider**: {result.provider_name}\n\n"
        if result.success:
            content += f"{result.content}\n\n"
            if result.execution_time > 0:
                content += f"*執行時間: {result.execution_time:.2f} 秒*\n\n"
        else:
            content += f"**錯誤**: {result.error}\n\n"
        content += "---\n\n"
    
    content += f"""## Strategist 總結

**Provider**: {strategist_result.provider_name}

{strategist_result.content if strategist_result.success else f"**錯誤**: {strategist_result.error}"}

---
*本紀錄由 J-GOD 系統自動產生*
"""
    
    # 寫入檔案
    log_file.write_text(content, encoding="utf-8")
    
    # 記錄到 logger
    logger.info(f"War Room log saved: {log_file}")
    logger.info(f"Mode: {mode}, Enabled Providers: {enabled_providers}")
    
    return str(log_file)


def render_log_download_button(log_file_path: str) -> None:
    """渲染下載按鈕"""
    if Path(log_file_path).exists():
        with open(log_file_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        
        st.download_button(
            label="📥 下載會議紀錄",
            data=log_content,
            file_name=Path(log_file_path).name,
            mime="text/markdown",
            key="download_war_room_log",
        )

