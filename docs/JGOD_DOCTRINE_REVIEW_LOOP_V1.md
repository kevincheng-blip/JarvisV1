# J-GOD Doctrine Review Loop v1 規格文件

## 📋 文件目的

本文件說明 J-GOD Doctrine Review Loop v1 的設計與使用方式。Review Loop 從 14 本聖經切 section、分類內容、提取程式碼與算式，產生「AI 可加工」的 review JSONL skeleton。

**重點**：本模組**不呼叫任何 LLM API**，只做結構化處理，AI 解析交給 Cursor 編輯器。

---

## 🎯 設計目標

Doctrine Review Loop v1 的目標是：

1. **切 section**：從 14 本聖經中提取所有 sections
2. **分類內容**：自動偵測程式碼、算式、checklist
3. **提取特殊內容**：分欄保存程式碼區塊和公式行
4. **產生 JSONL skeleton**：留空 ai_* 欄位給 Cursor AI 填寫

**不修改任何現有引擎或服務**。

---

## 📦 模組結構

```
jgod/doctrine_review/
├── __init__.py
└── review_loop_v1.py      # 核心實作
```

---

## 🔍 核心功能

### 1. Section 內容分類

`classify_section_content()` 函式會自動偵測：

#### has_code（程式碼偵測）

- 檢查 code block（```）
- 檢查常見程式語言標記（```python, ```javascript 等）
- 檢查關鍵字：`def`, `class`, `function`, `import`, `from`
- 檢查行首標記：`CODE:`, `程式碼:`

#### has_formula（算式偵測）

- 檢查關鍵字：`FORMULA`, `公式`, `Sharpe`, `VaR`, `MaxDD`
- 檢查數學符號：`∑`, `Σ`, `√`, `^`, `∫`, `∂`, `∇`
- 檢查公式模式：`變數 = 表達式`（包含運算符號）

#### has_checklist（檢查清單偵測）

- 檢查多行 bullet points（`-`, `*`, `•`）
- 檢查關鍵字：`檢查`, `Checklist`, `步驟`, `TODO`

#### knowledge_tags（知識標籤）

自動產生標籤：
- `CONCEPT`：預設標籤
- `RULE`：包含「規則、原則、心法」
- `RISK_RULE`：包含「不要、避免、風險」
- `FORMULA`：如果 has_formula
- `CODE_SNIPPET`：如果 has_code
- `STORY`：包含「故事、案例、例子」

### 2. 程式碼提取

`extract_code_blocks()` 函式：

- 提取所有 ``` 區塊（保留原始格式）
- 提取連續的程式碼行（def/class/import/function 開頭）
- 去重並過濾空字串

### 3. 公式提取

`extract_formula_lines()` 函式：

- 提取包含公式關鍵字的行
- 提取包含數學符號的行
- 提取符合公式模式的行（`變數 = 表達式`）
- 過濾註解行

### 4. Review Record 產生

`build_review_record()` 方法產生以下結構：

```json
{
  "book_id": "book_03",
  "book_title": "...",
  "section_id": "book_03_section_012",
  "section_title": "xxxx",
  "raw_text": "原始 section 全文",
  "classification": {
    "has_code": true,
    "has_formula": true,
    "has_checklist": false,
    "knowledge_tags": ["CONCEPT", "RULE", "FORMULA", "CODE_SNIPPET"]
  },
  "extracted_code": [
    "def example(...): ...",
    "for trade in trades: ..."
  ],
  "extracted_formulas": [
    "Sharpe = (Return_p - R_f) / StdDev_p",
    "MaxDD = max(1 - Equity_t / PeakEquity)"
  ],
  "ai_summary": "",
  "ai_core_principles": [],
  "ai_risk_rules": [],
  "ai_error_patterns": [],
  "ai_alpha_ideas": [],
  "created_at": "2025-12-09T12:00:00Z"
}
```

**重點**：`ai_*` 欄位預設為空，留給 Cursor AI 填寫。

---

## 🛠️ 使用方式

### Python API

```python
from jgod.doctrine_review import DoctrineReviewLoopV1

# 初始化
review_loop = DoctrineReviewLoopV1(output_dir="data/doctrine_reviews")

# 執行完整 review（所有 14 本書）
stats = review_loop.run_full_review()

# 只處理指定書籍
stats = review_loop.run_full_review(book_ids=["book_01", "book_03"])

# 自訂輸出檔名
stats = review_loop.run_full_review(
    book_ids=["book_01"],
    output_filename="custom_review.jsonl"
)
```

### CLI 工具

```bash
# 處理所有 14 本書
PYTHONPATH=. python scripts/run_doctrine_review_v1.py

# 只處理指定書籍
PYTHONPATH=. python scripts/run_doctrine_review_v1.py --books book_01,book_03

# 自訂輸出檔名
PYTHONPATH=. python scripts/run_doctrine_review_v1.py --output data/doctrine_reviews/custom_review.jsonl
```

### 輸出統計

CLI 會輸出以下統計資訊：

```
📊 Review Statistics
================================================================================
Total books processed: 14
Total sections: 5234
Sections with code: 1234
Sections with formula: 567
Sections with checklist: 890
Total code blocks extracted: 2345
Total formula lines extracted: 1234

Output file: data/doctrine_reviews/review_2025-12-09.jsonl
================================================================================
```

---

## 📝 工作流程

### Step 1: 執行 Review Loop

```bash
PYTHONPATH=. python scripts/run_doctrine_review_v1.py
```

這會產生 `data/doctrine_reviews/review_YYYY-MM-DD.jsonl`，包含所有 sections 的 skeleton。

### Step 2: 使用 Cursor AI 填寫 ai_* 欄位

在 Cursor 編輯器中打開 JSONL 檔案，使用 AI 功能填寫：
- `ai_summary`：section 摘要
- `ai_core_principles`：核心原則列表
- `ai_risk_rules`：風險規則列表
- `ai_error_patterns`：錯誤模式列表
- `ai_alpha_ideas`：Alpha 想法列表

### Step 3: 執行 Knowledge Sync

使用 `run_doctrine_knowledge_sync_v1.py` 將已完成的 review 轉換成知識庫格式（見下一份文件）。

---

## ⚠️ 重要限制

1. **不呼叫 LLM**：本模組不呼叫任何 GPT / OpenAI / Claude API
2. **不修改現有模組**：不修改 ErrorLearningEngine、RLEngine、PolicyRewardAdapter 等
3. **只做結構化處理**：分類、提取、產生 skeleton，不做語義理解

---

## 🔄 與其他模組的關係

### 使用 Doctrine Service

Review Loop 使用 `DoctrineQueryV1` 和 `DoctrineRegistryV1` 來：
- 取得所有 sections
- 取得書籍 metadata

### 輸出格式

產生的 JSONL 格式設計為：
- **人類可讀**：可以直接在編輯器中查看和編輯
- **AI 可加工**：Cursor AI 可以理解結構並填寫欄位
- **程式可解析**：Knowledge Sync 可以讀取並轉換

---

## 📊 範例輸出

### 單一 Review Record

```json
{
  "book_id": "book_07",
  "book_title": "J-GOD 股票交易聖經 v1.0",
  "section_id": "book_07_section_045",
  "section_title": "單筆最大虧損 2% 規則",
  "raw_text": "## 單筆最大虧損 2% 規則\n\n...",
  "classification": {
    "has_code": false,
    "has_formula": true,
    "has_checklist": true,
    "knowledge_tags": ["CONCEPT", "RULE", "RISK_RULE", "FORMULA"]
  },
  "extracted_code": [],
  "extracted_formulas": [
    "MaxLoss = PositionSize * 0.02",
    "StopLoss = EntryPrice * (1 - 0.02)"
  ],
  "ai_summary": "",
  "ai_core_principles": [],
  "ai_risk_rules": [],
  "ai_error_patterns": [],
  "ai_alpha_ideas": [],
  "created_at": "2025-12-09T12:00:00Z"
}
```

---

## 🔄 版本歷史

- **v1.0** (2025-01-XX): 初始版本
  - 實作 section 分類
  - 實作 code/formula 提取
  - 產生 review JSONL skeleton

---

## 📚 相關文件

- [J-GOD Doctrine Service v1 規格文件](./JGOD_DOCTRINE_SERVICE_V1_SPEC.md)
- [J-GOD Doctrine Knowledge Sync v1 規格文件](./JGOD_DOCTRINE_KNOWLEDGE_SYNC_V1.md)
- [J-GOD 14 本聖經 Doctrine Mapping Report v1](./JGOD_DOCTRINE_MAPPING_V1.md)

---

**備註**：Review Loop v1 為純結構化處理模組，不呼叫 LLM，不修改任何現有引擎。

