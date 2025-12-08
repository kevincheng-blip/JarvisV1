# J-GOD Doctrine Knowledge Sync v1 規格文件

## 📋 文件目的

本文件說明 J-GOD Doctrine Knowledge Sync v1 的設計與使用方式。Knowledge Sync 將已完成的 review JSONL（AI 已填好 ai_* 欄位）轉換成 KnowledgeBrain 格式的知識庫 JSONL。

**重點**：本模組**不直接修改 KnowledgeBrain**，只產生知識庫檔案。未來可以選擇性整合。

---

## 🎯 設計目標

Doctrine Knowledge Sync v1 的目標是：

1. **讀取已完成的 review**：review JSONL 中的 ai_* 欄位已由 Cursor AI 填寫
2. **轉換格式**：將 review record 轉換成 KnowledgeBrain 格式
3. **保留特殊內容**：程式碼和算式分欄保存，不被當普通文字吃掉
4. **產生知識庫檔案**：輸出到 `knowledge_base/jgod_doctrine_knowledge_v1.jsonl`

**不修改任何現有模組**。

---

## 📦 模組結構

```
jgod/doctrine/
└── doctrine_knowledge_sync_v1.py    # 核心實作
```

---

## 🔄 轉換流程

### 輸入：Review JSONL

```json
{
  "book_id": "book_07",
  "book_title": "J-GOD 股票交易聖經 v1.0",
  "section_id": "book_07_section_045",
  "section_title": "單筆最大虧損 2% 規則",
  "raw_text": "...",
  "classification": {
    "has_code": false,
    "has_formula": true,
    "has_checklist": true,
    "knowledge_tags": ["CONCEPT", "RULE", "RISK_RULE", "FORMULA"]
  },
  "extracted_code": [],
  "extracted_formulas": ["MaxLoss = PositionSize * 0.02"],
  "ai_summary": "單筆交易最大虧損不得超過總資金的 2%",
  "ai_core_principles": ["風險控制是交易的第一要務"],
  "ai_risk_rules": ["每筆交易設定停損點", "虧損超過 2% 立即平倉"],
  "ai_error_patterns": [],
  "ai_alpha_ideas": [],
  "created_at": "2025-12-09T12:00:00Z"
}
```

### 輸出：Knowledge Entry

```json
{
  "id": "doctrine_book_07_book-07-section-045_entry_0001",
  "type": "RULE",
  "title": "單筆最大虧損 2% 規則",
  "description": "單筆交易最大虧損不得超過總資金的 2%",
  "tags": ["DOCTRINE", "CONCEPT", "RULE", "RISK_RULE", "FORMULA", "RISK"],
  "source_doc": "doctrine_review_v1:book_07",
  "source_location": "book_07_section_045",
  "raw_text": "...",
  "structured": {
    "book_id": "book_07",
    "book_title": "J-GOD 股票交易聖經 v1.0",
    "section_id": "book_07_section_045",
    "section_title": "單筆最大虧損 2% 規則",
    "rules": [
      "風險控制是交易的第一要務",
      "每筆交易設定停損點",
      "虧損超過 2% 立即平倉"
    ],
    "code_examples": [],
    "formulas": ["MaxLoss = PositionSize * 0.02"],
    "ai_core_principles": ["風險控制是交易的第一要務"],
    "ai_risk_rules": ["每筆交易設定停損點", "虧損超過 2% 立即平倉"],
    "ai_error_patterns": [],
    "ai_alpha_ideas": [],
    "classification": {
      "has_code": false,
      "has_formula": true,
      "has_checklist": true,
      "knowledge_tags": ["CONCEPT", "RULE", "RISK_RULE", "FORMULA"]
    }
  },
  "created_at": "2025-12-09T12:00:00Z"
}
```

---

## 📊 欄位對應說明

### 基本欄位

| Review 欄位 | Knowledge Entry 欄位 | 說明 |
|------------|---------------------|------|
| `book_id` | `structured.book_id` | 書本 ID |
| `book_title` | `structured.book_title` | 書本標題 |
| `section_id` | `structured.section_id` | Section ID |
| `section_title` | `title` | Section 標題作為 entry title |
| `raw_text` | `raw_text` | 原始文字 |
| `created_at` | `created_at` | 建立時間 |

### 分類與標籤

| Review 欄位 | Knowledge Entry 欄位 | 說明 |
|------------|---------------------|------|
| `classification.knowledge_tags` | `tags` | 加上 `DOCTRINE` 前綴 |
| `classification.has_code` | `structured.classification.has_code` | 保留在 structured 中 |
| `classification.has_formula` | `structured.classification.has_formula` | 保留在 structured 中 |

### 特殊內容（分欄保存）

| Review 欄位 | Knowledge Entry 欄位 | 說明 |
|------------|---------------------|------|
| `extracted_code` | `structured.code_examples` | **程式碼分欄保存** |
| `extracted_formulas` | `structured.formulas` | **公式分欄保存** |

### AI 欄位

| Review 欄位 | Knowledge Entry 欄位 | 說明 |
|------------|---------------------|------|
| `ai_summary` | `description` | 作為 entry description |
| `ai_core_principles` | `structured.rules` + `structured.ai_core_principles` | 合併到 rules |
| `ai_risk_rules` | `structured.rules` + `structured.ai_risk_rules` | 合併到 rules |
| `ai_error_patterns` | `structured.ai_error_patterns` | 保留在 structured 中 |
| `ai_alpha_ideas` | `structured.ai_alpha_ideas` | 保留在 structured 中，並加入 `ALPHA` tag |

### Type 判斷

根據 tags 自動判斷 entry type：
- 如果包含 `FORMULA` → `type = "FORMULA"`
- 如果包含 `RULE` 或 `RISK_RULE` → `type = "RULE"`
- 如果包含 `CODE_SNIPPET` → `type = "CODE"`
- 否則 → `type = "CONCEPT"`

---

## 🛠️ 使用方式

### Python API

```python
from jgod.doctrine.doctrine_knowledge_sync_v1 import DoctrineKnowledgeSyncV1

# 初始化
sync = DoctrineKnowledgeSyncV1(
    input_paths=["data/doctrine_reviews/review_2025-12-09.jsonl"],
    output_path="knowledge_base/jgod_doctrine_knowledge_v1.jsonl"
)

# 執行 sync
stats = sync.sync()
```

### CLI 工具

```bash
# 單一檔案
PYTHONPATH=. python scripts/run_doctrine_knowledge_sync_v1.py \
    --inputs data/doctrine_reviews/review_2025-12-09.jsonl

# 多個檔案
PYTHONPATH=. python scripts/run_doctrine_knowledge_sync_v1.py \
    --inputs "review1.jsonl,review2.jsonl,review3.jsonl"

# 自訂輸出路徑
PYTHONPATH=. python scripts/run_doctrine_knowledge_sync_v1.py \
    --inputs review.jsonl \
    --output knowledge_base/custom_doctrine_knowledge.jsonl
```

### 輸出統計

CLI 會輸出以下統計資訊：

```
📊 Knowledge Sync Statistics
================================================================================
Input review records: 5234
Output knowledge entries: 5123
Entries with code: 1234
Entries with formula: 567
Skipped entries: 111

Output file: knowledge_base/jgod_doctrine_knowledge_v1.jsonl
================================================================================
```

---

## 📝 完整工作流程

### Step 1: 執行 Review Loop

```bash
PYTHONPATH=. python scripts/run_doctrine_review_v1.py
```

產生 `data/doctrine_reviews/review_YYYY-MM-DD.jsonl`（skeleton）。

### Step 2: 使用 Cursor AI 填寫 ai_* 欄位

在 Cursor 編輯器中打開 JSONL 檔案，使用 AI 功能填寫所有 `ai_*` 欄位。

### Step 3: 執行 Knowledge Sync

```bash
PYTHONPATH=. python scripts/run_doctrine_knowledge_sync_v1.py \
    --inputs data/doctrine_reviews/review_YYYY-MM-DD.jsonl
```

產生 `knowledge_base/jgod_doctrine_knowledge_v1.jsonl`。

### Step 4: 未來整合（可選）

未來可以讓 `KnowledgeBrain` 同時讀取：
- `knowledge_base/jgod_knowledge_v1.jsonl`（現有知識庫）
- `knowledge_base/jgod_doctrine_knowledge_v1.jsonl`（Doctrine 知識庫）

但目前 v1 階段**不修改 KnowledgeBrain**。

---

## 🔍 特殊內容處理

### 程式碼保存

程式碼會被保存在 `structured.code_examples` 欄位中，**不會被當普通文字吃掉**：

```json
{
  "structured": {
    "code_examples": [
      "def calculate_sharpe(returns, risk_free_rate):\n    ...",
      "for trade in trades:\n    if trade.loss > 0.02:\n        ..."
    ]
  }
}
```

### 公式保存

公式會被保存在 `structured.formulas` 欄位中：

```json
{
  "structured": {
    "formulas": [
      "Sharpe = (Return_p - R_f) / StdDev_p",
      "MaxDD = max(1 - Equity_t / PeakEquity)"
    ]
  }
}
```

---

## ⚠️ 重要限制

1. **不修改 KnowledgeBrain**：本模組只產生檔案，不修改 `KnowledgeBrain` 的程式碼
2. **不呼叫 LLM**：本模組不呼叫任何 AI API
3. **不修改現有模組**：不修改 ErrorLearningEngine、RLEngine 等

---

## 🔄 與其他模組的關係

### 輸入：Review JSONL

由 `DoctrineReviewLoopV1` 產生，經過 Cursor AI 填寫。

### 輸出：Knowledge JSONL

格式與 `knowledge_base/jgod_knowledge_v1.jsonl` 相容，但：
- 目前是**獨立檔案**
- 未來可以選擇性整合到 `KnowledgeBrain`

### 未來整合方向

未來可以在 `KnowledgeBrain` 中支援讀取多個知識庫檔案：

```python
# 未來可能的實作（目前不實作）
brain = KnowledgeBrain()
brain.load()  # 載入 jgod_knowledge_v1.jsonl
brain.load_additional("jgod_doctrine_knowledge_v1.jsonl")  # 載入 Doctrine 知識庫
```

但目前 v1 階段，**只產生檔案，不修改 KnowledgeBrain**。

---

## 📊 範例轉換

### 輸入：Review Record（AI 已填寫）

```json
{
  "book_id": "book_08",
  "section_id": "book_08_section_123",
  "section_title": "Reward 設計原則",
  "ai_summary": "Policy Reward 應基於 Sharpe Ratio 和 Max Drawdown 的加權組合",
  "ai_core_principles": [
    "Reward = w1 * Sharpe + w2 * (1 - MaxDD)",
    "權重應根據回測結果調整"
  ],
  "extracted_formulas": [
    "Reward = 0.7 * Sharpe + 0.3 * (1 - MaxDD)"
  ],
  "classification": {
    "has_formula": true,
    "knowledge_tags": ["CONCEPT", "RULE", "FORMULA"]
  }
}
```

### 輸出：Knowledge Entry

```json
{
  "id": "doctrine_book_08_book-08-section-123_entry_0123",
  "type": "FORMULA",
  "title": "Reward 設計原則",
  "description": "Policy Reward 應基於 Sharpe Ratio 和 Max Drawdown 的加權組合",
  "tags": ["DOCTRINE", "CONCEPT", "RULE", "FORMULA"],
  "source_doc": "doctrine_review_v1:book_08",
  "source_location": "book_08_section_123",
  "structured": {
    "rules": [
      "Reward = w1 * Sharpe + w2 * (1 - MaxDD)",
      "權重應根據回測結果調整"
    ],
    "formulas": [
      "Reward = 0.7 * Sharpe + 0.3 * (1 - MaxDD)"
    ],
    "ai_core_principles": [
      "Reward = w1 * Sharpe + w2 * (1 - MaxDD)",
      "權重應根據回測結果調整"
    ]
  }
}
```

---

## 🔄 版本歷史

- **v1.0** (2025-01-XX): 初始版本
  - 實作 review → knowledge 轉換
  - 保留程式碼和公式分欄
  - 產生知識庫 JSONL

---

## 📚 相關文件

- [J-GOD Doctrine Review Loop v1 規格文件](./JGOD_DOCTRINE_REVIEW_LOOP_V1.md)
- [J-GOD Doctrine Service v1 規格文件](./JGOD_DOCTRINE_SERVICE_V1_SPEC.md)
- [J-GOD 14 本聖經 Doctrine Mapping Report v1](./JGOD_DOCTRINE_MAPPING_V1.md)

---

**備註**：Knowledge Sync v1 只產生知識庫檔案，不修改任何現有模組。未來可以選擇性整合到 KnowledgeBrain。

