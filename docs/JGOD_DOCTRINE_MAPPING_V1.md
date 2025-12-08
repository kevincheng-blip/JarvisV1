# J-GOD 14 本聖經 Doctrine Mapping Report v1

## 📋 文件目的

本文件盤點 J-GOD 系統中所有「聖經相關」檔案（structured_books），追蹤它們在專案中的使用情況，並識別哪些已經實際接入系統，哪些仍為純文字文件。

**注意**：本報告僅為盤點與說明，不涉及任何程式碼修改。

---

## 📚 Step 1: 14 本核心聖經索引表

### 核心聖經檔案清單（ENHANCED 版為代表）

| book_id | filename | title_or_heading | version_type | main_theme | 備註 |
|---------|----------|-------------------|--------------|------------|------|
| book_01 | `structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_ENHANCED.md` | J-GOD 股市聖經系統1 | ENHANCED | 系統哲學 | 核心系統設計 |
| book_02 | `structured_books/股神腦系統具體化設計_AI知識庫版_v1_ENHANCED.md` | 股神腦系統具體化設計 | ENHANCED | 系統哲學 | ~8788 行，核心大腦設計 |
| book_03 | `structured_books/股市大自然萬物修復法則_AI知識庫版_v1_ENHANCED.md` | 股市大自然萬物修復法則 | ENHANCED | 系統哲學 | 萬物修復法則 |
| book_04 | `structured_books/股市聖經二_AI知識庫版_v1_ENHANCED.md` | 股市聖經二 | ENHANCED | 系統哲學 | 聖經系列第二本 |
| book_05 | `structured_books/股市聖經三_AI知識庫版_v1_ENHANCED.md` | 股市聖經三 | ENHANCED | 系統哲學 | 聖經系列第三本 |
| book_06 | `structured_books/股市聖經四_AI知識庫版_v1_ENHANCED.md` | 股市聖經四 | ENHANCED | 系統哲學 | 聖經系列第四本 |
| book_07 | `structured_books/JGOD_STOCK_TRADING_BIBLE_v1_AI知識庫版_v1_ENHANCED.md` | J-GOD 股票交易聖經 v1.0 | ENHANCED | 風控總綱 | 交易聖經 |
| book_08 | `structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_ENHANCED.md` | 雙引擎與自主演化閉環 | ENHANCED | RL & Reward | 演化閉環設計 |
| book_09 | `structured_books/Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_ENHANCED.md` | Path A 歷史回測撈取資料＋分析 | ENHANCED | 回測與驗證 | Path A 回測規範 |
| book_10 | `structured_books/滾動式分析_AI知識庫版_v1_ENHANCED.md` | 滾動式分析 | ENHANCED | 回測與驗證 | Walk-Forward 分析 |
| book_11 | `structured_books/J-GOD 邏輯系統補充_AI知識庫版_v1_ENHANCED.md` | J-GOD 邏輯系統補充 | ENHANCED | 錯誤學習 | 邏輯系統補充 |
| book_12 | `structured_books/邏輯版操作說明書_AI知識庫版_v1_ENHANCED.md` | 邏輯版操作說明書 | ENHANCED | 錯誤學習 | 操作說明 |
| book_13 | `structured_books/JGOD_原始開發藍圖_清整強化版_AI知識庫版_v1_ENHANCED.md` | JGOD 原始開發藍圖清整強化版 | ENHANCED | 系統哲學 | 原始藍圖 |
| book_14 | `structured_books/J-GOD_Book_Complete_v1_AI知識庫版_v1_ENHANCED.md` | J-GOD Book Complete v1 | ENHANCED | 系統哲學 | 完整版彙整 |

**註**：
- 以上為核心 14 本聖經，每本都有 CORRECTED / ENHANCED / STRUCTURED 三個版本
- 本表以 **ENHANCED 版**作為代表（通常包含最完整的程式化說明與白話註解）
- 實際檔案總數：約 44 個檔案（14 本 × 3 版本 + 其他輔助檔案）

### 版本類型說明

- **ENHANCED**: 增強版，包含額外的結構化標記與優化
- **STRUCTURED**: 結構化版本，已整理為標準格式
- **CORRECTED**: 修正版，已校對與修正
- **RAW**: 原始版本，未經處理
- **MIXED**: 混合版本，包含多種處理狀態

---

## 🔗 Step 2: Book → 模組對應表

### 實際使用情況

| book_id | used_by_module | file_path | usage_type | 備註 |
|---------|----------------|------------|------------|------|
| book_01 | `jgod/knowledge/knowledge_brain.py` | `jgod/knowledge/knowledge_brain.py` | 當成知識來源（間接） | 透過 knowledge_base/jgod_knowledge_v1.jsonl 間接使用 |
| book_01 | `jgod/council_chamber/knowledge_gateway.py` | `jgod/council_chamber/knowledge_gateway.py` | 當成知識來源（間接） | 透過 KnowledgeBrain 查詢知識 |
| book_01 | `jgod/council_chamber/war_room.py` | `jgod/council_chamber/war_room.py` | 只當說明文件 | 註解中提及「未來實作需參考」 |
| book_01 | `jgod/backtest/backtest_engine.py` | `jgod/backtest/backtest_engine.py` | 只當說明文件 | 註解中提及「未來實作需參考」 |
| book_01 | `jgod/risk/risk_engine.py` | `jgod/risk/risk_engine.py` | 只當說明文件 | 註解中提及「未來實作需參考」 |
| book_01 | `jgod/signal/signal_engine.py` | `jgod/signal/signal_engine.py` | 只當說明文件 | 註解中提及「未來實作需參考」 |
| book_02 | `jgod/alpha_engine/alpha_engine.py` | `jgod/alpha_engine/alpha_engine.py` | 只當說明文件 | 註解中提及「Based on」 |
| book_02 | `jgod/alpha_engine/flow_factor.py` | `jgod/alpha_engine/flow_factor.py` | 只當說明文件 | 註解中提及「Based on」 |
| book_02 | `jgod/factor/factor_engine.py` | `jgod/factor/factor_engine.py` | 只當說明文件 | 註解中提及「未來實作需參考」 |
| book_03 | `jgod/alpha_engine/reversion_factor.py` | `jgod/alpha_engine/reversion_factor.py` | 只當說明文件 | 註解中提及「Based on」 |
| book_08 | `jgod/rl/rl_engine.py` | `jgod/rl/rl_engine.py` | 只當說明文件 | 註解中提及「未來實作需參考」 |
| book_08 | `jgod/policy/policy_reward_adapter_v1.py` | `jgod/policy/policy_reward_adapter_v1.py` | 當成規則來源（概念） | Policy Reward Adapter 可能參考 RL 設計 |
| book_09 | `jgod/model/path_a_engine.py` | `jgod/model/path_a_engine.py` | 只當說明文件 | 註解中提及「未來實作需參考」 |
| book_09 | `jgod/alpha_engine/micro_momentum_factor.py` | `jgod/alpha_engine/micro_momentum_factor.py` | 只當說明文件 | 註解中提及「Based on」 |
| book_10 | `jgod/walkforward/walkforward_engine.py` | `jgod/walkforward/walkforward_engine.py` | 只當說明文件 | 註解中提及「未來實作需參考」 |
| book_11 | `jgod/learning/error_learning_engine.py` | `jgod/learning/error_learning_engine.py` | 當成知識來源（間接） | 使用 knowledge_base/jgod_knowledge_drafts.jsonl |
| book_11 | `jgod/knowledge/extractors/extract_from_corrected_md.py` | `jgod/knowledge/extractors/extract_from_corrected_md.py` | 當成知識來源（直接） | 直接讀取 structured_books/*_CORRECTED.md 檔案 |
| book_04 | - | - | **not_wired_yet** | 股市聖經二（系統哲學） |
| book_05 | - | - | **not_wired_yet** | 股市聖經三（系統哲學） |
| book_06 | - | - | **not_wired_yet** | 股市聖經四（系統哲學） |
| book_07 | - | - | **not_wired_yet** | J-GOD 股票交易聖經（風控總綱） |
| book_12 | - | - | **not_wired_yet** | 邏輯版操作說明書（錯誤學習） |
| book_13 | - | - | **not_wired_yet** | JGOD 原始開發藍圖（系統哲學） |
| book_14 | - | - | **not_wired_yet** | J-GOD Book Complete（系統哲學） |

### Usage Type 說明

- **當成知識來源（部分）**: 程式碼中有明確的檔案讀取或引用，但可能只使用部分內容
- **當成規則來源（概念）**: 程式邏輯可能受到書本概念影響，但沒有直接讀取檔案
- **當成 prompt template**: 書本內容被用作 AI prompt 的模板
- **只當說明文件**: 僅作為開發參考，未實際接入系統
- **not_wired_yet**: 目前完全沒有被任何程式引用

---

## 📊 Step 3: 總結分析

### 已接入系統的聖經（部分接入）

1. **book_01 (J-GOD 股市聖經系統1)**
   - 使用模組：
     - `jgod/knowledge/knowledge_brain.py`（間接，透過 JSONL 知識庫）
     - `jgod/council_chamber/knowledge_gateway.py`（間接，透過 KnowledgeBrain）
   - 接入程度：**間接接入**，內容已提取到 `knowledge_base/jgod_knowledge_v1.jsonl`

2. **book_11 (J-GOD 邏輯系統補充)**
   - 使用模組：
     - `jgod/knowledge/extractors/extract_from_corrected_md.py`（**直接讀取** structured_books 檔案）
     - `jgod/learning/error_learning_engine.py`（使用提取後的知識庫）
   - 接入程度：**直接接入**，有專門的 extractor 讀取 CORRECTED 版本檔案

### 概念層面影響但未正式接線的聖經

以下聖經在程式碼註解中被提及，但**沒有直接讀取檔案**：

1. **book_02 (股神腦系統具體化設計)**: 被 `alpha_engine`、`flow_factor`、`factor_engine` 提及
2. **book_03 (股市大自然萬物修復法則)**: 被 `reversion_factor` 提及
3. **book_08 (雙引擎與自主演化閉環)**: 被 `rl_engine` 提及
4. **book_09 (Path A 歷史回測)**: 被 `path_a_engine`、`micro_momentum_factor` 提及
5. **book_10 (滾動式分析)**: 被 `walkforward_engine` 提及

### 尚未接入系統的聖經

1. **book_04 (股市聖經二)**: 系統哲學，純文字文件
2. **book_05 (股市聖經三)**: 系統哲學，純文字文件
3. **book_06 (股市聖經四)**: 系統哲學，純文字文件
4. **book_07 (J-GOD 股票交易聖經)**: 風控總綱，純文字文件
5. **book_12 (邏輯版操作說明書)**: 錯誤學習，純文字文件
6. **book_13 (JGOD 原始開發藍圖)**: 系統哲學，純文字文件
7. **book_14 (J-GOD Book Complete)**: 系統哲學，純文字文件

### 關鍵發現

#### ✅ 已有實際接線的模組

1. **Knowledge Brain** (`jgod/knowledge/knowledge_brain.py`)
   - **實際讀取**：`knowledge_base/jgod_knowledge_v1.jsonl`
   - 提供知識查詢介面（rules, formulas, concepts）
   - **間接使用** structured_books（內容已提取到 JSONL）

2. **Knowledge Extractor** (`jgod/knowledge/extractors/extract_from_corrected_md.py`)
   - **直接讀取**：`structured_books/*_CORRECTED.md` 檔案
   - 從 CORRECTED 版本提取規則、公式、概念
   - 輸出到 JSONL 知識庫

3. **Council Chamber Knowledge Gateway** (`jgod/council_chamber/knowledge_gateway.py`)
   - 使用 `KnowledgeBrain` 提供統一的知識查詢介面
   - 為幕僚會議室提供知識支援
   - **間接使用** structured_books（透過 KnowledgeBrain）

#### ⚠️ 概念層面影響但未正式接線的模組

以下模組在程式碼註解中提及對應聖經，但**沒有直接讀取檔案**：

1. **Alpha Engine** (`jgod/alpha_engine/`)
   - 提及：book_02 (股神腦系統具體化設計)、book_03 (股市大自然萬物修復法則)、book_09 (Path A)
   - 狀態：僅在註解中標註「Based on」或「未來實作需參考」

2. **Factor Engine** (`jgod/factor/`)
   - 提及：book_02 (股神腦系統具體化設計)
   - 狀態：僅在註解中標註「未來實作需參考」

3. **RL Engine** (`jgod/rl/`)
   - 提及：book_08 (雙引擎與自主演化閉環)
   - 狀態：僅在註解中標註「未來實作需參考」

4. **Policy Service** (`jgod/policy/`)
   - 可能參考：book_08 (雙引擎與自主演化閉環) 的概念
   - 狀態：邏輯層面影響，但沒有直接讀取檔案

5. **Walk-Forward Engine** (`jgod/walkforward/`)
   - 提及：book_10 (滾動式分析)
   - 狀態：僅在註解中標註「未來實作需參考」

6. **其他引擎** (risk, signal, backtest, path_a)
   - 提及：book_01 (J-GOD 股市聖經系統1)
   - 狀態：僅在註解中標註「未來實作需參考」

#### 🔍 目前缺少的「Doctrine Service」層

目前系統中**沒有統一的「Doctrine Service」**來：

1. **統一管理所有聖經檔案**
   - 目前 structured_books 只是檔案目錄，沒有統一的管理介面

2. **提供標準化的知識查詢 API**
   - Knowledge Gateway 存在，但可能沒有覆蓋所有聖經
   - 沒有統一的「根據主題查詢聖經內容」的介面

3. **版本管理與更新機制**
   - 沒有追蹤哪個模組使用了哪個版本的哪本聖經
   - 沒有自動化更新機制

4. **知識庫與聖經的對應關係**
   - `knowledge_base/jgod_knowledge_v1.jsonl` 存在，但與 structured_books 的對應關係不明確

---

## 🎯 建議：Doctrine Service 設計概念（預留章節）

### 設計目標

建立一個統一的「Doctrine Service」層，作為所有聖經內容的管理與查詢中心。

### 核心功能（概念）

1. **Doctrine Registry**
   - 註冊所有 structured_books 檔案
   - 維護 book_id → file_path → version_type 的對應表
   - 支援版本追蹤

2. **Doctrine Loader**
   - 統一讀取與解析 structured_books（支援 .md / .txt）
   - 提供結構化查詢介面（例如：根據 book_id + section 查詢內容）
   - 支援快取機制

3. **Doctrine Query API**
   - 提供模組級別的查詢介面（例如：`get_doctrine(book_id="book_06", section="reward_design")`）
   - 支援全文搜尋（根據關鍵字查詢相關聖經段落）
   - 支援主題查詢（例如：查詢所有與「風控」相關的聖經內容）

4. **Doctrine → Module Mapping**
   - 維護「哪個模組使用了哪本聖經」的對應表
   - 支援反向查詢（例如：查詢某本聖經被哪些模組使用）

5. **Integration with Knowledge Base**
   - 與現有的 `knowledge_base/jgod_knowledge_v1.jsonl` 整合
   - 提供統一的知識查詢入口

### 模組結構（概念）

```
jgod/doctrine/
├── __init__.py
├── doctrine_registry.py      # 註冊所有聖經檔案
├── doctrine_loader.py        # 讀取與解析聖經
├── doctrine_query.py          # 查詢 API
├── doctrine_mapper.py         # 模組對應表管理
└── config/
    └── doctrine_mapping.yaml  # 靜態對應表配置
```

### 使用範例（概念）

```python
from jgod.doctrine import DoctrineService

# 初始化
doctrine = DoctrineService()

# 查詢特定聖經內容
content = doctrine.get_doctrine("book_06", section="reward_design")

# 根據主題查詢
risk_content = doctrine.query_by_theme("風控")

# 查詢某本聖經被哪些模組使用
modules = doctrine.get_modules_using("book_05")
```

---

## 📝 附錄：檔案掃描結果

### structured_books 目錄檔案清單

（實際掃描結果會根據專案現況動態更新）

### knowledge_base 目錄檔案清單

- `knowledge_base/jgod_knowledge_v1.jsonl`: JSON Lines 格式的知識庫檔案

### 相關模組檔案清單

- `jgod/knowledge/knowledge_gateway.py`: 知識閘道
- `jgod/knowledge/knowledge_loader.py`: 知識載入器
- `jgod/council_chamber/knowledge_gateway.py`: 幕僚會議室知識閘道
- `jgod/error_engine/error_learning_engine.py`: 錯誤學習引擎
- `jgod/policy/policy_reward_adapter_v1.py`: Policy Reward Adapter

---

## 🔄 版本歷史

- **v1.0** (2025-01-XX): 初始盤點報告

---

**備註**：本文件為盤點報告，不涉及程式碼修改。實際的 Doctrine Service 實作將在後續階段進行。

