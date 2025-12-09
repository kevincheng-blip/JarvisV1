# J-GOD Decision Layer v1 SPEC

**版本**: v1.0  
**實作日期**: 2025-12-09  
**狀態**: ✅ 已完成

---

## 概述

Decision Layer v1 是 J-GOD 系統中的「Raw Score → Final Score（Doctrine 仲裁層）」，負責：

- 接收 Raw Score（由策略 / Prediction Engine 計算）
- 查詢 Doctrine 知識庫（透過 KnowledgeBrain）
- 呼叫 LLM 進行定性仲裁
- 輸出 Final Score、Doctrine Flags、調整理由

**原則**: Raw Score 不被覆寫，只被「附加修正與說明」，Final Score 由 Decision Layer 統一輸出。

---

## 模組結構

```
jgod/decision/
  __init__.py              # 模組匯出
  models.py                # 資料結構定義
  config.py                # 配置類別
  llm_client.py            # LLM 封裝（重用現有 API clients）
  prompt_builder.py        # Prompt 組裝
  engine.py                # DecisionEngineV1 核心邏輯
  integration_policy.py    # 整合函式
```

---

## 資料模型

### RawScoreItem（輸入）

```python
@dataclass
class RawScoreItem:
    symbol: str
    name: Optional[str]
    date: date
    raw_score: float
    strategy_scores: Dict[str, float]  # {"S1_momentum": 0.85, ...}
    risk_metrics: Dict[str, float]     # {"vol_20d": 0.3, ...}
    context_tags: List[str]            # ["high_beta", "low_liquidity"]
```

### DecisionOutput（輸出）

```python
@dataclass
class DecisionOutput:
    symbol: str
    date: date
    raw_score: float
    final_score: float                  # = raw_score * correction_factor
    correction_factor: float            # 0.5 ~ 1.5
    doctrine_flags: List[DoctrineFlag]  # 風險標籤
    adjustment_reason: str              # 調整理由
    llm_model: str                      # 使用的模型
```

### DoctrineFlag

```python
@dataclass
class DoctrineFlag:
    code: str                           # "over_concentration"
    severity: str                       # "info" | "warning" | "critical"
    message: str                        # 短說明
    doctrine_refs: List[str]            # ["Book_03#S12", ...]
```

---

## DecisionEngineV1 核心邏輯

### 初始化

```python
engine = DecisionEngineV1(
    config=DecisionConfig(...),
    knowledge_brain=knowledge_brain_instance
)
```

### 主要方法

1. **`decide_for_single(raw_item: RawScoreItem) -> DecisionOutput`**
   - 處理單一 Raw Score 項目
   - 內部流程：
     1. 建立決策上下文
     2. 查詢 Doctrine（如果啟用）
     3. 呼叫 LLM（如果啟用）
     4. 套用修正並計算 Final Score

2. **`decide_for_batch(raw_items: List[RawScoreItem]) -> DecisionBatchResult`**
   - 批次處理多個項目
   - 包含錯誤處理（單一項目失敗不影響其他項目）

---

## KnowledgeBrain / Doctrine 整合

### 查詢方法

```python
doctrine_hits = knowledge_brain.search_doctrine(
    query=query_string,  # 例如: "2330, high raw_score 0.92, high volatility"
    top_k=5
)
```

### Query 組合邏輯

決策引擎會組合以下資訊建立查詢字串：
- symbol
- raw_score
- risk_metrics 關鍵欄位
- context_tags
- 已知 error patterns

---

## LLM Prompt & 呼叫

### Prompt 結構

`prompt_builder.py` 會建立包含以下區塊的 Prompt：

1. **System / Role 說明**
   - 說明 Decision Layer 的職責
   - 強調 correction_factor 範圍（0.5 ~ 1.5）

2. **Input 概況**
   - symbol, name, date
   - raw_score
   - strategy_scores
   - risk_metrics
   - context_tags

3. **Doctrine 條文摘要**
   - 以 bullet 方式列出 doctrine_hits 的 summary / core_principles / risk_rules

4. **輸出格式要求**
   - 要求回傳 JSON 格式：
     ```json
     {
       "correction_factor": <float>,
       "doctrine_flags": [...],
       "adjustment_reason": "<string>"
     }
     ```

### LLM 支援

Decision Layer 支援以下 Provider（透過 `api_clients/`）：
- **GPTProvider** (OpenAI): `gpt-4o-mini`, `gpt-4o`, etc.
- **GeminiProvider**: `gemini-2.5-flash`, etc.
- **ClaudeProvider**: `claude-3-5-sonnet-20241022`, etc.

模型選擇由 `DecisionConfig.llm_model` 決定，會自動選擇對應的 Provider。

### 錯誤處理

- LLM 呼叫失敗 → fallback `correction_factor = 1.0`
- JSON 解析失敗 → fallback `correction_factor = 1.0`
- 超時 → fallback `correction_factor = 1.0`
- 所有錯誤都會記錄 log

---

## Final Score 計算與限制

### 基本計算

```
final_score = raw_score * correction_factor
```

### 邊界限制

- `raw_score` 假設範圍: `[0, 1]`
- `correction_factor` 範圍: `[min_correction, max_correction]` (預設 `[0.5, 1.5]`)
- 若 LLM 給的 factor 超出範圍：
  - 自動 clip 到安全範圍
  - 在 `adjustment_reason` 加註說明

---

## 配置（DecisionConfig）

```python
@dataclass
class DecisionConfig:
    llm_model: str = "gpt-4o-mini"
    max_correction: float = 1.5
    min_correction: float = 0.5
    doctrine_top_k: int = 5
    enable_doctrine: bool = True
    enable_llm: bool = True
    llm_timeout: int = 30
    llm_max_retries: int = 2
    fallback_correction_factor: float = 1.0
```

### 使用場景

- **關閉 LLM** (`enable_llm=False`): 只用 rule-based，`correction_factor = 1.0`
- **關閉 Doctrine** (`enable_doctrine=False`): 不查詢 Doctrine，但 LLM 仍可使用
- **測試模式**: 可以關閉 LLM 測試其他功能

---

## 整合函式

### generate_final_predictions

```python
from jgod.decision import generate_final_predictions, DecisionEngineV1

engine = DecisionEngineV1(config, knowledge_brain)
raw_items = [...]  # List[RawScoreItem]

final_predictions = generate_final_predictions(raw_items, engine)
# 回傳: List[DecisionOutput]（已按 final_score 降序排序）
```

這個函式供以下使用：
- **TopN API**: `/api/v1/predictions/top-n/long` / `/short`
- **Final Orders API**: `/api/v1/orders/final`
- **War Room**: 顯示 Final Score 排行榜

---

## 錯誤處理與 Logging

### 必須 Log 的事件

1. LLM 呼叫失敗
2. Doctrine 查詢返回空結果
3. LLM 回傳 JSON parse 失敗
4. correction_factor 被 clip
5. 批次處理中的單一項目錯誤

### Log 內容

- symbol
- date
- raw_score
- 使用的 llm_model
- 錯誤原因

未來可將這些 log 餵回 ErrorLearningEngine。

---

## 測試

單元測試位於 `tests/decision/test_decision_engine_v1.py`，涵蓋：

- ✅ LLM 關閉時：`final_score = raw_score`
- ✅ Doctrine 關閉時：引擎仍能正常運作
- ✅ correction_factor clipping
- ✅ 批次處理
- ✅ `generate_final_predictions` 整合
- ✅ 錯誤處理

---

## 使用範例

```python
from jgod.decision import (
    DecisionEngineV1,
    DecisionConfig,
    RawScoreItem,
    generate_final_predictions
)
from jgod.council_chamber.knowledge_gateway import get_knowledge_brain
from datetime import date

# 1. 初始化
config = DecisionConfig(
    llm_model="gpt-4o-mini",
    enable_llm=True,
    enable_doctrine=True
)
knowledge_brain = get_knowledge_brain()
engine = DecisionEngineV1(config, knowledge_brain)

# 2. 準備 Raw Scores
raw_items = [
    RawScoreItem(
        symbol="2330",
        name="台積電",
        date=date.today(),
        raw_score=0.85,
        strategy_scores={"S1_momentum": 0.9, "S2_value": 0.8},
        risk_metrics={"vol_20d": 0.25},
        context_tags=["high_beta", "tech_sector"]
    ),
    # ... 更多項目
]

# 3. 產生 Final Scores
final_predictions = generate_final_predictions(raw_items, engine)

# 4. 使用結果
for output in final_predictions:
    print(f"{output.symbol}: {output.raw_score:.3f} → {output.final_score:.3f}")
    print(f"  修正係數: {output.correction_factor:.3f}")
    print(f"  理由: {output.adjustment_reason}")
    if output.doctrine_flags:
        print(f"  風險標籤: {[f.code for f in output.doctrine_flags]}")
```

---

## 後續整合

### TopN API

需要修改 `/api/v1/predictions/top-n/long` 和 `/short`：

1. 從 Prediction Engine 取得 Raw Scores
2. 呼叫 `generate_final_predictions()`
3. 按 `final_score` 排序
4. 回傳 `DecisionOutput` 列表（轉換為 API 格式）

### Final Orders API

需要修改 `/api/v1/orders/final`：

1. 從 Decision Layer 取得 Final Scores
2. 檢查 `doctrine_flags` 中是否有 `critical` 等級
3. 如果嚴重，可設定 `blocked: bool`

---

## 實作狀態

- ✅ 資料模型 (`models.py`)
- ✅ 配置 (`config.py`)
- ✅ LLM 封裝 (`llm_client.py`) - 重用現有 API clients
- ✅ Prompt 組裝 (`prompt_builder.py`)
- ✅ 核心引擎 (`engine.py`)
- ✅ 整合函式 (`integration_policy.py`)
- ✅ 單元測試
- ⏳ 與 Prediction Engine 整合（待實作）
- ⏳ TopN API 整合（待實作）
- ⏳ Final Orders API 整合（待實作）

---

**完成日期**: 2025-12-09  
**實作者**: Cursor AI Editor

