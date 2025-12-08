# J-GOD Doctrine Knowledge Integration v1

## 📋 文件目的

本文件說明如何將 Doctrine 知識庫整合到現有的 KnowledgeBrain 系統中。

**重點**：本整合**不修改任何 RL / Policy / War Room / Backtest 相關邏輯**，只強化「知識查詢與解讀」這一層。

---

## 🎯 整合目標

讓 KnowledgeBrain 同時支援載入與查詢：

1. **原本的一般知識庫**：`knowledge_base/jgod_knowledge_v1.jsonl`
2. **新的 Doctrine 知識庫**：`knowledge_base/jgod_doctrine_knowledge_v1.jsonl`

---

## 📦 實作位置

### 核心模組

- **檔案位置**：`jgod/knowledge/knowledge_brain.py`
- **類別**：`KnowledgeBrain`

### 預設知識庫檔案

在 `jgod/knowledge/knowledge_brain.py` 中定義：

```python
DEFAULT_KNOWLEDGE_FILES = [
    "knowledge_base/jgod_knowledge_v1.jsonl",
    "knowledge_base/jgod_doctrine_knowledge_v1.jsonl",
]
```

---

## 🔍 使用方式

### 基本使用（自動載入多個知識庫）

```python
from jgod.knowledge.knowledge_brain import KnowledgeBrain

# 初始化（會自動載入所有預設知識庫）
brain = KnowledgeBrain()
brain.load()

# 查詢所有知識庫
results = brain.search("風控規則")
```

### 只查詢 Doctrine 知識庫

```python
# 方法 1: 使用 search_doctrine() helper
doctrine_results = brain.search_doctrine("風控規則", top_k=10)

# 方法 2: 使用 require_doctrine 參數
doctrine_results = brain.search("風控規則", require_doctrine=True, limit=10)
```

### 查詢所有知識庫（預設行為）

```python
# 不指定 require_doctrine，會搜尋全部知識庫
all_results = brain.search("Sharpe Ratio")
```

---

## 🔧 API 變更說明

### 新增參數：`require_doctrine`

`search()` 方法新增了 `require_doctrine` 參數：

```python
def search(
    query: Optional[str] = None,
    type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20,
    require_doctrine: bool = False  # 新增參數
) -> List[KnowledgeItem]:
```

- `require_doctrine=False`（預設）：搜尋所有知識庫
- `require_doctrine=True`：只搜尋標籤包含 `"DOCTRINE"` 的項目

### 新增方法：`search_doctrine()`

便利函式，等同於 `search(require_doctrine=True)`：

```python
def search_doctrine(query: str, top_k: int = 10) -> List[KnowledgeItem]:
    """Search only in Doctrine knowledge base"""
    return self.search(query=query, limit=top_k, require_doctrine=True)
```

---

## 📊 載入機制

### 多檔案載入

KnowledgeBrain 現在支援從多個 JSONL 檔案載入：

1. **迭代所有檔案路徑**（定義在 `DEFAULT_KNOWLEDGE_FILES` 或自訂 `path`）
2. **合併所有 entries** 到單一的 in-memory 索引
3. **保留所有欄位**：`tags`、`structured` 等欄位完整保留
4. **ID 去重**：如果多個檔案有相同 ID，後載入的會覆蓋先載入的

### 向後相容

- **單一檔案模式**：如果只提供單一 `path`（字串或 Path），行為與之前相同
- **預設行為**：如果不提供 `path`，自動載入所有預設知識庫檔案

---

## 🏷️ Doctrine 標籤識別

Doctrine 知識庫的 entries 會在 `tags` 欄位中包含 `"DOCTRINE"` 標籤：

```json
{
  "id": "doctrine_book_07_...",
  "tags": ["DOCTRINE", "CONCEPT", "RULE", "RISK_RULE"],
  ...
}
```

當 `require_doctrine=True` 時，只會搜尋 `tags` 中包含 `"DOCTRINE"`（大小寫不敏感）的項目。

---

## 🔄 與其他模組的關係

### 不受影響的模組

以下模組**完全不受影響**，繼續使用原有的 KnowledgeBrain API：

- ✅ **RL Engine** (`jgod/rl/`)
- ✅ **Policy Service** (`jgod/policy/`)
- ✅ **War Room** (`jgod/council_chamber/`)
- ✅ **Backtest Engine** (`jgod/backtest/`, `jgod/path_a/`)
- ✅ **Execution Engine** (`jgod/execution/`)

### 自動受益的模組

所有使用 `KnowledgeBrain` 的模組會**自動**獲得 Doctrine 知識庫的查詢能力，例如：

- `jgod/council_chamber/knowledge_gateway.py`：會自動載入並可使用 Doctrine 知識
- 任何呼叫 `KnowledgeBrain().search()` 的程式碼：可選擇性使用 `require_doctrine=True`

---

## 📝 範例

### 範例 1：查詢所有風險相關規則

```python
from jgod.knowledge.knowledge_brain import KnowledgeBrain

brain = KnowledgeBrain()
brain.load()

# 搜尋所有知識庫中的風險規則
all_risk_rules = brain.search(query="風險", type="RULE", tags=["risk"])
```

### 範例 2：只查詢 Doctrine 知識庫中的風控規則

```python
# 只搜尋 Doctrine 知識庫
doctrine_risk_rules = brain.search_doctrine("風控", top_k=10)

# 或使用完整 API
doctrine_risk_rules = brain.search(
    query="風控",
    type="RULE",
    require_doctrine=True,
    limit=10
)
```

### 範例 3：比較一般知識庫與 Doctrine 知識庫

```python
# 一般知識庫的結果
general_results = brain.search("Sharpe Ratio", require_doctrine=False)

# Doctrine 知識庫的結果
doctrine_results = brain.search("Sharpe Ratio", require_doctrine=True)

print(f"一般知識庫: {len(general_results)} 筆")
print(f"Doctrine 知識庫: {len(doctrine_results)} 筆")
```

---

## ⚠️ 重要限制

### 不修改的模組

- ❌ **不修改** RL Engine
- ❌ **不修改** Policy Service  
- ❌ **不修改** War Room
- ❌ **不修改** Backtest / Path A Engine
- ❌ **不修改** Execution Engine

### 只強化知識層

- ✅ **只修改** `jgod/knowledge/knowledge_brain.py`
- ✅ **只新增** Doctrine 過濾功能
- ✅ **保持** 原有 API 向後相容

---

## 🔄 版本歷史

- **v1.0** (2025-01-XX): 初始整合版本
  - 支援多檔案知識庫載入
  - 新增 `require_doctrine` 參數
  - 新增 `search_doctrine()` helper 方法

---

## 📚 相關文件

- [J-GOD Doctrine Review Loop v1 規格文件](./JGOD_DOCTRINE_REVIEW_LOOP_V1.md)
- [J-GOD Doctrine Knowledge Sync v1 規格文件](./JGOD_DOCTRINE_KNOWLEDGE_SYNC_V1.md)
- [J-GOD Doctrine Service v1 規格文件](./JGOD_DOCTRINE_SERVICE_V1_SPEC.md)
- [J-GOD 14 本聖經 Doctrine Mapping Report v1](./JGOD_DOCTRINE_MAPPING_V1.md)

---

**備註**：本整合只強化知識查詢層，不修改任何其他引擎或服務。Doctrine 知識庫透過統一的 `KnowledgeBrain` API 提供查詢能力。

