# MASTER_INDEX v1 輸出格式範例

本文檔提供 MASTER_INDEX 的 JSONL 和 Markdown 輸出格式範例，供 Editor 建立檔案時參考。

## 📋 JSONL 格式範例

### 範例 1: RULE（規則）

```json
{
  "id": "RULE_股市聖經系統1_001",
  "type": "RULE",
  "title": "單筆最大虧損 2% 規則",
  "source_file": "J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED",
  "source_phase": "CORRECTED",
  "tags": ["risk", "stop_loss", "position_sizing"],
  "description": "單筆交易最大虧損不得超過帳戶總值的 2%，這是風控的核心規則。當虧損達到 -2% 時，必須立即砍單，不准猶豫。",
  "related_ids": [
    "FORMULA_max_drawdown_001",
    "CONCEPT_risk_management_001"
  ],
  "path": "structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md",
  "version": "v1",
  "line_range": [245, 280],
  "raw_text": "**[RULE]**\n\n單筆最大虧損 2% 規則\n\n行為定義：跌到 -2% 必須砍單，不准猶豫。\n\n適用範圍：所有交易策略\n\n優先級：最高（P10）\n\n[原文]",
  "structured": {
    "if": "單筆交易虧損達到帳戶總值的 -2%",
    "then": "立即砍單，不准猶豫",
    "priority": 10,
    "scope": "risk"
  }
}
```

### 範例 2: FORMULA（公式）

```json
{
  "id": "FORMULA_雙引擎與自主演化閉環_045",
  "type": "FORMULA",
  "title": "Sharpe Ratio（夏普比率）",
  "source_file": "雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED",
  "source_phase": "CORRECTED",
  "tags": ["risk", "performance", "sharpe", "path_a"],
  "description": "Sharpe Ratio 是計算風險調整後報酬率的指標。公式為：(R_p - R_f) / σ_p，其中 R_p 是投資組合報酬率，R_f 是無風險利率，σ_p 是投資組合標準差。",
  "related_ids": [
    "FORMULA_max_drawdown_001",
    "CONCEPT_risk_adjusted_return_001"
  ],
  "path": "structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md",
  "version": "v1",
  "line_range": [1520, 1565],
  "raw_text": "**[FORMULA]**\n\nSharpe Ratio 計算公式：\n\n$$\\text{Sharpe} = \\frac{R_p - R_f}{\\sigma_p}$$\n\n其中：\n- $R_p$：投資組合報酬率\n- $R_f$：無風險利率（通常用 1% 或 0）\n- $\\sigma_p$：投資組合標準差\n\n年化 Sharpe = 日 Sharpe × √252\n\n[外部知識補強]",
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

### 範例 3: CONCEPT（概念）

```json
{
  "id": "CONCEPT_股神腦系統具體化設計_012",
  "type": "CONCEPT",
  "title": "RCNC（即時累積淨成本線）",
  "source_file": "股神腦系統具體化設計_AI知識庫版_v1_CORRECTED",
  "source_phase": "CORRECTED",
  "tags": ["intraday", "capital_flow", "cost", "factor"],
  "description": "RCNC 是基於主力大單與逐筆成交數據計算的成本線。透過 Pandas cumsum 向量化計算，用於偵測主力掃貨頻率與流動性變化。可以計算當日 RCNC 波動率作為長線引擎的輸入因子。",
  "related_ids": [
    "CODE_factor_rcnc_calculation_001",
    "CONCEPT_capital_flow_001"
  ],
  "path": "structured_books/股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md",
  "version": "v1",
  "line_range": [890, 945],
  "raw_text": "**[CONCEPT]**\n\nRCNC（即時累積淨成本線）\n\n定義：基於主力大單（XQ）與逐筆成交數據計算的動態成本線。\n\n計算方法：\n- 使用 Pandas cumsum 向量化計算\n- 基於逐筆成交的買賣價差\n\n應用場景：\n- 偵測主力掃貨頻率\n- 識別流動性變化\n- 作為長線引擎的輸入因子\n\n[原文]",
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

## 📄 Markdown 格式範例

以下是 Markdown 輸出的主要結構：

```markdown
# J-GOD MASTER_INDEX v1

> **說明**：本索引整合了 Phase 1-3 所有結構化知識節點。
> **生成時間**：自動生成

---

## 📊 總覽

- **總節點數**：1,234
- **按類型統計**：
  - RULE: 456 個
  - FORMULA: 234 個
  - CONCEPT: 345 個
  - STRUCTURE: 45 個
  - TABLE: 67 個
  - CODE: 89 個
  - NOTE: 4 個
- **按來源文件統計**：14 個文件
- **標籤數量**：25 個

---

## 🔍 按類型瀏覽

### RULE

- **[RULE_股市聖經系統1_001]** 單筆最大虧損 2% 規則
  - 來源：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED
  - 標籤：risk, stop_loss, position_sizing
  - 相關：FORMULA_max_drawdown_001, CONCEPT_risk_management_001
  - 描述：單筆交易最大虧損不得超過帳戶總值的 2%，這是風控的核心規則。當虧損達到 -2% 時，必須立即砍單，不准猶豫。
  - 路徑：structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md:245-280

- **[RULE_股市聖經系統1_002]** 部位大小限制規則
  - 來源：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED
  - 標籤：risk, position_sizing
  - 相關：RULE_stop_loss_001
  - 描述：單一標的持有部位不得超過總資金的 20%，分散風險...
  - 路徑：structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md:281-310

### FORMULA

- **[FORMULA_雙引擎與自主演化閉環_045]** Sharpe Ratio（夏普比率）
  - 來源：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED
  - 標籤：risk, performance, sharpe, path_a
  - 相關：FORMULA_max_drawdown_001, CONCEPT_risk_adjusted_return_001
  - 描述：Sharpe Ratio 是計算風險調整後報酬率的指標。公式為：(R_p - R_f) / σ_p...
  - 路徑：structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md:1520-1565

- **[FORMULA_雙引擎與自主演化閉環_046]** 最大回撤（Max Drawdown）
  - 來源：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED
  - 標籤：risk, drawdown, performance, path_a
  - 相關：FORMULA_sharpe_ratio_001
  - 描述：最大回撤計算公式：1. 計算累積淨值序列：C_t = ∏(1 + r_i)...
  - 路徑：structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md:1566-1620

### CONCEPT

- **[CONCEPT_股神腦系統具體化設計_012]** RCNC（即時累積淨成本線）
  - 來源：股神腦系統具體化設計_AI知識庫版_v1_CORRECTED
  - 標籤：intraday, capital_flow, cost, factor
  - 相關：CODE_factor_rcnc_calculation_001, CONCEPT_capital_flow_001
  - 描述：RCNC 是基於主力大單與逐筆成交數據計算的成本線。透過 Pandas cumsum 向量化計算...
  - 路徑：structured_books/股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md:890-945

---

## 📁 按來源文件瀏覽

### J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED

- **[RULE_股市聖經系統1_001]** 單筆最大虧損 2% 規則
- **[RULE_股市聖經系統1_002]** 部位大小限制規則
- **[FORMULA_股市聖經系統1_010]** 勝率計算公式
- ...

### 雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED

- **[FORMULA_雙引擎與自主演化閉環_045]** Sharpe Ratio（夏普比率）
- **[FORMULA_雙引擎與自主演化閉環_046]** 最大回撤（Max Drawdown）
- ...

---

## 📑 完整索引列表

### 按 ID 排序

- [CONCEPT_股神腦系統具體化設計_012] RCNC（即時累積淨成本線） (CONCEPT)
- [FORMULA_雙引擎與自主演化閉環_045] Sharpe Ratio（夏普比率） (FORMULA)
- [FORMULA_雙引擎與自主演化閉環_046] 最大回撤（Max Drawdown） (FORMULA)
- [RULE_股市聖經系統1_001] 單筆最大虧損 2% 規則 (RULE)
- [RULE_股市聖經系統1_002] 部位大小限制規則 (RULE)
- ...

---

## 🏷️ 按標籤瀏覽

### risk

- RULE_股市聖經系統1_001 - 單筆最大虧損 2% 規則
- FORMULA_雙引擎與自主演化閉環_045 - Sharpe Ratio
- FORMULA_雙引擎與自主演化閉環_046 - 最大回撤
- ...

### path_a

- FORMULA_雙引擎與自主演化閉環_045 - Sharpe Ratio
- FORMULA_雙引擎與自主演化閉環_046 - 最大回撤
- ...

---

*此索引由 Phase 4: MASTER_INDEX Builder 自動生成*
```

## 📝 說明

1. **JSONL 格式**：每行一個完整的 JSON 物件，便於逐行讀取和處理
2. **Markdown 格式**：人類可讀，包含總覽、分類瀏覽、完整索引等多個視角
3. **關聯關係**：每個節點包含 `related_ids`，方便探索相關知識
4. **路徑信息**：包含 `path` 和 `line_range`，可以直接跳轉到原始文件位置

---

*範例結束*

