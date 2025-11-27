# Data Feed 模組

## 概述

Data Feed 模組是創世紀量化系統 Step 1 的核心組件，負責統一處理多家 API 來源的 Tick 資料。

## 核心組件

### 1. UnifiedTick

統一的 Tick 數據結構，所有 API 來源最終都要轉換成這個格式。

```python
from data_feed import UnifiedTick

tick = UnifiedTick(
    timestamp=1234567890.123,
    symbol="2330.TW",
    source="sinopac",
    price=750.0,
    volume=100,
    bid_price=749.5,
    ask_price=750.5,
)
```

### 2. BaseTickConverter

抽象基底類別，規範不同 API 來源的轉換流程。

所有具體的 Converter（SinopacConverter、XQConverter、PolygonConverter 等）都必須繼承此類別。

### 3. SinopacConverter

永豐 Sinopac API 的轉換器（目前為骨架版本，待正式 API 文件後完善）。

```python
from data_feed import SinopacConverter

converter = SinopacConverter()
unified_tick = converter.convert_to_unified(raw_data)
```

### 4. MockSinopacAPI

模擬永豐 API 的資料來源，用於開發與測試。

```python
from data_feed import MockSinopacAPI

mock_api = MockSinopacAPI(symbol="2330", base_price=750.0, price_range=10.0)
raw_tick = mock_api.get_next_raw_tick()
```

## 使用範例

### 完整流程：Mock API → Converter → UnifiedTick

```python
from data_feed import MockSinopacAPI, SinopacConverter

# 1. 建立 Mock API
mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)

# 2. 建立 Converter
converter = SinopacConverter()

# 3. 取得原始 Tick 並轉換
raw_tick = mock_api.get_next_raw_tick()
unified_tick = converter.convert_to_unified(raw_tick)

print(f"統一格式: {unified_tick}")
```

## 後續步驟

完成 Step 1 後，可以：

1. **接 InfoTimeEngine（Volume Bar）**：使用 UnifiedTick 作為輸入
2. **接 Factor Engine**：F_Orderbook、F_PT、F_MRR、F_Inertia 等因子引擎
3. **擴展其他 API 來源**：XQ、Polygon 等（只需建立對應的 Converter）

## 檔案結構

```
data_feed/
├── __init__.py          # 模組初始化
├── tick_handler.py      # 核心實作
└── README.md            # 本文件
```

## 測試

執行測試：

```bash
python3 data_feed/tick_handler.py
```

或使用 pytest：

```bash
pytest tests/data_feed/test_tick_handler.py -v
```

## 注意事項

- **SinopacConverter 目前為骨架版本**：待正式 API 文件後再完善欄位映射邏輯
- **MockSinopacAPI 用於開發測試**：正式 API 準備好後，只需修改 Converter 即可無痛切換
- **UnifiedTick 為全系統標準格式**：所有後續模組都應使用此格式

