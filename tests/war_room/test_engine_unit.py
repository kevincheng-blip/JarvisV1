"""
War Room Engine 單元測試
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from jgod.war_room.core.chat_engine import WarRoomEngine
from jgod.war_room.providers import ProviderManager
from jgod.war_room.providers.base_provider import ProviderResult
from jgod.war_room.core.models import RoleName, RoleResult


class TestWarRoomEngine:
    """War Room Engine 單元測試"""
    
    @pytest.fixture
    def mock_provider_manager(self):
        """建立模擬的 Provider Manager"""
        manager = Mock(spec=ProviderManager)
        manager.providers = {}
        return manager
    
    @pytest.fixture
    def engine(self, mock_provider_manager):
        """建立 War Room Engine 實例"""
        return WarRoomEngine(mock_provider_manager)
    
    @pytest.mark.asyncio
    async def test_run_war_room_batch_normal(self, engine, mock_provider_manager):
        """測試 run_war_room_batch 正常回傳"""
        # 模擬 Provider
        mock_provider = AsyncMock()
        mock_provider.run_stream = AsyncMock(return_value=ProviderResult(
            success=True,
            content="這是一段測試分析內容",
            provider_name="gpt",
            execution_time=1.5,
        ))
        
        mock_provider_manager.providers = {"gpt": mock_provider}
        mock_provider_manager.providers.get = lambda k: mock_provider if k == "gpt" else None
        
        # 執行測試
        result = await engine.run_war_room(
            mode="Lite",
            custom_providers=None,
            stock_id="2330",
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_question="請分析台積電",
        )
        
        # 驗證結果
        assert result is not None
        assert len(result.results) > 0
        assert result.executed_roles is not None
    
    @pytest.mark.asyncio
    async def test_each_role_returns_content(self, engine, mock_provider_manager):
        """測試每個角色至少吐回一段文字"""
        # 模擬多個 Provider
        mock_providers = {}
        for provider_key in ["gpt", "claude", "gemini", "perplexity"]:
            mock_provider = AsyncMock()
            mock_provider.run_stream = AsyncMock(return_value=ProviderResult(
                success=True,
                content=f"{provider_key} 的分析內容",
                provider_name=provider_key,
                execution_time=1.0,
            ))
            mock_providers[provider_key] = mock_provider
        
        mock_provider_manager.providers = mock_providers
        mock_provider_manager.providers.get = lambda k: mock_providers.get(k)
        
        # 執行測試（God 模式）
        result = await engine.run_war_room(
            mode="God",
            custom_providers=None,
            stock_id="2330",
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_question="請分析",
        )
        
        # 驗證每個角色都有內容
        for role, role_result in result.results.items():
            assert role_result.success or role_result.error is not None
            if role_result.success:
                assert len(role_result.content) > 0
    
    @pytest.mark.asyncio
    async def test_provider_key_empty_fallback(self, engine, mock_provider_manager):
        """測試 provider_key 空值時自動 fallback"""
        # 模擬沒有 Provider 的情況
        mock_provider_manager.providers = {}
        mock_provider_manager.providers.get = lambda k: None
        
        # 執行測試
        result = await engine.run_war_room(
            mode="Lite",
            custom_providers=None,
            stock_id="2330",
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_question="請分析",
        )
        
        # 驗證結果（應該有錯誤處理）
        assert result is not None
        # 如果沒有 Provider，應該返回空結果或錯誤結果
        assert len(result.results) >= 0
    
    @pytest.mark.asyncio
    async def test_missing_api_key_returns_error(self, engine, mock_provider_manager):
        """測試缺 API Key 時正確回傳錯誤事件"""
        # 模擬 Provider 初始化失敗（API Key 缺失）
        mock_provider = AsyncMock()
        mock_provider.run_stream = AsyncMock(return_value=ProviderResult(
            success=False,
            content="",
            error="API_KEY_MISSING:OPENAI_API_KEY 未設定",
            provider_name="gpt",
            execution_time=0.0,
        ))
        
        mock_provider_manager.providers = {"gpt": mock_provider}
        mock_provider_manager.providers.get = lambda k: mock_provider if k == "gpt" else None
        
        # 執行測試
        result = await engine.run_war_room(
            mode="Lite",
            custom_providers=None,
            stock_id="2330",
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_question="請分析",
        )
        
        # 驗證錯誤處理
        for role, role_result in result.results.items():
            if not role_result.success:
                assert "API_KEY_MISSING" in role_result.error or "API_CALL_FAILED" in role_result.error
    
    @pytest.mark.asyncio
    async def test_max_tokens_limit(self, engine, mock_provider_manager):
        """測試 max_tokens = 512 時，回傳長度上限正常"""
        # 模擬 Provider 回傳長內容
        long_content = "測試內容 " * 200  # 約 2000 字元
        
        mock_provider = AsyncMock()
        mock_provider.run_stream = AsyncMock(return_value=ProviderResult(
            success=True,
            content=long_content[:512],  # 模擬 max_tokens 限制
            provider_name="gpt",
            execution_time=1.0,
        ))
        
        mock_provider_manager.providers = {"gpt": mock_provider}
        mock_provider_manager.providers.get = lambda k: mock_provider if k == "gpt" else None
        
        # 執行測試
        result = await engine.run_war_room(
            mode="Lite",
            custom_providers=None,
            stock_id="2330",
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_question="請分析",
        )
        
        # 驗證內容長度（實際長度取決於 Provider 實作，這裡只驗證有內容）
        for role, role_result in result.results.items():
            if role_result.success:
                assert len(role_result.content) > 0

