"""
角色卡片組件 - 固定顯示，即時更新
"""
from typing import Optional
import streamlit as st

from jgod.council_chamber.providers.base_provider import ProviderResult

# 角色中文名稱映射
ROLE_CHINESE_NAMES = {
    "Intel Officer": "情報官",
    "Scout": "斥候",
    "Risk Officer": "風控長",
    "Quant Lead": "量化長",
    "Strategist": "股神總結人格",
    "Execution Officer": "執行官",
}

# Provider 中文名稱映射
PROVIDER_CHINESE_NAMES = {
    "Perplexity Sonar": "Perplexity",
    "Gemini Flash 2.5": "Gemini",
    "Claude 3.5 Haiku": "Claude",
    "GPT-4o-mini": "GPT",
}


def render_role_card(
    role_name: str,
    provider_name: str,
    result: Optional[ProviderResult] = None,
    loading: bool = False,
) -> None:
    """
    渲染角色卡片（聊天室風格，固定顯示，即時更新）
    
    Args:
        role_name: 角色名稱（英文）
        provider_name: Provider 名稱
        result: Provider 執行結果（可選）
        loading: 是否正在載入
    """
    # 取得中文名稱
    chinese_role_name = ROLE_CHINESE_NAMES.get(role_name, role_name)
    chinese_provider_name = PROVIDER_CHINESE_NAMES.get(provider_name, provider_name)
    
    # 角色任務描述
    role_tasks = {
        "Intel Officer": "市場資訊蒐集",
        "Scout": "快速偵查分析",
        "Risk Officer": "風險評估",
        "Quant Lead": "量化技術分析",
        "Strategist": "統整決策建議",
        "Execution Officer": "執行策略",
    }
    task_desc = role_tasks.get(role_name, "分析中")
    
    # 卡片容器（使用 st.container 確保正確渲染）
    with st.container():
        # 卡片標題區域（更專業的設計）
        col_title, col_status = st.columns([3, 1])
        
        with col_title:
            # 格式：情報官（Intel Officer）｜Perplexity
            title_text = f"**{chinese_role_name}**（{role_name}）｜{chinese_provider_name}"
            st.markdown(f"### {title_text}")
            st.caption(f"📋 {task_desc}")
        
        with col_status:
            if loading:
                st.markdown("🔄 **分析中...**")
            elif result:
                if result.success:
                    st.markdown("✅ **完成**")
                else:
                    st.markdown("❌ **錯誤**")
            else:
                st.markdown("⏳ **等待**")
        
        st.markdown("---")
        
        # 內容區域（聊天室風格）
        if loading:
            # 載入動畫
            with st.spinner(f"🔄 {chinese_role_name} 正在快速分析市場資訊..."):
                st.markdown("💭 *正在思考中...*")
        elif result:
            if result.success:
                # 成功：顯示內容（聊天室風格）
                if result.execution_time > 0:
                    st.caption(f"⏱️ 執行時間: {result.execution_time:.2f} 秒")
                
                # 使用 markdown 顯示內容，支援更好的格式
                st.markdown(result.content)
            else:
                # 失敗：根據錯誤類型顯示不同訊息
                error_msg = result.error or "未知錯誤"
                
                if error_msg.startswith("NOT_ENABLED:"):
                    # Provider 未啟用
                    st.warning(f"⚠️ **此 Provider 在目前模式未啟用**")
                    st.caption("請在左側 Sidebar 選擇對應的 Provider")
                elif error_msg.startswith("API_KEY_MISSING:"):
                    # API Key 未設定
                    actual_error = error_msg.replace("API_KEY_MISSING:", "")
                    st.error(f"❌ **此 Provider 的 API Key 未設定，相關功能暫停**")
                    st.caption(f"詳細：{actual_error}")
                    st.info("💡 請檢查環境變數設定（.env 檔案）")
                elif error_msg.startswith("API_CALL_FAILED:"):
                    # API 呼叫失敗
                    actual_error = error_msg.replace("API_CALL_FAILED:", "")
                    st.error(f"❌ **呼叫 Provider 失敗，請稍後重試**")
                    st.caption(f"錯誤：{actual_error[:100]}...")
                    st.info("💡 詳細錯誤已記錄至 logs/error/")
                else:
                    # 其他錯誤
                    st.error(f"❌ **錯誤**: {error_msg}")
                    st.info("💡 請檢查設定或稍後重試")
        else:
            # 等待狀態
            st.info(f"⏳ **等待執行** - {chinese_role_name} 準備就緒")
