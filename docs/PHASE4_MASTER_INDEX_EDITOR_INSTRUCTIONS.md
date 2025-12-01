# Phase 4: MASTER_INDEX Editor 指令包

本文檔包含建立 Phase 4: MASTER_INDEX 系統所需的所有 Editor 指令，可直接複製貼上到 Cursor Editor 使用。

## 📋 處理步驟總覽

1. ✅ **建立標準文件** - `docs/PHASE4_MASTER_INDEX_STANDARD_v1.md`
2. ✅ **建立 Builder 程式** - `structured_books/build_master_index.py`
3. ✅ **建立範例文件** - `structured_books/MASTER_INDEX_EXAMPLES.md`
4. 🔄 **執行 Builder 產生索引** - 執行 `build_master_index.py`
5. 🔄 **驗證輸出結果** - 檢查 JSONL 和 Markdown 輸出

---

## 🎯 Editor 指令 1：驗證現有檔案

### 檢查已建立的檔案

```bash
# 檢查標準文件是否存在
ls -lh docs/PHASE4_MASTER_INDEX_STANDARD_v1.md

# 檢查 Builder 程式是否存在
ls -lh structured_books/build_master_index.py

# 檢查範例文件是否存在
ls -lh structured_books/MASTER_INDEX_EXAMPLES.md
```

### 檢查 CORRECTED 文件

```bash
# 列出所有 CORRECTED 文件
find structured_books -name "*_CORRECTED.md" | wc -l

# 列出所有 CORRECTED 文件清單
find structured_books -name "*_CORRECTED.md" | sort
```

---

## 🎯 Editor 指令 2：執行 Builder 產生索引

### 執行建構器

```bash
# 進入專案根目錄
cd /Users/kevincheng/JarvisV1

# 執行 Builder
python3 structured_books/build_master_index.py
```

### 預期輸出

```
============================================================
Phase 4: MASTER_INDEX Builder
============================================================
============================================================
開始建立 MASTER_INDEX...
============================================================
📚 找到 14 個 CORRECTED 文件
📖 處理文件: J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
  ✅ 提取了 X 個知識節點
...
📊 總共提取了 Y 個知識節點
✅ 建立了 Y 個索引項目
🔗 建立關聯關係...
  ✅ 建立了 Z 個關聯關係
🔍 驗證索引...
  ✅ 索引驗證通過
💾 匯出 JSONL: knowledge_base/jgod_master_index_v1.jsonl
  ✅ 已匯出 Y 個項目
💾 匯出 Markdown: docs/J-GOD_MASTER_INDEX_v1.md
  ✅ 已匯出 Markdown 文件 (X 行)
============================================================
✅ Phase 4: MASTER_INDEX 建立完成！
============================================================
```

---

## 🎯 Editor 指令 3：檢查輸出結果

### 檢查 JSONL 輸出

```bash
# 檢查 JSONL 文件是否存在
ls -lh knowledge_base/jgod_master_index_v1.jsonl

# 查看前 3 行 JSONL（範例）
head -n 3 knowledge_base/jgod_master_index_v1.jsonl | python3 -m json.tool

# 統計總行數（即總節點數）
wc -l knowledge_base/jgod_master_index_v1.jsonl

# 檢查 JSONL 格式是否正確
python3 -c "import json; [json.loads(line) for line in open('knowledge_base/jgod_master_index_v1.jsonl')]; print('✅ JSONL 格式正確')"
```

### 檢查 Markdown 輸出

```bash
# 檢查 Markdown 文件是否存在
ls -lh docs/J-GOD_MASTER_INDEX_v1.md

# 查看文件前 50 行
head -n 50 docs/J-GOD_MASTER_INDEX_v1.md

# 統計文件行數和大小
wc -l docs/J-GOD_MASTER_INDEX_v1.md
```

---

## 🎯 Editor 指令 4：驗證索引內容

### 檢查索引統計

```bash
# 使用 Python 分析索引內容
python3 << 'EOF'
import json
from collections import Counter, defaultdict

# 讀取 JSONL
items = []
with open('knowledge_base/jgod_master_index_v1.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        items.append(json.loads(line))

print(f"總節點數：{len(items)}")
print(f"\n按類型統計：")
type_counts = Counter(item['type'] for item in items)
for node_type, count in sorted(type_counts.items()):
    print(f"  - {node_type}: {count} 個")

print(f"\n按來源文件統計：")
source_counts = Counter(item['source_file'] for item in items)
for source, count in sorted(source_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  - {source}: {count} 個")

print(f"\n標籤統計（前 10）：")
all_tags = []
for item in items:
    all_tags.extend(item.get('tags', []))
tag_counts = Counter(all_tags)
for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  - {tag}: {count} 個")

print(f"\n關聯關係統計：")
related_counts = [len(item.get('related_ids', [])) for item in items]
if related_counts:
    print(f"  - 平均關聯數：{sum(related_counts) / len(related_counts):.2f}")
    print(f"  - 最大關聯數：{max(related_counts)}")
    print(f"  - 最小關聯數：{min(related_counts)}")
EOF
```

### 檢查特定節點

```bash
# 搜尋特定類型的節點
python3 << 'EOF'
import json

# 讀取 JSONL
items = []
with open('knowledge_base/jgod_master_index_v1.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        items.append(json.loads(line))

# 搜尋包含 "Sharpe" 的節點
sharpe_items = [item for item in items if 'sharpe' in item.get('title', '').lower() or 'sharpe' in item.get('description', '').lower()]
print(f"找到 {len(sharpe_items)} 個包含 'Sharpe' 的節點：\n")
for item in sharpe_items[:5]:
    print(f"- [{item['id']}] {item['title']}")
    print(f"  類型：{item['type']}")
    print(f"  來源：{item['source_file']}")
    print()
EOF
```

---

## 🎯 Editor 指令 5：更新 README

### 更新 structured_books/README.md

在 `structured_books/README.md` 中的 Phase 4 部分，更新狀態為「✅ 已完成」：

```markdown
### Phase 4：MASTER_INDEX ✅ 已完成

- ✅ 建立標準文件：`docs/PHASE4_MASTER_INDEX_STANDARD_v1.md`
- ✅ 建立 Builder 程式：`structured_books/build_master_index.py`
- ✅ 產生 JSONL 索引：`knowledge_base/jgod_master_index_v1.jsonl`
- ✅ 產生 Markdown 索引：`docs/J-GOD_MASTER_INDEX_v1.md`
```

---

## 🎯 Editor 指令 6：測試索引讀取

### 建立簡單測試腳本

```python
# 檔案：tests/test_master_index.py

"""測試 MASTER_INDEX 讀取和查詢功能"""

import json
from pathlib import Path

def test_read_jsonl():
    """測試讀取 JSONL 索引"""
    jsonl_path = Path("knowledge_base/jgod_master_index_v1.jsonl")
    
    assert jsonl_path.exists(), f"JSONL 文件不存在: {jsonl_path}"
    
    items = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            items.append(item)
    
    assert len(items) > 0, "索引為空"
    
    # 檢查必要欄位
    for item in items[:10]:  # 只檢查前 10 個
        assert 'id' in item, f"缺少 id: {item}"
        assert 'type' in item, f"缺少 type: {item}"
        assert 'title' in item, f"缺少 title: {item}"
        assert 'source_file' in item, f"缺少 source_file: {item}"
    
    print(f"✅ 成功讀取 {len(items)} 個索引項目")
    return items

if __name__ == "__main__":
    items = test_read_jsonl()
    print(f"\n前 5 個項目：")
    for item in items[:5]:
        print(f"  - [{item['id']}] {item['title']} ({item['type']})")
```

執行測試：

```bash
python3 tests/test_master_index.py
```

---

## 📝 完整執行流程（一鍵執行）

### 完整執行腳本

建立一個腳本自動執行所有步驟：

```bash
#!/bin/bash
# 檔案：scripts/run_phase4_master_index.sh

echo "============================================================"
echo "Phase 4: MASTER_INDEX - 完整執行流程"
echo "============================================================"
echo ""

# 步驟 1: 檢查環境
echo "📋 步驟 1: 檢查環境..."
cd /Users/kevincheng/JarvisV1

if [ ! -d "structured_books" ]; then
    echo "❌ 錯誤：structured_books 目錄不存在"
    exit 1
fi

CORRECTED_COUNT=$(find structured_books -name "*_CORRECTED.md" | wc -l | tr -d ' ')
echo "  ✅ 找到 $CORRECTED_COUNT 個 CORRECTED 文件"

# 步驟 2: 執行 Builder
echo ""
echo "🔨 步驟 2: 執行 MASTER_INDEX Builder..."
python3 structured_books/build_master_index.py

if [ $? -ne 0 ]; then
    echo "❌ Builder 執行失敗"
    exit 1
fi

# 步驟 3: 驗證輸出
echo ""
echo "✅ 步驟 3: 驗證輸出..."

if [ -f "knowledge_base/jgod_master_index_v1.jsonl" ]; then
    JSONL_COUNT=$(wc -l < knowledge_base/jgod_master_index_v1.jsonl | tr -d ' ')
    echo "  ✅ JSONL 文件已建立（$JSONL_COUNT 行）"
else
    echo "  ❌ JSONL 文件不存在"
    exit 1
fi

if [ -f "docs/J-GOD_MASTER_INDEX_v1.md" ]; then
    MD_SIZE=$(ls -lh docs/J-GOD_MASTER_INDEX_v1.md | awk '{print $5}')
    echo "  ✅ Markdown 文件已建立（大小：$MD_SIZE）"
else
    echo "  ❌ Markdown 文件不存在"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ Phase 4: MASTER_INDEX 執行完成！"
echo "============================================================"
```

執行：

```bash
chmod +x scripts/run_phase4_master_index.sh
./scripts/run_phase4_master_index.sh
```

---

## 🎯 Editor 指令 7：整合到 KnowledgeBrain

### 更新 KnowledgeBrain 支援 MASTER_INDEX

如果需要讓 `KnowledgeBrain` 支援從 MASTER_INDEX 讀取，可以建立一個 wrapper：

```python
# 檔案：jgod/knowledge/master_index_reader.py

"""讀取和查詢 MASTER_INDEX"""

from pathlib import Path
from typing import List, Dict, Optional
import json

class MasterIndexReader:
    """讀取 MASTER_INDEX 的簡單介面"""
    
    def __init__(self, jsonl_path: Optional[Path] = None):
        """初始化讀取器"""
        if jsonl_path is None:
            project_root = Path(__file__).parent.parent.parent
            jsonl_path = project_root / "knowledge_base" / "jgod_master_index_v1.jsonl"
        
        self.jsonl_path = Path(jsonl_path)
        self._items: List[Dict] = []
        self._by_id: Dict[str, Dict] = {}
        self._loaded = False
    
    def load(self) -> None:
        """載入索引"""
        if self._loaded:
            return
        
        if not self.jsonl_path.exists():
            raise FileNotFoundError(f"MASTER_INDEX 不存在: {self.jsonl_path}")
        
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                self._items.append(item)
                self._by_id[item['id']] = item
        
        self._loaded = True
    
    def get_by_id(self, item_id: str) -> Optional[Dict]:
        """根據 ID 取得項目"""
        if not self._loaded:
            self.load()
        return self._by_id.get(item_id)
    
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """搜尋項目"""
        if not self._loaded:
            self.load()
        
        query_lower = query.lower()
        results = []
        
        for item in self._items:
            score = 0
            if query_lower in item.get('title', '').lower():
                score += 10
            if query_lower in item.get('description', '').lower():
                score += 5
            if query_lower in ' '.join(item.get('tags', [])).lower():
                score += 3
            
            if score > 0:
                results.append((score, item))
        
        # 按分數排序
        results.sort(key=lambda x: -x[0])
        
        return [item for _, item in results[:limit]]
    
    def get_by_type(self, node_type: str) -> List[Dict]:
        """根據類型取得項目"""
        if not self._loaded:
            self.load()
        
        return [item for item in self._items if item.get('type') == node_type]
```

---

## 📋 檢查清單

執行完成後，確認以下項目：

- [ ] `docs/PHASE4_MASTER_INDEX_STANDARD_v1.md` 已建立
- [ ] `structured_books/build_master_index.py` 已建立且可執行
- [ ] `structured_books/MASTER_INDEX_EXAMPLES.md` 已建立
- [ ] `knowledge_base/jgod_master_index_v1.jsonl` 已產生
- [ ] `docs/J-GOD_MASTER_INDEX_v1.md` 已產生
- [ ] JSONL 格式正確（可用 JSON 解析）
- [ ] Markdown 格式正確（可讀取）
- [ ] 索引包含所有 CORRECTED 文件的節點
- [ ] 所有節點都有必要的欄位（id, type, title, etc.）
- [ ] 關聯關係已建立
- [ ] `structured_books/README.md` 已更新狀態

---

## 🚀 後續步驟

1. **測試索引查詢功能**：建立測試腳本驗證查詢
2. **整合到 KnowledgeBrain**：讓 KnowledgeBrain 支援從 MASTER_INDEX 讀取
3. **建立視覺化工具**：可選，建立索引的視覺化瀏覽工具
4. **自動更新機制**：當 CORRECTED 文件更新時，自動重建索引

---

**End of Editor Instructions**

