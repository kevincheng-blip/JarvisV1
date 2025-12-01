# J-GOD Knowledge Schema v1

## 1. 基本資料結構

每一條知識（Knowledge Item）用一個 JSON 物件表示，欄位如下：

- `id`: string - 唯一識別碼（建議格式：`{type}_{hash}` 或 `{source_doc}_{line_number}`）
- `type`: string - 知識類型（`TABLE` / `CODE` / `FORMULA` / `RULE` / `CONCEPT` / `STRUCTURE` / `NOTE`）
- `title`: string - 標題或簡短名稱
- `description`: string - 完整描述
- `tags`: string[] - 標籤陣列，用於分類與搜尋
- `source_doc`: string - 來源文件路徑（例如：`structured_books/J-GOD_股市聖經系統1_AI知識庫版_v1_CORRECTED.md`）
- `source_location`: string - 來源文件中的位置（章節、行號或區塊標識）
- `raw_text`: string - 原始文字內容（保留原文以備查閱）

### structured: 結構化資料

根據 `type` 的不同，`structured` 欄位包含不同結構：

#### FORMULA（公式）

```json
{
  "expression": "string - 數學表達式或公式文字",
  "variables": {
    "var_name": "variable description"
  },
  "notes": "string - 公式說明與使用注意事項"
}
```

**範例：**

```json
{
  "id": "formula_sharpe_ratio_001",
  "type": "FORMULA",
  "title": "Sharpe Ratio",
  "description": "計算風險調整後報酬率的指標",
  "tags": ["risk", "performance", "sharpe"],
  "source_doc": "structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md",
  "source_location": "第 2 章：績效指標",
  "raw_text": "Sharpe Ratio = (R_p - R_f) / σ_p",
  "structured": {
    "expression": "Sharpe = (R_p - R_f) / σ_p",
    "variables": {
      "R_p": "投資組合報酬率",
      "R_f": "無風險利率",
      "σ_p": "投資組合標準差"
    },
    "notes": "年化 Sharpe = 日 Sharpe × √252"
  }
}
```

#### RULE（規則）

```json
{
  "if": "string - 條件描述",
  "then": "string - 結果或行動",
  "priority": "integer - 優先級（數字越大優先級越高）",
  "scope": "string - 適用範圍（例如：strategy、risk、entry、exit）"
}
```

**範例：**

```json
{
  "id": "rule_stop_loss_001",
  "type": "RULE",
  "title": "單筆最大虧損 2% 規則",
  "description": "單筆交易最大虧損不得超過帳戶總值的 2%",
  "tags": ["risk", "stop_loss", "position_sizing"],
  "source_doc": "structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md",
  "source_location": "風控引擎章節",
  "raw_text": "單筆最大虧損 2% - 行為定義：跌到 -2% 必須砍單，不准猶豫",
  "structured": {
    "if": "單筆交易虧損達到帳戶總值的 -2%",
    "then": "立即砍單，不准猶豫",
    "priority": 10,
    "scope": "risk"
  }
}
```

#### CONCEPT（概念）

```json
{
  "name": "string - 概念名稱",
  "definition": "string - 定義說明",
  "examples": ["string", "string"] - 範例陣列
}
```

**範例：**

```json
{
  "id": "concept_rcnc_001",
  "type": "CONCEPT",
  "title": "RCNC（即時累積淨成本線）",
  "description": "基於主力大單與逐筆成交數據計算的成本線",
  "tags": ["intraday", "capital_flow", "cost"],
  "source_doc": "structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md",
  "source_location": "盤中當沖預測引擎章節",
  "raw_text": "RCNC 基於主力大單（XQ）與逐筆成交數據，使用 Pandas cumsum 向量化計算",
  "structured": {
    "name": "RCNC",
    "definition": "即時累積淨成本線（Real-time Cumulative Net Cost），透過主力大單與逐筆成交數據計算的動態成本線，用於偵測主力掃貨頻率與流動性變化",
    "examples": [
      "計算當日 RCNC 波動率作為長線引擎的輸入因子",
      "偵測 RCNC 異常波動以識別主力動向"
    ]
  }
}
```

#### STRUCTURE（結構）

```json
{
  "tree": "object - 樹狀結構物件（例如：系統架構、模組層級關係）"
}
```

**範例：**

```json
{
  "id": "structure_jgod_modules_001",
  "type": "STRUCTURE",
  "title": "J-GOD 核心模組架構",
  "description": "J-GOD 系統的模組層級架構圖",
  "tags": ["architecture", "module", "system"],
  "source_doc": "spec/JGOD_Python_Interface_Spec.md",
  "source_location": "一、整體架構說明",
  "raw_text": "J-GOD 系統由 10 大核心模組組成...",
  "structured": {
    "tree": {
      "level_1": {
        "Factor Engine": ["F_C", "F_S", "F_D"],
        "Data Universe Engine": ["market_data", "xq_data"]
      },
      "level_2": {
        "Signal Engine": ["六大武功策略"],
        "Prediction Engine": ["Intraday", "Macro"]
      }
    }
  }
}
```

#### TABLE（表格）

```json
{
  "columns": ["string", "string"] - 欄位名稱陣列,
  "rows": [
    ["string", "string"] - 資料列
  ]
}
```

**範例：**

```json
{
  "id": "table_strategy_list_001",
  "type": "TABLE",
  "title": "六大武功策略列表",
  "description": "J-GOD 核心交易策略清單",
  "tags": ["strategy", "trading", "entry"],
  "source_doc": "structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md",
  "source_location": "六大武功策略章節",
  "raw_text": "主流突破、強勢回檔、主力反轉、逆勢突襲、急攻狙擊、爆量警戒",
  "structured": {
    "columns": ["策略名稱", "進場條件", "出場條件"],
    "rows": [
      ["主流突破", "站上季線、突破壓力、量價同步", "跌破支撐或停損"],
      ["強勢回檔", "拉回至支撐、量縮止穩、出現多方訊號", "跌破支撐或停損"]
    ]
  }
}
```

#### CODE（程式碼）

```json
{
  "language": "string - 程式語言（python、sql、bash 等）",
  "code": "string - 程式碼內容"
}
```

**範例：**

```json
{
  "id": "code_factor_calculation_001",
  "type": "CODE",
  "title": "因子計算範例",
  "description": "計算 F_C 資金流因子的 Python 程式碼範例",
  "tags": ["code", "factor", "python"],
  "source_doc": "structured_books/股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md",
  "source_location": "CapitalFlowEngine 實作範例",
  "raw_text": "使用 Pandas 計算族群資金占比的 residual",
  "structured": {
    "language": "python",
    "code": "def compute_factor(market_data, xq_data):\n    # 計算 SAI (Sector Attack Index)\n    sector_weights = xq_data.groupby('sector')['volume'].sum()\n    historical_mean = sector_weights.mean()\n    residual = (sector_weights - historical_mean) / historical_mean.std()\n    return residual.to_dict()"
  }
}
```

#### NOTE（備註）

```json
{
  "content": "string - 備註內容"
}
```

**範例：**

```json
{
  "id": "note_risk_warning_001",
  "type": "NOTE",
  "title": "風控重要提醒",
  "description": "風控規則的重要性說明",
  "tags": ["risk", "warning", "note"],
  "source_doc": "structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md",
  "source_location": "風控引擎章節",
  "raw_text": "風控紀律遵守率必須 > 95%",
  "structured": {
    "content": "風控規則是最重要的底線，任何策略都不能違反風控規則。系統會自動記錄所有風控違規，並在戰情室中顯示警告。"
  }
}
```

---

## 2. 儲存格式

### 路徑

- **主要知識庫**：`knowledge_base/jgod_knowledge_v1.jsonl`
- **備份/版本**：`knowledge_base/backups/`（可選）

### 格式：JSON Lines

每一行為一個獨立的 JSON 物件，以換行符號分隔。

**優點：**
- 易於增量新增知識
- 流式讀取效率高
- 版本控制友好（一行一個知識項目）

**範例檔案內容：**

```jsonl
{"id":"formula_sharpe_001","type":"FORMULA","title":"Sharpe Ratio",...}
{"id":"rule_stop_loss_001","type":"RULE","title":"單筆最大虧損 2%",...}
{"id":"concept_rcnc_001","type":"CONCEPT","title":"RCNC",...}
```

---

## 3. 使用情境

### 3.1 KnowledgeBrain 查詢介面

KnowledgeBrain 類別提供以下查詢方法：

#### 依類型查詢

- `get_rules(tag=None)` - 取得所有規則（可選標籤過濾）
- `get_formulas(tag=None)` - 取得所有公式（可選標籤過濾）
- `get_concepts(tag=None)` - 取得所有概念（可選標籤過濾）

#### 依 ID 查詢

- `get_by_id(item_id)` - 精確取得特定知識項目

#### 全文搜尋

- `search(query, type=None, tags=None, limit=20)` - 多條件搜尋
  - `query`: 關鍵字（搜尋 title、description、raw_text）
  - `type`: 過濾知識類型
  - `tags`: 過濾標籤（陣列）
  - `limit`: 回傳結果數量上限

#### 概念解釋

- `explain_concept(name)` - 解釋特定概念（比對 structured.name 或 title）

---

## 4. 知識提取來源

### 主要來源文件

1. **structured_books/***_CORRECTED.md** - 結構化知識庫文件（14 本）
2. **spec/JGOD_Python_Interface_Spec.md** - 系統架構規格
3. **jgod/** - 程式碼註解與文件字串（未來可提取）

### 提取重點

- **公式**：從 CORRECTED.md 中提取所有數學公式、統計公式
- **規則**：從 CORRECTED.md 中提取 Rules_Entry、Rules_Exit、風控規則
- **概念**：從 CORRECTED.md 中提取重要概念定義（包含 [外部知識補強] 標記的內容）
- **結構**：從 Interface Spec 中提取系統架構樹
- **程式碼範例**：從 CORRECTED.md 中的 [程式化說明] 區塊提取

---

## 5. 版本控制

- **Schema 版本**：v1
- **知識庫版本**：在檔案名稱中標示（例如：`jgod_knowledge_v1.jsonl`）
- **未來擴充**：v2 可能新增欄位（例如：`created_at`、`updated_at`、`confidence_score`），但需保持向後相容

---

## 6. 範例：完整 Knowledge Item

```json
{
  "id": "formula_max_drawdown_001",
  "type": "FORMULA",
  "title": "最大回撤（Max Drawdown）",
  "description": "計算投資組合從歷史最高點的最大跌幅",
  "tags": ["risk", "drawdown", "performance", "path_a"],
  "source_doc": "structured_books/Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md",
  "source_location": "第 3 章：績效指標計算",
  "raw_text": "最大回撤計算公式：\n1. 計算累積淨值序列：C_t = ∏(1 + r_i)\n2. 計算歷史最高點：P_t = max(C_1, ..., C_t)\n3. 計算回撤：D_t = (P_t - C_t) / P_t\n4. 最大回撤 = max(D_1, ..., D_T)",
  "structured": {
    "expression": "Max Drawdown = max((P_t - C_t) / P_t)",
    "variables": {
      "C_t": "時刻 t 的累積淨值",
      "P_t": "時刻 t 之前的歷史最高淨值",
      "D_t": "時刻 t 的回撤幅度"
    },
    "notes": "最大回撤是風險管理的重要指標，用於評估策略在最壞情況下的損失幅度"
  }
}
```

---

**End of Schema Specification**

