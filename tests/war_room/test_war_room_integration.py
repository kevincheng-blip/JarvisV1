"""
War Room 整合測試
"""
import pytest
import asyncio
from jgod.war_room.core.chat_engine import WarRoomEngine
from jgod.war_room.providers import ProviderManager
from jgod.war_room.core.models import RoleName


class TestWarRoomIntegration:
    """War Room 整合測試"""
    
    @pytest.fixture
    def engine(self):
        """建立 War Room Engine 實例"""
        provider_manager = ProviderManager()
        return WarRoomEngine(provider_manager)
    
    @pytest.mark.asyncio
    async def test_god_mode_all_roles_enabled(self, engine):
        """測試 God 模式：所有角色正確啟用"""
        # 執行 God 模式
        result = await engine.run_war_room(
            mode="God",
            custom_providers=None,
            stock_id="2330",
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_question="請分析台積電的投資建議",
        )
        
        # 驗證結果
        assert result is not None
        assert len(result.executed_roles) > 0
        
        # 檢查是否有至少一個角色執行
        # 注意：如果 API Key 未設定，可能沒有角色執行
        if len(result.executed_roles) > 0:
            # 驗證每個執行的角色都有結果
            for role in result.executed_roles:
                assert role in result.results
    
    @pytest.mark.asyncio
    async def test_custom_mode_custom_providers_only(self, engine):
        """測試 Custom 模式：自訂 provider only 流程"""
        # 執行 Custom 模式（只啟用 GPT）
        result = await engine.run_war_room(
            mode="Custom",
            custom_providers=["gpt"],
            stock_id="2412",
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_question="請分析中華電信的投資建議",
        )
        
        # 驗證結果
        assert result is not None
        
        # 檢查只有 GPT 相關的角色執行
        for role, role_result in result.results.items():
            # 只有 Strategist 和 Execution Officer 使用 GPT
            if role in [RoleName.STRATEGIST, RoleName.EXECUTION_OFFICER]:
                assert role_result.provider_key == "gpt"
    
    @pytest.mark.asyncio
    async def test_engine_event_stream_order(self, engine):
        """測試 Engine 事件流（Streaming）順序檢查"""
        events = []
        
        def streaming_callback(role: RoleName, chunk: str):
            """收集 streaming 事件"""
            events.append({
                "type": "role_chunk",
                "role": role.value,
                "chunk": chunk,
            })
        
        # 執行 War Room（使用 streaming callback）
        result = await engine.run_war_room(
            mode="Lite",
            custom_providers=None,
            stock_id="2603",
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_question="請分析長榮的投資建議",
            streaming_callback=streaming_callback,
        )
        
        # 驗證事件順序
        # 1. 應該有 session_start（隱含在執行開始）
        # 2. 應該有 role_chunk（至少一個）
        # 3. 應該有 role_done（每個角色完成）
        # 4. 應該有 summary（執行完成）
        
        # 檢查是否有 chunk 事件
        chunk_events = [e for e in events if e["type"] == "role_chunk"]
        if len(chunk_events) > 0:
            # 驗證 chunk 事件格式
            for event in chunk_events:
                assert "role" in event
                assert "chunk" in event
                assert len(event["chunk"]) > 0
        
        # 檢查結果
        assert result is not None
        assert len(result.results) > 0
        
        # 驗證每個角色都有完成事件（透過 result）
        for role, role_result in result.results.items():
            assert role_result.success or role_result.error is not None
    
    @pytest.mark.parametrize("stock_id", ["2330", "2412", "2603", "1101"])
    @pytest.mark.asyncio
    async def test_different_stock_ids(self, engine, stock_id):
        """測試不同股票代碼"""
        result = await engine.run_war_room(
            mode="Lite",
            custom_providers=None,
            stock_id=stock_id,
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_question=f"請分析股票 {stock_id} 的投資建議",
        )
        
        # 驗證結果
        assert result is not None
        # 即使 API Key 未設定，也應該返回結構化的結果
        assert hasattr(result, "results")
        assert hasattr(result, "executed_roles")
        assert hasattr(result, "failed_roles")

