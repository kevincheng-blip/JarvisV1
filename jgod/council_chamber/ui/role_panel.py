"""
角色面板：聊天室風格的角色卡片
"""
import streamlit as st
from typing import Optional, Dict
import time

from jgod.council_chamber.providers.base_provider import ProviderResult
from jgod.council_chamber.utils.error_handler import ErrorHandler, ErrorType


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

# 角色任務描述
ROLE_TASKS = {
    "Intel Officer": "市場資訊蒐集",
    "Scout": "快速偵查分析",
    "Risk Officer": "風險評估",
    "Quant Lead": "量化技術分析",
    "Strategist": "統整決策建議",
    "Execution Officer": "執行策略",
}

# Provider Logo Emoji
PROVIDER_LOGOS = {
    "GPT-4o-mini": "🤖",
    "Claude 3.5 Haiku": "🧠",
    "Gemini Flash 2.5": "💎",
    "Perplexity Sonar": "🔍",
}


class RolePanel:
    """角色面板：聊天室風格的角色卡片"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
    
    def render_role_card(
        self,
        role_name: str,
        provider_name: str,
        result: Optional[ProviderResult] = None,
        loading: bool = False,
        streaming_content: Optional[str] = None,
    ) -> None:
        """
        渲染角色卡片（聊天室風格，支援 streaming）
        
        Args:
            role_name: 角色名稱（英文）
            provider_name: Provider 名稱
            result: Provider 執行結果（可選）
            loading: 是否正在載入
            streaming_content: Streaming 內容（即時更新）
        """
        chinese_role_name = ROLE_CHINESE_NAMES.get(role_name, role_name)
        chinese_provider_name = PROVIDER_CHINESE_NAMES.get(provider_name, provider_name)
        task_desc = ROLE_TASKS.get(role_name, "分析中")
        provider_logo = PROVIDER_LOGOS.get(provider_name, "🤖")
        
        # 卡片容器（Bloomberg 風格）
        with st.container():
            # 卡片標題區域
            col_title, col_status = st.columns([4, 1])
            
            with col_title:
                # 格式：🤖 情報官（Intel Officer）｜Perplexity
                title_html = f"""
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 24px;">{provider_logo}</span>
                    <div>
                        <h3 style="margin: 0; font-weight: 600;">{chinese_role_name}（{role_name}）</h3>
                        <p style="margin: 0; color: #666; font-size: 0.9em;">{chinese_provider_name} · {task_desc}</p>
                    </div>
                </div>
                """
                st.markdown(title_html, unsafe_allow_html=True)
            
            with col_status:
                # 狀態指示器
                if loading:
                    st.markdown("🟡 **分析中...**")
                elif result:
                    if result.success:
                        st.markdown("🟢 **完成**")
                    else:
                        st.markdown("🔴 **錯誤**")
                else:
                    st.markdown("⚪ **等待**")
            
            st.markdown("---")
            
            # 內容區域（聊天室風格）
            if loading:
                # 載入動畫
                with st.spinner(f"💭 {chinese_role_name} 正在快速分析市場資訊..."):
                    st.markdown("*正在思考中...*")
                    
                    # 顯示 streaming 內容（如果有的話）
                    if streaming_content:
                        # 使用打字動畫效果
                        st.markdown(streaming_content)
                        # 顯示「正在輸入...」動畫
                        st.caption("💬 正在輸入...")
            elif result:
                if result.success:
                    # 成功：顯示內容（優先顯示 streaming 內容）
                    content = streaming_content or result.content
                    
                    if result.execution_time > 0:
                        st.caption(f"⏱️ 執行時間: {result.execution_time:.2f} 秒")
                    
                    # 使用 markdown 顯示內容，支援更好的格式
                    # 聊天室風格：使用訊息框
                    if content:
                        # 使用 HTML 實現聊天室風格
                        message_html = f"""
                        <div style="
                            background: #f8f9fa;
                            border-left: 4px solid #007bff;
                            padding: 12px 16px;
                            margin: 8px 0;
                            border-radius: 8px;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                            line-height: 1.6;
                        ">
                            <div style="color: #333;">
                                {content.replace(chr(10), '<br>')}
                            </div>
                        </div>
                        """
                        st.markdown(message_html, unsafe_allow_html=True)
                    else:
                        st.markdown(content)
                else:
                    # 失敗：使用 ErrorHandler 解析錯誤
                    error_info = self.error_handler.parse_error(result.error or "未知錯誤", provider_name)
                    title, details = self.error_handler.get_error_ui_message(error_info)
                    
                    if error_info.error_type == ErrorType.NOT_ENABLED:
                        st.warning(title)
                        st.caption(details)
                    elif error_info.error_type == ErrorType.API_KEY_MISSING:
                        st.error(title)
                        st.caption(details)
                        st.info("💡 請檢查環境變數設定（.env 檔案）")
                    else:
                        st.error(title)
                        st.caption(details)
                        if error_info.can_retry:
                            st.info("💡 請稍後重試，詳細錯誤已記錄至 logs/error/")
            else:
                # 等待狀態
                st.info(f"⏳ **等待執行** - {chinese_role_name} 準備就緒")
    
    def render_chatroom_style(
        self,
        role_name: str,
        provider_name: str,
        content: str,
        is_streaming: bool = False,
    ) -> None:
        """
        渲染聊天室風格的角色訊息（逐字輸出動畫）
        
        Args:
            role_name: 角色名稱
            provider_name: Provider 名稱
            content: 內容（會逐字顯示）
            is_streaming: 是否正在 streaming
        """
        chinese_role_name = ROLE_CHINESE_NAMES.get(role_name, role_name)
        provider_logo = PROVIDER_LOGOS.get(provider_name, "🤖")
        
        # 聊天室風格訊息框
        message_html = f"""
        <div style="
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        ">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="font-size: 20px;">{provider_logo}</span>
                <strong>{chinese_role_name}</strong>
                {('<span style="color: #28a745;">● 正在輸入...</span>' if is_streaming else '')}
            </div>
            <div style="color: #333; line-height: 1.6;">
                {content}
            </div>
        </div>
        """
        
        st.markdown(message_html, unsafe_allow_html=True)

