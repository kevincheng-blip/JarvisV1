"""
War Room Engine v6.0 單元測試
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from jgod.war_room_v6.core.engine_v6 import (
    WarRoomEngineV6,
    WarRoomRequest,
    WarRoomEvent,
)
from jgod.war_room.providers import ProviderManager
from jgod.war_room.providers.base_provider import ProviderResult


class TestWarRoomEngineV6:
    """War Room Engine v6 測試"""
    
    @pytest.fixture
    def mock_provider_manager(self):
        """建立模擬的 Provider Manager"""
        manager = Mock(spec=ProviderManager)
        manager.providers = {}
        return manager
    
    @pytest.fixture
    def engine(self, mock_provider_manager):
        """建立 War Room Engine v6 實例"""
        return WarRoomEngineV6(mock_provider_manager)
    
    @pytest.mark.asyncio
    async def test_run_session_basic_flow(self, engine, mock_provider_manager):
        """測試基本 Session 執行流程"""
        # 模擬 Provider
        mock_provider = AsyncMock()
        mock_provider.run_stream = AsyncMock(return_value=ProviderResult(
            success=True,
            content="測試分析內容",
            provider_name="gpt",
            execution_time=1.0,
        ))
        
        mock_provider_manager.providers = {"gpt": mock_provider}
        mock_provider_manager.run_role_streaming = AsyncMock(return_value=ProviderResult(
            success=True,
            content="測試分析內容",
            provider_name="gpt",
            execution_time=1.0,
        ))
        
        # 建立請求
        request = WarRoomRequest(
            session_id="test-session-001",
            stock_ids=["2330"],
            mode="god",
            enabled_providers=["gpt"],
            user_prompt="請分析台積電",
        )
        
        # 執行 Session
        events = []
        async for event in engine.run_session(request):
            events.append(event)
        
        # 驗證事件順序
        assert len(events) > 0
        assert events[0].type == "session_start"
        
        # 應該有 role_start, role_chunk (可能), role_done, summary
        event_types = [e.type for e in events]
        assert "session_start" in event_types
        assert "summary" in event_types
    
    @pytest.mark.asyncio
    async def test_run_session_event_types(self, engine, mock_provider_manager):
        """測試事件類型完整性"""
        # 模擬 Provider
        mock_provider_manager.run_role_streaming = AsyncMock(return_value=ProviderResult(
            success=True,
            content="完整內容",
            provider_name="gpt",
            execution_time=1.0,
        ))
        
        request = WarRoomRequest(
            session_id="test-session-002",
            stock_ids=["2330"],
            mode="god",
            enabled_providers=["gpt"],
            user_prompt="測試",
        )
        
        events = []
        async for event in engine.run_session(request):
            events.append(event)
            # 驗證事件結構
            assert isinstance(event, WarRoomEvent)
            assert event.session_id == "test-session-002"
            assert event.type in ["session_start", "role_start", "role_chunk", "role_done", "summary", "error"]
    
    @pytest.mark.asyncio
    async def test_run_session_error_handling(self, engine, mock_provider_manager):
        """測試錯誤處理"""
        # 模擬 Provider 失敗
        mock_provider_manager.run_role_streaming = AsyncMock(return_value=ProviderResult(
            success=False,
            content="",
            error="API_KEY_MISSING:OPENAI_API_KEY 未設定",
            provider_name="gpt",
            execution_time=0.0,
        ))
        
        request = WarRoomRequest(
            session_id="test-session-003",
            stock_ids=["2330"],
            mode="god",
            enabled_providers=["gpt"],
            user_prompt="測試",
        )
        
        events = []
        async for event in engine.run_session(request):
            events.append(event)
        
        # 應該有 role_done 事件，且包含錯誤
        role_done_events = [e for e in events if e.type == "role_done"]
        assert len(role_done_events) > 0
        assert role_done_events[0].error is not None
    
    @pytest.mark.asyncio
    async def test_run_session_no_enabled_roles(self, engine, mock_provider_manager):
        """測試沒有啟用角色的情況"""
        request = WarRoomRequest(
            session_id="test-session-004",
            stock_ids=["2330"],
            mode="custom",
            enabled_providers=[],  # 空列表
            user_prompt="測試",
        )
        
        events = []
        async for event in engine.run_session(request):
            events.append(event)
        
        # 應該有 error 事件
        error_events = [e for e in events if e.type == "error"]
        assert len(error_events) > 0
    
    def test_war_room_request_dataclass(self):
        """測試 WarRoomRequest dataclass"""
        request = WarRoomRequest(
            session_id="test-001",
            stock_ids=["2330"],
            mode="god",
            enabled_providers=["gpt"],
            user_prompt="測試",
        )
        
        assert request.session_id == "test-001"
        assert request.stock_ids == ["2330"]
        assert request.mode == "god"
        assert request.enabled_providers == ["gpt"]
        assert request.max_tokens == 512  # 預設值
    
    def test_war_room_event_dict(self):
        """測試 WarRoomEvent.dict() 方法"""
        event = WarRoomEvent(
            type="role_chunk",
            session_id="test-001",
            role="Intel Officer",
            role_label="情報官",
            provider="perplexity",
            chunk="測試 chunk",
        )
        
        event_dict = event.dict()
        assert isinstance(event_dict, dict)
        assert event_dict["type"] == "role_chunk"
        assert event_dict["session_id"] == "test-001"
        assert event_dict["chunk"] == "測試 chunk"

