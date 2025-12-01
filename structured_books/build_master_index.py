#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: MASTER_INDEX Builder

從 Phase 1-3 的所有 CORRECTED 文件中提取知識節點，建立統一的 MASTER_INDEX。

處理流程：
1. 掃描 corrected_md/ 中所有已校正 MD（實際上是 structured_books/*_CORRECTED.md）
2. 使用 extractors 解析節點
3. 建立完整的索引 dict
4. 產生 JSONL + Markdown 兩種格式
5. 安全防呆（重複 id、缺欄位、空節點）
"""

from __future__ import annotations

import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import sys

# 專案根目錄
REPO_ROOT = Path(__file__).parent.parent
STRUCTURED_BOOKS_DIR = REPO_ROOT / "structured_books"
KNOWLEDGE_BASE_DIR = REPO_ROOT / "knowledge_base"
DOCS_DIR = REPO_ROOT / "docs"


@dataclass
class MasterIndexItem:
    """MASTER_INDEX 單一項目資料結構"""
    id: str
    type: str  # RULE / FORMULA / CONCEPT / STRUCTURE / TABLE / CODE / NOTE
    title: str
    source_file: str  # 原始 MD 文件名稱
    source_phase: str  # STRUCTURED / ENHANCED / CORRECTED
    tags: List[str] = field(default_factory=list)
    description: str = ""
    related_ids: List[str] = field(default_factory=list)
    path: str = ""  # 檔案位置（相對路徑）
    version: str = "v1"
    line_range: Optional[Tuple[int, int]] = None
    raw_text: str = ""
    structured: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """轉換為字典（用於 JSON 輸出）"""
        result = asdict(self)
        # 處理 Optional 欄位
        if result["line_range"] is None:
            del result["line_range"]
        if result["structured"] is None:
            del result["structured"]
        return result


class KnowledgeNodeExtractor:
    """知識節點提取器
    
    從 CORRECTED Markdown 文件中提取結構化的知識節點。
    """
    
    # 節點類型標記模式
    TYPE_PATTERNS = {
        "RULE": re.compile(r'\*\*\[RULE\]\*\*', re.IGNORECASE),
        "FORMULA": re.compile(r'\*\*\[FORMULA\]\*\*', re.IGNORECASE),
        "CONCEPT": re.compile(r'\*\*\[CONCEPT\]\*\*', re.IGNORECASE),
        "STRUCTURE": re.compile(r'\*\*\[STRUCTURE\]\*\*', re.IGNORECASE),
        "TABLE": re.compile(r'\*\*\[TABLE\]\*\*', re.IGNORECASE),
        "CODE": re.compile(r'\*\*\[CODE\]\*\*', re.IGNORECASE),
        "NOTE": re.compile(r'\*\*\[NOTE\]\*\*', re.IGNORECASE),
    }
    
    # 自動識別模式
    FORMULA_PATTERN = re.compile(r'\$\$.*?\$\$|\$[^\n$]+\$', re.DOTALL)
    CODE_BLOCK_PATTERN = re.compile(r'```(\w+)?\n.*?```', re.DOTALL)
    TABLE_PATTERN = re.compile(r'\|.*\|.*\n\|[-\s\|]+\|', re.MULTILINE)
    
    def __init__(self):
        """初始化提取器"""
        self.nodes: List[Dict] = []
    
    def extract_from_file(self, file_path: Path, source_phase: str = "CORRECTED") -> List[Dict]:
        """
        從單一文件中提取所有知識節點
        
        Args:
            file_path: Markdown 文件路徑
            source_phase: 來源階段（STRUCTURED / ENHANCED / CORRECTED）
        
        Returns:
            知識節點列表
        """
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            return []
        
        print(f"📖 處理文件: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            content = ''.join(lines)
        
        nodes = []
        current_node = None
        current_type = None
        current_lines = []
        start_line = 0
        
        source_file_basename = file_path.stem.replace('_CORRECTED', '').replace('_ENHANCED', '').replace('_STRUCTURED', '')
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 檢查是否為節點類型標記
            node_type = self._detect_node_type(stripped)
            
            if node_type:
                # 保存前一個節點
                if current_node and current_type:
                    node_dict = self._finalize_node(
                        current_node, current_type, current_lines, 
                        start_line, line_num - 1, file_path, source_file_basename, source_phase
                    )
                    if node_dict:
                        nodes.append(node_dict)
                
                # 開始新節點
                current_type = node_type
                current_lines = [line]
                start_line = line_num
                current_node = {
                    "type": node_type,
                    "raw_lines": []
                }
            elif current_node is not None:
                # 累積節點內容
                current_lines.append(line)
                current_node["raw_lines"].append(line)
            else:
                # 檢查是否為自動識別的節點（無標記的公式、程式碼等）
                auto_node = self._detect_auto_node(stripped, line_num, file_path, source_file_basename, source_phase)
                if auto_node:
                    nodes.append(auto_node)
        
        # 保存最後一個節點
        if current_node and current_type:
            node_dict = self._finalize_node(
                current_node, current_type, current_lines,
                start_line, len(lines), file_path, source_file_basename, source_phase
            )
            if node_dict:
                nodes.append(node_dict)
        
        print(f"  ✅ 提取了 {len(nodes)} 個知識節點")
        return nodes
    
    def _detect_node_type(self, line: str) -> Optional[str]:
        """偵測節點類型標記"""
        for node_type, pattern in self.TYPE_PATTERNS.items():
            if pattern.search(line):
                return node_type
        return None
    
    def _detect_auto_node(self, line: str, line_num: int, file_path: Path, 
                          source_file: str, source_phase: str) -> Optional[Dict]:
        """自動識別無標記的節點（公式、程式碼等）"""
        # 檢查公式
        if self.FORMULA_PATTERN.search(line):
            return {
                "type": "FORMULA",
                "raw_lines": [line],
                "start_line": line_num,
                "end_line": line_num,
                "source_file": source_file,
                "source_phase": source_phase,
                "path": str(file_path.relative_to(REPO_ROOT))
            }
        
        # 檢查程式碼區塊（簡化版，實際需要更複雜的邏輯）
        if self.CODE_BLOCK_PATTERN.search(line):
            return {
                "type": "CODE",
                "raw_lines": [line],
                "start_line": line_num,
                "end_line": line_num,
                "source_file": source_file,
                "source_phase": source_phase,
                "path": str(file_path.relative_to(REPO_ROOT))
            }
        
        return None
    
    def _finalize_node(self, node: Dict, node_type: str, lines: List[str],
                       start_line: int, end_line: int, file_path: Path,
                       source_file: str, source_phase: str) -> Optional[Dict]:
        """完成節點的提取和結構化"""
        raw_text = ''.join(lines).strip()
        
        if not raw_text or len(raw_text) < 10:  # 過濾空節點
            return None
        
        # 提取標題
        title = self._extract_title(lines)
        
        # 提取標籤
        tags = self._extract_tags(lines, raw_text)
        
        # 提取描述（前 200 字元）
        description = self._extract_description(raw_text)
        
        # 解析結構化資料
        structured = self._parse_structured(node_type, raw_text, lines)
        
        return {
            "type": node_type,
            "title": title,
            "source_file": source_file,
            "source_phase": source_phase,
            "tags": tags,
            "description": description,
            "line_range": (start_line, end_line),
            "path": str(file_path.relative_to(REPO_ROOT)),
            "raw_text": raw_text,
            "structured": structured
        }
    
    def _extract_title(self, lines: List[str]) -> str:
        """提取標題"""
        for line in lines[:10]:  # 只檢查前 10 行
            stripped = line.strip()
            # 檢查 Markdown 標題
            if stripped.startswith('#'):
                return stripped.lstrip('#').strip()
            # 檢查粗體文字
            if stripped.startswith('**') and stripped.endswith('**'):
                title = stripped[2:-2].strip()
                if len(title) < 100:  # 避免提取過長的內容
                    return title
            # 檢查第一行非空文字
            if stripped and not stripped.startswith('[') and len(stripped) < 100:
                return stripped[:100]
        return "未命名節點"
    
    def _extract_tags(self, lines: List[str], raw_text: str) -> List[str]:
        """提取標籤"""
        tags = set()
        
        # 從內容中自動識別標籤
        text_lower = raw_text.lower()
        
        tag_keywords = {
            "risk": ["風險", "風控", "停損", "drawdown", "risk"],
            "strategy": ["策略", "strategy", "交易", "trading"],
            "entry": ["進場", "買入", "entry", "buy"],
            "exit": ["出場", "賣出", "exit", "sell"],
            "performance": ["績效", "報酬", "performance", "return", "sharpe"],
            "path_a": ["path a", "回測", "backtest", "歷史"],
            "alpha": ["alpha", "因子", "factor"],
            "optimizer": ["optimizer", "優化", "optimization"],
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.add(tag)
        
        return sorted(list(tags))
    
    def _extract_description(self, raw_text: str, max_length: int = 200) -> str:
        """提取描述（自動摘要）"""
        # 移除 Markdown 格式
        text = re.sub(r'#{1,6}\s+', '', raw_text)  # 移除標題標記
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # 移除粗體
        text = re.sub(r'`([^`]+)`', r'\1', text)  # 移除程式碼標記
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # 移除連結
        text = re.sub(r'\$\$.*?\$\$', '', text, flags=re.DOTALL)  # 移除公式
        
        # 提取前 max_length 字元
        description = text.strip()[:max_length]
        
        # 確保在單詞邊界截斷
        if len(text) > max_length:
            last_space = description.rfind(' ')
            if last_space > max_length * 0.8:  # 只在 80% 後才截斷
                description = description[:last_space]
        
        return description.strip()
    
    def _parse_structured(self, node_type: str, raw_text: str, lines: List[str]) -> Optional[Dict]:
        """根據節點類型解析結構化資料"""
        if node_type == "FORMULA":
            return self._parse_formula(raw_text)
        elif node_type == "RULE":
            return self._parse_rule(raw_text)
        elif node_type == "CONCEPT":
            return self._parse_concept(raw_text)
        elif node_type == "CODE":
            return self._parse_code(raw_text)
        elif node_type == "TABLE":
            return self._parse_table(raw_text)
        else:
            return None
    
    def _parse_formula(self, raw_text: str) -> Dict:
        """解析公式"""
        # 提取 LaTeX 公式
        formulas = self.FORMULA_PATTERN.findall(raw_text)
        
        expression = formulas[0] if formulas else ""
        
        # 提取變數說明（簡化版）
        variables = {}
        # 這裡可以添加更複雜的變數提取邏輯
        
        return {
            "expression": expression,
            "variables": variables,
            "notes": ""
        }
    
    def _parse_rule(self, raw_text: str) -> Dict:
        """解析規則"""
        # 簡化版：從文字中提取 if-then 邏輯
        # 實際需要更複雜的 NLP 處理
        
        # 尋找「如果」「當」「則」「應該」等關鍵字
        if_match = re.search(r'(如果|當|若|當.*?時)(.+?)(則|應該|必須|要)', raw_text, re.DOTALL)
        
        condition = if_match.group(2).strip() if if_match else ""
        action = ""
        
        return {
            "if": condition,
            "then": action,
            "priority": 5,  # 預設優先級
            "scope": "general"
        }
    
    def _parse_concept(self, raw_text: str) -> Dict:
        """解析概念"""
        # 提取定義和範例
        definition = self._extract_description(raw_text, 500)
        examples = []
        
        # 尋找範例（簡化版）
        example_pattern = re.compile(r'範例[：:]\s*(.+?)(?:\n|$)', re.IGNORECASE)
        examples_match = example_pattern.findall(raw_text)
        if examples_match:
            examples = [ex.strip() for ex in examples_match[:3]]
        
        return {
            "name": self._extract_title([raw_text.split('\n')[0]]),
            "definition": definition,
            "examples": examples
        }
    
    def _parse_code(self, raw_text: str) -> Dict:
        """解析程式碼"""
        # 提取程式碼區塊
        code_match = self.CODE_BLOCK_PATTERN.search(raw_text)
        
        if code_match:
            language = code_match.group(1) or "python"
            code = code_match.group(0).strip('`').strip()
            # 移除語言標記
            code = re.sub(r'^(\w+)\n', '', code, flags=re.MULTILINE)
            return {
                "language": language,
                "code": code
            }
        
        return {
            "language": "python",
            "code": raw_text
        }
    
    def _parse_table(self, raw_text: str) -> Dict:
        """解析表格"""
        # 簡化版：提取表格結構
        table_match = self.TABLE_PATTERN.search(raw_text)
        
        if table_match:
            table_text = table_match.group(0)
            lines = [l.strip() for l in table_text.split('\n') if '|' in l]
            
            if len(lines) >= 2:
                columns = [col.strip() for col in lines[0].split('|') if col.strip()]
                rows = []
                for line in lines[2:]:  # 跳過分隔線
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    if cells:
                        rows.append(cells)
                
                return {
                    "columns": columns,
                    "rows": rows
                }
        
        return {
            "columns": [],
            "rows": []
        }


class MasterIndexBuilder:
    """MASTER_INDEX 建構器
    
    整合所有知識節點，建立統一的索引。
    """
    
    def __init__(self):
        """初始化建構器"""
        self.extractor = KnowledgeNodeExtractor()
        self.master_index: Dict[str, MasterIndexItem] = {}
        self.by_type: Dict[str, List[str]] = defaultdict(list)
        self.by_source_file: Dict[str, List[str]] = defaultdict(list)
        self.by_tags: Dict[str, List[str]] = defaultdict(list)
        self.id_counter: Dict[str, int] = defaultdict(int)
        self.used_ids: Set[str] = set()
    
    def scan_corrected_files(self) -> List[Path]:
        """掃描所有 CORRECTED 文件"""
        corrected_files = list(STRUCTURED_BOOKS_DIR.glob("*_CORRECTED.md"))
        print(f"📚 找到 {len(corrected_files)} 個 CORRECTED 文件")
        return corrected_files
    
    def build_index(self) -> None:
        """建立完整索引"""
        print("=" * 60)
        print("開始建立 MASTER_INDEX...")
        print("=" * 60)
        
        # 掃描文件
        corrected_files = self.scan_corrected_files()
        
        # 從每個文件提取節點
        all_nodes = []
        for file_path in corrected_files:
            nodes = self.extractor.extract_from_file(file_path, source_phase="CORRECTED")
            all_nodes.extend(nodes)
        
        print(f"\n📊 總共提取了 {len(all_nodes)} 個知識節點")
        
        # 轉換為 MasterIndexItem 並分配 ID
        for node in all_nodes:
            item = self._create_master_index_item(node)
            if item:
                self.master_index[item.id] = item
                self._update_indices(item)
        
        print(f"✅ 建立了 {len(self.master_index)} 個索引項目")
        
        # 建立關聯關係
        self._build_relationships()
        
        # 安全防呆檢查
        self._validate_index()
    
    def _create_master_index_item(self, node: Dict) -> Optional[MasterIndexItem]:
        """建立 MasterIndexItem"""
        node_type = node.get("type", "NOTE")
        source_file = node.get("source_file", "unknown")
        
        # 生成唯一 ID
        item_id = self._generate_unique_id(node_type, source_file)
        
        # 建立項目
        item = MasterIndexItem(
            id=item_id,
            type=node_type,
            title=node.get("title", "未命名"),
            source_file=source_file,
            source_phase=node.get("source_phase", "CORRECTED"),
            tags=node.get("tags", []),
            description=node.get("description", ""),
            related_ids=[],  # 稍後建立
            path=node.get("path", ""),
            version="v1",
            line_range=node.get("line_range"),
            raw_text=node.get("raw_text", ""),
            structured=node.get("structured")
        )
        
        return item
    
    def _generate_unique_id(self, node_type: str, source_file: str) -> str:
        """生成唯一 ID"""
        # 簡化檔名
        file_base = source_file.replace('_AI知識庫版_v1', '').replace('_CORRECTED', '')
        file_base = file_base.replace(' ', '_').replace('-', '_')
        file_base = re.sub(r'[^\w]', '', file_base)
        
        # 計數器
        self.id_counter[f"{node_type}_{file_base}"] += 1
        seq = self.id_counter[f"{node_type}_{file_base}"]
        
        # 生成 ID
        item_id = f"{node_type}_{file_base}_{seq:03d}"
        
        # 檢查重複
        if item_id in self.used_ids:
            # 添加後綴
            counter = 1
            while f"{item_id}_dup{counter}" in self.used_ids:
                counter += 1
            item_id = f"{item_id}_dup{counter}"
        
        self.used_ids.add(item_id)
        return item_id
    
    def _update_indices(self, item: MasterIndexItem) -> None:
        """更新反向索引"""
        self.by_type[item.type].append(item.id)
        self.by_source_file[item.source_file].append(item.id)
        for tag in item.tags:
            self.by_tags[tag].append(item.id)
    
    def _build_relationships(self) -> None:
        """建立關聯關係"""
        print("\n🔗 建立關聯關係...")
        
        # 簡化版：根據標題和描述中的關鍵字匹配
        # 實際需要更複雜的 NLP 處理
        
        all_items = list(self.master_index.values())
        
        for item in all_items:
            related = []
            
            # 檢查其他項目中是否有相關的
            for other_item in all_items:
                if other_item.id == item.id:
                    continue
                
                # 簡單的關鍵字匹配
                if self._is_related(item, other_item):
                    related.append(other_item.id)
            
            item.related_ids = related[:5]  # 限制最多 5 個關聯
        
        total_relations = sum(len(item.related_ids) for item in all_items)
        print(f"  ✅ 建立了 {total_relations} 個關聯關係")
    
    def _is_related(self, item1: MasterIndexItem, item2: MasterIndexItem) -> bool:
        """判斷兩個項目是否相關"""
        # 簡單的關鍵字匹配（實際需要更複雜的 NLP）
        
        # 檢查標題相似度
        title1_words = set(item1.title.lower().split())
        title2_words = set(item2.title.lower().split())
        if len(title1_words & title2_words) >= 2:
            return True
        
        # 檢查標籤重疊
        if set(item1.tags) & set(item2.tags):
            return True
        
        # 檢查描述中的關鍵字
        desc1_words = set(item1.description.lower().split())
        desc2_words = set(item2.description.lower().split())
        common_words = desc1_words & desc2_words
        if len(common_words) >= 3:
            return True
        
        return False
    
    def _validate_index(self) -> None:
        """驗證索引（安全防呆）"""
        print("\n🔍 驗證索引...")
        
        issues = []
        
        for item_id, item in self.master_index.items():
            # 檢查必填欄位
            if not item.id:
                issues.append(f"{item_id}: 缺少 ID")
            if not item.type:
                issues.append(f"{item_id}: 缺少 type")
            if not item.title:
                issues.append(f"{item_id}: 缺少 title")
            if not item.raw_text or len(item.raw_text) < 10:
                issues.append(f"{item_id}: raw_text 太短或為空")
        
        if issues:
            print(f"  ⚠️  發現 {len(issues)} 個問題:")
            for issue in issues[:10]:  # 只顯示前 10 個
                print(f"    - {issue}")
            if len(issues) > 10:
                print(f"    ... 還有 {len(issues) - 10} 個問題")
        else:
            print("  ✅ 索引驗證通過")
    
    def export_jsonl(self, output_path: Path) -> None:
        """匯出為 JSONL 格式"""
        print(f"\n💾 匯出 JSONL: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in self.master_index.values():
                json_line = json.dumps(item.to_dict(), ensure_ascii=False)
                f.write(json_line + '\n')
        
        print(f"  ✅ 已匯出 {len(self.master_index)} 個項目")
    
    def export_markdown(self, output_path: Path) -> None:
        """匯出為 Markdown 格式"""
        print(f"\n💾 匯出 Markdown: {output_path}")
        
        lines = []
        
        # 標題
        lines.append("# J-GOD MASTER_INDEX v1\n")
        lines.append("> **說明**：本索引整合了 Phase 1-3 所有結構化知識節點。\n")
        lines.append("> **生成時間**：自動生成\n")
        lines.append("\n---\n\n")
        
        # 總覽
        lines.append("## 📊 總覽\n\n")
        lines.append(f"- **總節點數**：{len(self.master_index)}\n")
        lines.append(f"- **按類型統計**：\n")
        for node_type, items in sorted(self.by_type.items()):
            lines.append(f"  - {node_type}: {len(items)} 個\n")
        lines.append(f"- **按來源文件統計**：{len(self.by_source_file)} 個文件\n")
        lines.append(f"- **標籤數量**：{len(self.by_tags)} 個\n\n")
        
        # 按類型瀏覽
        lines.append("## 🔍 按類型瀏覽\n\n")
        for node_type in sorted(self.by_type.keys()):
            lines.append(f"### {node_type}\n\n")
            item_ids = self.by_type[node_type]
            for item_id in item_ids[:20]:  # 只顯示前 20 個
                item = self.master_index[item_id]
                lines.append(f"- **[{item_id}]** {item.title}\n")
                lines.append(f"  - 來源：{item.source_file}\n")
                if item.tags:
                    lines.append(f"  - 標籤：{', '.join(item.tags)}\n")
                if item.related_ids:
                    lines.append(f"  - 相關：{', '.join(item.related_ids[:3])}\n")
                lines.append(f"  - 描述：{item.description[:100]}...\n\n")
            if len(item_ids) > 20:
                lines.append(f"  ... 還有 {len(item_ids) - 20} 個項目\n\n")
        
        # 索引列表
        lines.append("## 📑 完整索引列表\n\n")
        lines.append("### 按 ID 排序\n\n")
        for item_id in sorted(self.master_index.keys()):
            item = self.master_index[item_id]
            lines.append(f"- [{item_id}] {item.title} ({item.type})\n")
        
        # 寫入檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"  ✅ 已匯出 Markdown 文件 ({len(lines)} 行)")


def main():
    """主函數"""
    print("=" * 60)
    print("Phase 4: MASTER_INDEX Builder")
    print("=" * 60)
    
    # 建立建構器
    builder = MasterIndexBuilder()
    
    # 建立索引
    builder.build_index()
    
    # 確保輸出目錄存在
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 匯出 JSONL
    jsonl_path = KNOWLEDGE_BASE_DIR / "jgod_master_index_v1.jsonl"
    builder.export_jsonl(jsonl_path)
    
    # 匯出 Markdown
    md_path = DOCS_DIR / "J-GOD_MASTER_INDEX_v1.md"
    builder.export_markdown(md_path)
    
    print("\n" + "=" * 60)
    print("✅ Phase 4: MASTER_INDEX 建立完成！")
    print("=" * 60)
    print(f"\n輸出檔案：")
    print(f"  - JSONL: {jsonl_path}")
    print(f"  - Markdown: {md_path}")


if __name__ == "__main__":
    main()

