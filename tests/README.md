# War Room v5.0 測試套件

## 測試結構

```
tests/
├── conftest.py                          # Pytest 配置與共用 Fixtures
├── war_room/
│   ├── test_engine_unit.py             # Engine 單元測試
│   └── test_war_room_integration.py    # 整合測試
└── providers/
    └── test_provider_manager.py        # Provider Manager 單元測試
```

## 執行測試

### 安裝依賴
```bash
# 安裝所有依賴（包含 pytest 和 pytest-asyncio）
pip install -r requirements.txt

# 或僅安裝測試相關依賴
pip install pytest pytest-asyncio
```

### 執行所有測試
```bash
pytest tests/ -v
```

### 執行特定測試套件
```bash
# Engine 單元測試
pytest tests/war_room/test_engine_unit.py -v

# Provider Manager 測試
pytest tests/providers/test_provider_manager.py -v

# 整合測試
pytest tests/war_room/test_war_room_integration.py -v
```

## 測試項目

### Engine 單元測試 (`test_engine_unit.py`)
- ✅ `run_war_room_batch` 正常回傳
- ✅ 每個角色至少吐回一段文字
- ✅ provider_key 空值時自動 fallback
- ✅ 缺 API Key 時正確回傳錯誤事件
- ✅ max_tokens = 512 時，回傳長度上限正常

### Provider Manager 單元測試 (`test_provider_manager.py`)
- ✅ OpenAI provider 初始化
- ✅ Claude provider 初始化
- ✅ Gemini provider 初始化
- ✅ Perplexity provider 初始化
- ✅ 任一 provider 未設定 API Key → 應回傳合理錯誤，不應 crash
- ✅ `ask()` / `ask_stream()` 正常回傳格式

### 整合測試 (`test_war_room_integration.py`)
- ✅ God 模式：所有角色正確啟用
- ✅ Custom 模式：自訂 provider only 流程
- ✅ Engine 事件流（Streaming）順序檢查
- ✅ 測試資料：2330 / 2412 / 2603 / 1101

## 注意事項

- 測試不需要實際的 API Key 即可執行（使用 Mock）
- 如果 API Key 已設定，部分測試會進行真實 API 呼叫
- 整合測試可能需要較長時間（取決於 API 回應速度）

