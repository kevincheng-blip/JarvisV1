# Phase 4: MASTER_INDEX v1 標準文件

## 📋 概述

Phase 4 的目標是將 Phase 1-3（STRUCTURED → ENHANCED → CORRECTED）所有已結構化知識節點整合成一份 **J-GOD MASTER_INDEX_v1（主索引）**。

## 🎯 目標

1. **整合所有知識節點**：從 14 本 CORRECTED 文件中提取所有知識節點
2. **建立統一索引**：提供完整的索引結構，便於查詢和導航
3. **支援多種格式**：同時產生 JSONL（機器可讀）和 Markdown（人類可讀）
4. **建立關聯關係**：標記知識節點之間的關聯性

## 📊 MASTER_INDEX_v1 Schema

### 核心欄位定義

```python
{
    "id": str,                    # 唯一識別碼（格式：{type}_{source_file}_{seq}）
    "type": str,                  # 知識類型：RULE / FORMULA / CONCEPT / STRUCTURE / TABLE / CODE / NOTE
    "title": str,                 # 標題或簡短名稱
    "source_file": str,           # 原始 MD 文件名稱（不含路徑）
    "source_phase": str,          # 來源階段：STRUCTURED / ENHANCED / CORRECTED
    "tags": List[str],            # 標籤列表（來自節點 metadata）
    "description": str,           # 自動摘要（從 raw_text 提取前 200 字）
    "related_ids": List[str],     # 相互關聯的節點 ID 列表
    "path": str,                  # 檔案位置（相對路徑，便於跳轉）
    "version": str,               # 版本（預設 "v1"）
    "line_range": Tuple[int, int], # 原始文件中的行號範圍（可選）
    "raw_text": str,              # 原始文字內容（完整）
    "structured": dict            # 結構化資料（依 type 不同而有不同結構）
}
```

### 欄位詳細說明

#### 1. id（唯一識別碼）

**格式**：`{type}_{source_file_basename}_{sequence}`

**範例**：
- `RULE_股市聖經系統1_001`
- `FORMULA_雙引擎與自主演化閉環_045`
- `CONCEPT_股神腦系統具體化設計_012`

**生成規則**：
- 從 CORRECTED 文件中提取時，依出現順序編號
- 確保全域唯一（檢查重複）

#### 2. type（知識類型）

**允許值**：
- `RULE`：交易規則、風控規則、進出場規則
- `FORMULA`：數學公式、統計公式、指標計算
- `CONCEPT`：概念定義、術語解釋
- `STRUCTURE`：系統架構、模組結構
- `TABLE`：表格資料、對照表
- `CODE`：程式碼範例、實作片段
- `NOTE`：備註、說明、提醒

#### 3. source_file（原始文件）

**格式**：文件名稱（不含路徑和副檔名）

**範例**：
- `J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED`
- `雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED`

#### 4. source_phase（來源階段）

**允許值**：
- `STRUCTURED`：來自 STRUCTURED 版本
- `ENHANCED`：來自 ENHANCED 版本（新增內容）
- `CORRECTED`：來自 CORRECTED 版本（最終版本，優先使用）

**規則**：
- 優先從 CORRECTED 文件提取
- 如果 CORRECTED 中沒有，才從 ENHANCED 或 STRUCTURED 提取

#### 5. tags（標籤列表）

**來源**：
- 從原始文件的 metadata 區塊提取
- 從內容中自動識別（例如：包含「風控」→ 標記 `risk`）

**標準標籤**：
- `risk`：風險相關
- `strategy`：策略相關
- `entry`：進場規則
- `exit`：出場規則
- `performance`：績效指標
- `path_a`：Path A 回測相關
- `alpha`：Alpha Engine 相關
- `optimizer`：Optimizer 相關
- `knowledge`：知識庫相關

#### 6. description（自動摘要）

**生成規則**：
- 從 `raw_text` 提取前 200 字元
- 如果 `raw_text` 太短，直接使用
- 自動去除 Markdown 格式符號

#### 7. related_ids（關聯節點）

**識別規則**：
- 檢查內容中提到的其他概念、規則、公式
- 使用模糊匹配找出可能的關聯
- 手動驗證（Phase 4 v1 先自動生成，後續可手動調整）

**範例**：
```json
{
    "id": "RULE_stop_loss_001",
    "related_ids": ["FORMULA_max_drawdown_001", "CONCEPT_risk_management_001"]
}
```

#### 8. path（檔案位置）

**格式**：相對路徑（從專案根目錄）

**範例**：
- `structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md`
- `structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md`

#### 9. version（版本）

**預設值**：`"v1"`

**說明**：未來如有更新，可升級為 v2、v3 等

#### 10. structured（結構化資料）

**結構依 type 而定**：

- **RULE**：
  ```json
  {
      "if": "條件描述",
      "then": "結果或行動",
      "priority": 10,
      "scope": "risk"
  }
  ```

- **FORMULA**：
  ```json
  {
      "expression": "數學表達式",
      "variables": {"var": "說明"},
      "notes": "注意事項"
  }
  ```

- **CONCEPT**：
  ```json
  {
      "name": "概念名稱",
      "definition": "定義說明",
      "examples": ["範例1", "範例2"]
  }
  ```

- 其他類型依 `JGOD_Knowledge_Schema_v1.md` 定義

## 🔧 處理流程

### 步驟 1：掃描 CORRECTED 文件

1. 掃描 `structured_books/` 目錄
2. 找出所有 `*_CORRECTED.md` 文件
3. 驗證文件格式和完整性

### 步驟 2：提取知識節點

使用現有的 extractors 或建立新的 extractor：

1. **識別節點類型**：從 Markdown 標記中識別（例如：`**[RULE]**`、`**[FORMULA]**`）
2. **提取 metadata**：tags、標題、描述
3. **提取 raw_text**：完整原始內容
4. **解析 structured**：根據類型解析結構化資料

### 步驟 3：建立索引字典

1. 建立全域字典：`master_index: Dict[str, MasterIndexItem]`
2. 為每個節點分配唯一 ID
3. 建立反向索引：`by_type`、`by_source_file`、`by_tags`

### 步驟 4：建立關聯關係

1. 分析內容中的關鍵字
2. 匹配已知的知識節點 ID
3. 建立 `related_ids` 列表

### 步驟 5：產生輸出

1. **JSONL 格式**：`knowledge_base/jgod_master_index_v1.jsonl`
2. **Markdown 格式**：`docs/J-GOD_MASTER_INDEX_v1.md`

### 步驟 6：安全防呆

1. **檢查重複 ID**：如果 ID 重複，自動添加後綴 `_dup1`、`_dup2`
2. **檢查必填欄位**：確保所有必填欄位都有值
3. **檢查空節點**：過濾掉空內容或無效的節點
4. **驗證格式**：確保 JSON 格式正確

## 📁 輸出檔案

### 1. JSONL 格式

**路徑**：`knowledge_base/jgod_master_index_v1.jsonl`

**格式**：每行一個 JSON 物件

**範例**：
```jsonl
{"id":"RULE_股市聖經系統1_001","type":"RULE","title":"單筆最大虧損 2% 規則",...}
{"id":"FORMULA_雙引擎與自主演化閉環_045","type":"FORMULA","title":"Sharpe Ratio",...}
```

### 2. Markdown 格式

**路徑**：`docs/J-GOD_MASTER_INDEX_v1.md`

**結構**：
```markdown
# J-GOD MASTER_INDEX v1

## 總覽
- 總節點數：X
- 按類型分類：...
- 按來源文件分類：...

## 按類型瀏覽

### RULE（規則）
- [RULE_001] 單筆最大虧損 2% 規則
  - 來源：股市聖經系統1
  - 標籤：risk, stop_loss
  - 相關：FORMULA_max_drawdown_001

### FORMULA（公式）
...

## 按來源文件瀏覽

### 股市聖經系統1
...

## 索引

### 按 ID 排序
- [RULE_股市聖經系統1_001] ...
- [FORMULA_雙引擎與自主演化閉環_045] ...
```

## 🔍 節點提取規則

### 識別節點類型

從 CORRECTED 文件中識別節點的方法：

1. **標記識別**：
   - `**[RULE]**` → RULE 類型
   - `**[FORMULA]**` → FORMULA 類型
   - `**[CONCEPT]**` → CONCEPT 類型
   - `**[STRUCTURE]**` → STRUCTURE 類型
   - `**[TABLE]**` → TABLE 類型
   - `**[CODE]**` → CODE 類型
   - `**[NOTE]**` → NOTE 類型

2. **內容模式識別**：
   - 包含數學公式（`$$...$$` 或 `$...$`）→ FORMULA
   - 包含程式碼區塊（` ```python`）→ CODE
   - 包含表格（Markdown table）→ TABLE
   - 包含「如果...則...」邏輯 → RULE

### 提取 metadata

1. **tags**：從內容中提取或自動標記
2. **title**：從標題或第一句話提取
3. **description**：從前 200 字元提取

### 提取 structured

根據類型使用不同的解析器：
- FORMULA：提取數學表達式和變數說明
- RULE：提取 if-then 邏輯
- CONCEPT：提取定義和範例
- 等等

## 📈 統計資訊

MASTER_INDEX 應包含以下統計：

- 總節點數
- 按類型統計（RULE: X, FORMULA: Y, ...）
- 按來源文件統計
- 按標籤統計
- 平均關聯度（每個節點平均關聯幾個其他節點）

## 🔄 版本管理

- **Schema 版本**：v1
- **索引版本**：在檔案名稱中標示（`jgod_master_index_v1.jsonl`）
- **更新頻率**：每次 Phase 1-3 有更新時，重新生成 MASTER_INDEX

## 🚀 使用情境

1. **快速查詢**：根據 ID 快速找到知識節點
2. **關聯探索**：透過 `related_ids` 探索相關知識
3. **分類瀏覽**：按類型、來源、標籤瀏覽
4. **導航跳轉**：透過 `path` 直接跳轉到原始文件位置

---

**End of Phase 4: MASTER_INDEX Standard**

