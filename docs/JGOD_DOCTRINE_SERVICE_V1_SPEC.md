# J-GOD Doctrine Service v1 規格文件

## 📋 文件目的

本文件說明 J-GOD Doctrine Service v1 的設計與使用方式。Doctrine Service 提供統一的介面來管理與查詢 14 本核心聖經（structured_books）。

**相關文件**：
- [J-GOD 14 本聖經 Doctrine Mapping Report v1](./JGOD_DOCTRINE_MAPPING_V1.md)：盤點所有聖經檔案及其使用情況

---

## 🎯 設計目標

Doctrine Service v1 的目標是建立一個**乾淨的 Service Layer**，作為所有聖經內容的管理與查詢中心：

1. **統一註冊表**：所有 14 本聖經的 metadata 集中管理
2. **統一讀取介面**：標準化的檔案讀取與解析
3. **查詢 API**：提供簡單的 section 查詢功能
4. **不影響現有模組**：v1 不修改任何現有引擎或服務

---

## 📦 模組結構

```
jgod/doctrine/
├── __init__.py                  # 模組匯出
├── doctrine_registry_v1.py      # 註冊表（14 本聖經 metadata）
├── doctrine_loader_v1.py        # 讀取器（檔案讀取與 section 切割）
└── doctrine_query_v1.py         # 查詢器（查詢 API）
```

---

## 📚 Step 1: Doctrine Registry v1

### 功能說明

`DoctrineRegistryV1` 維護所有 14 本聖經的 metadata，包括：
- 書本基本資訊（book_id, title, description, category）
- 所有版本的檔案路徑（STRUCTURED / CORRECTED / ENHANCED）
- 標籤（tags）

### 資料結構

```python
@dataclass
class DoctrineBookMeta:
    book_id: str          # book_01 ~ book_14
    title: str
    description: str
    category: str         # SYSTEM_PHILOSOPHY / RISK / RL_REWARD / WALKFORWARD / ERROR_LEARNING
    structured_path: Optional[str]
    corrected_path: Optional[str]
    enhanced_path: Optional[str]
    tags: List[str]
```

### 使用範例

```python
from jgod.doctrine import DoctrineRegistryV1, get_book_meta, list_books

# 方法 1: 使用類別
registry = DoctrineRegistryV1()
book = registry.get_book_meta("book_01")
print(f"Title: {book.title}")

# 方法 2: 使用便利函式
book = get_book_meta("book_01")
books = list_books(category="SYSTEM_PHILOSOPHY")
```

### 已註冊的 14 本聖經

| book_id | title | category |
|---------|-------|----------|
| book_01 | J-GOD 股市聖經系統1 | SYSTEM_PHILOSOPHY |
| book_02 | 股神腦系統具體化設計 | SYSTEM_PHILOSOPHY |
| book_03 | 股市大自然萬物修復法則 | SYSTEM_PHILOSOPHY |
| book_04 | 股市聖經二 | SYSTEM_PHILOSOPHY |
| book_05 | 股市聖經三 | SYSTEM_PHILOSOPHY |
| book_06 | 股市聖經四 | SYSTEM_PHILOSOPHY |
| book_07 | J-GOD 股票交易聖經 v1.0 | RISK |
| book_08 | 雙引擎與自主演化閉環 | RL_REWARD |
| book_09 | Path A 歷史回測撈取資料＋分析 | WALKFORWARD |
| book_10 | 滾動式分析 | WALKFORWARD |
| book_11 | J-GOD 邏輯系統補充 | ERROR_LEARNING |
| book_12 | 邏輯版操作說明書 | ERROR_LEARNING |
| book_13 | JGOD 原始開發藍圖清整強化版 | SYSTEM_PHILOSOPHY |
| book_14 | J-GOD Book Complete v1 | SYSTEM_PHILOSOPHY |

---

## 📖 Step 2: Doctrine Loader v1

### 功能說明

`DoctrineLoaderV1` 提供讀取聖經檔案內容的功能：
- 根據 book_id 和 version 讀取檔案
- 將文字內容切割成 sections（基於 Markdown 標題）

### 使用範例

```python
from jgod.doctrine import DoctrineLoaderV1, load_book_text

# 方法 1: 使用類別
loader = DoctrineLoaderV1()
text = loader.load_book_text("book_01", version="ENHANCED")
sections = loader.split_book_into_sections(text, book_id="book_01")

# 方法 2: 使用便利函式
text = load_book_text("book_01", version="ENHANCED")
```

### Section 切割邏輯

v1 實作使用簡單的 Markdown 標題切割：
- 依據 `#`, `##`, `###` 等標題標記
- 每個 section 包含：
  - `section_id`: 唯一識別碼（例如 `book_01_section_001`）
  - `heading`: 標題文字
  - `level`: 標題層級（1=#, 2=##, ...）
  - `content`: 該 section 的完整內容
  - `start_line`, `end_line`: 行號範圍

**注意**：v1 不做 NLP、不做 embedding，只做基本的檔案讀取和標題切割。

---

## 🔍 Step 3: Doctrine Query v1

### 功能說明

`DoctrineQueryV1` 提供查詢 sections 的 API：
- 列出指定書籍的所有 sections
- 取得指定的 section
- 搜尋包含關鍵字的 sections（簡單字串匹配）

### 資料結構

```python
@dataclass
class DoctrineSection:
    book_id: str
    section_id: str
    heading: str
    content: str
    level: int
    start_line: int
    end_line: int
    tags: List[str]
```

### 使用範例

```python
from jgod.doctrine import DoctrineQueryV1

query = DoctrineQueryV1()

# 列出所有 sections
sections = query.list_sections("book_01")

# 取得指定 section
section = query.get_section("book_01", "book_01_section_001")

# 搜尋關鍵字（單一書籍）
results = query.search_sections("book_01", "風控")

# 跨書籍搜尋
results = query.search_across_books("風控", book_ids=["book_07", "book_01"])
```

### 快取機制

`DoctrineQueryV1` 會快取已讀取的 sections，避免重複讀取檔案。可以手動清除快取：

```python
query.clear_cache()  # 清除所有快取
query.clear_cache("book_01")  # 只清除指定書籍的快取
```

---

## 🛠️ Step 4: CLI 工具

### 使用方式

提供簡單的 CLI 工具 `scripts/run_doctrine_inspect_v1.py` 用於測試與瀏覽：

```bash
# 列出所有書籍
PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py list

# 按 category 過濾
PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py list --category SYSTEM_PHILOSOPHY

# 列出指定書籍的所有 sections
PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py sections book_01

# 顯示指定 section 的完整內容
PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py show book_01 book_01_section_001

# 搜尋關鍵字（所有書籍）
PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py search "風控"

# 搜尋關鍵字（指定書籍）
PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py search "風控" --book book_07

# 使用不同版本
PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py sections book_01 --version CORRECTED
```

---

## 🔄 與現有系統的關係

### 不影響現有模組

Doctrine Service v1 **不修改**以下模組：
- `ErrorLearningEngine`
- `RLEngine`
- `PolicyRewardAdapter`
- `Backtest` / `Policy` / `War Room` 任何現有功能

### 未來整合方向

未來其他模組可以選擇性使用 Doctrine Service：

```python
# 例如：ErrorLearningEngine 可以這樣使用
from jgod.doctrine import DoctrineQueryV1

query = DoctrineQueryV1()
error_learning_sections = query.list_sections("book_11")  # J-GOD 邏輯系統補充
```

但目前 v1 階段，這些模組**不會自動使用** Doctrine Service，保持獨立。

---

## 📊 14 本書如何在 Registry 註冊

所有 14 本聖經的 metadata 定義在 `jgod/doctrine/doctrine_registry_v1.py` 中的 `DOCTRINE_REGISTRY_V1` 字典。

### 註冊格式

```python
"book_01": DoctrineBookMeta(
    book_id="book_01",
    title="J-GOD 股市聖經系統1",
    description="核心系統設計與哲學",
    category="SYSTEM_PHILOSOPHY",
    structured_path=_get_full_path("structured_books/..._STRUCTURED.md"),
    corrected_path=_get_full_path("structured_books/..._CORRECTED.md"),
    enhanced_path=_get_full_path("structured_books/..._ENHANCED.md"),
    tags=["system", "core", "philosophy"],
),
```

### 檔案路徑

- 所有路徑使用 `_get_full_path()` 轉換為完整路徑（相對於專案根目錄）
- 如果某個版本不存在，可以設置為 `None`
- Loader 會自動處理檔案不存在的情況（返回空字串並記錄 warning）

---

## 📝 怎麼用 Loader 拿到原文

### 基本用法

```python
from jgod.doctrine import DoctrineLoaderV1

loader = DoctrineLoaderV1()

# 讀取 ENHANCED 版本（預設）
text = loader.load_book_text("book_01")

# 讀取指定版本
text = loader.load_book_text("book_01", version="CORRECTED")

# 讀取並切割成 sections
sections = loader.load_book_sections("book_01", version="ENHANCED")
```

### 錯誤處理

- 如果 `book_id` 不存在：拋出 `ValueError`
- 如果檔案不存在：返回空字串並記錄 `warning`（不會拋出例外）
- 如果讀取失敗：返回空字串並記錄 `error`

---

## 🔎 怎麼用 Query 取得 section

### 基本查詢

```python
from jgod.doctrine import DoctrineQueryV1

query = DoctrineQueryV1()

# 列出所有 sections
sections = query.list_sections("book_01")
for sec in sections:
    print(f"{sec.section_id}: {sec.heading}")

# 取得指定 section
section = query.get_section("book_01", "book_01_section_001")
if section:
    print(section.content)
```

### 搜尋功能

```python
# 在單一書籍中搜尋
results = query.search_sections("book_07", "風險管理")

# 跨書籍搜尋
results = query.search_across_books(
    "風控",
    book_ids=["book_07", "book_01"]
)

# 搜尋所有書籍
results = query.search_across_books("回測")
```

### Section 屬性

每個 `DoctrineSection` 包含：
- `book_id`: 書本 ID
- `section_id`: Section ID（例如 `book_01_section_001`）
- `heading`: 標題文字
- `content`: 完整內容
- `level`: 標題層級（1=#, 2=##, ...）
- `start_line`, `end_line`: 行號範圍
- `tags`: 標籤（v1 目前為空列表）

---

## 🎯 使用場景範例

### 場景 1: 查詢特定主題的內容

```python
from jgod.doctrine import DoctrineQueryV1

query = DoctrineQueryV1()

# 查詢所有與「風控」相關的 sections
risk_sections = query.search_across_books("風控")

# 只查詢 RISK category 的書籍
from jgod.doctrine import list_books
risk_books = [b.book_id for b in list_books(category="RISK")]
risk_sections = query.search_across_books("風控", book_ids=risk_books)
```

### 場景 2: 取得特定書籍的完整內容

```python
from jgod.doctrine import DoctrineLoaderV1

loader = DoctrineLoaderV1()

# 取得完整文字
text = loader.load_book_text("book_08", version="ENHANCED")

# 或取得所有 sections
sections = loader.load_book_sections("book_08")
for sec in sections:
    print(f"{sec['section_id']}: {sec['heading']}")
```

### 場景 3: 瀏覽書籍結構

```python
from jgod.doctrine import DoctrineQueryV1

query = DoctrineQueryV1()

# 列出所有頂層 sections（level=1）
sections = query.list_sections("book_02")
top_level = [s for s in sections if s.level == 1]

for sec in top_level:
    print(f"  {sec.heading}")
```

---

## ⚠️ 限制與注意事項

### v1 限制

1. **不做 NLP / Embedding**：v1 只提供基本的檔案讀取和標題切割，不做語義理解
2. **簡單搜尋**：搜尋功能使用簡單的字串匹配，不支援複雜查詢
3. **不自動整合**：v1 不會自動整合到現有模組，需要手動使用

### 檔案路徑

- 所有路徑相對於專案根目錄
- 如果檔案不存在，Loader 會返回空字串（不會拋出例外）
- 建議使用 `ENHANCED` 版本（通常包含最完整的程式化說明）

### 版本選擇

- **STRUCTURED**: 結構化版本，已整理為標準格式
- **CORRECTED**: 修正版，已校對與修正
- **ENHANCED**: 增強版，包含額外的結構化標記與優化（**推薦使用**）

---

## 🔄 版本歷史

- **v1.0** (2025-01-XX): 初始版本
  - 實作 Registry、Loader、Query
  - 註冊 14 本核心聖經
  - 提供 CLI 工具

---

## 📚 相關文件

- [J-GOD 14 本聖經 Doctrine Mapping Report v1](./JGOD_DOCTRINE_MAPPING_V1.md)：盤點報告
- `jgod/doctrine/__init__.py`：模組 API 文件

---

**備註**：Doctrine Service v1 為純 Service Layer，不修改任何現有模組。未來可以在其他模組中選擇性使用此服務。

