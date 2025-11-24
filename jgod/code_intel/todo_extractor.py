"""
TODO 提取器：從程式碼中提取 TODO、FIX、BUG 等註解
"""
from typing import List, Dict, Any
from pathlib import Path
import re
from dataclasses import dataclass


@dataclass
class TodoItem:
    """TODO 項目"""
    file_path: str
    line_number: int
    todo_type: str  # "TODO", "FIX", "BUG", etc.
    content: str
    priority: str = "normal"  # "high", "normal", "low"


class TodoExtractor:
    """
    TODO 提取器
    
    功能：
    - 掃描程式碼中的 TODO、FIX、BUG 註解
    - 產生任務清單
    - 分類優先級
    """
    
    # 匹配模式
    PATTERNS = {
        "TODO": re.compile(r"#\s*TODO[:\s]+(.+)", re.IGNORECASE),
        "FIX": re.compile(r"#\s*FIX[:\s]+(.+)", re.IGNORECASE),
        "BUG": re.compile(r"#\s*BUG[:\s]+(.+)", re.IGNORECASE),
        "HACK": re.compile(r"#\s*HACK[:\s]+(.+)", re.IGNORECASE),
        "NOTE": re.compile(r"#\s*NOTE[:\s]+(.+)", re.IGNORECASE),
    }
    
    def __init__(self):
        """初始化 TODO 提取器"""
        pass
    
    def extract_from_file(self, file_path: Path) -> List[TodoItem]:
        """
        從檔案中提取 TODO
        
        Args:
            file_path: 檔案路徑
        
        Returns:
            TODO 項目列表
        """
        todos = []
        
        if not file_path.exists() or not file_path.is_file():
            return todos
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    for todo_type, pattern in self.PATTERNS.items():
                        match = pattern.search(line)
                        if match:
                            content = match.group(1).strip()
                            priority = self._detect_priority(content)
                            
                            todos.append(TodoItem(
                                file_path=str(file_path),
                                line_number=line_num,
                                todo_type=todo_type,
                                content=content,
                                priority=priority,
                            ))
        except Exception as e:
            print(f"讀取檔案失敗 {file_path}: {e}")
        
        return todos
    
    def extract_from_directory(self, directory: Path) -> List[TodoItem]:
        """
        從目錄中提取所有 TODO
        
        Args:
            directory: 目錄路徑
        
        Returns:
            TODO 項目列表
        """
        todos = []
        
        # 只處理 Python 檔案
        for py_file in directory.rglob("*.py"):
            todos.extend(self.extract_from_file(py_file))
        
        return todos
    
    def _detect_priority(self, content: str) -> str:
        """
        偵測優先級
        
        Args:
            content: TODO 內容
        
        Returns:
            優先級
        """
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["urgent", "critical", "重要", "緊急"]):
            return "high"
        elif any(keyword in content_lower for keyword in ["low", "minor", "次要"]):
            return "low"
        else:
            return "normal"
    
    def generate_todo_list(self, todos: List[TodoItem]) -> str:
        """
        產生 TODO 清單（Markdown 格式）
        
        Args:
            todos: TODO 項目列表
        
        Returns:
            Markdown 格式的 TODO 清單
        """
        if not todos:
            return "# TODO 清單\n\n目前沒有待辦事項。\n"
        
        # 依類型分組
        by_type: Dict[str, List[TodoItem]] = {}
        for todo in todos:
            if todo.todo_type not in by_type:
                by_type[todo.todo_type] = []
            by_type[todo.todo_type].append(todo)
        
        lines = ["# TODO 清單\n", f"總計：{len(todos)} 項\n"]
        
        for todo_type, items in sorted(by_type.items()):
            lines.append(f"\n## {todo_type} ({len(items)} 項)\n")
            
            for todo in sorted(items, key=lambda x: (x.priority == "high", x.file_path, x.line_number)):
                priority_marker = "🔴" if todo.priority == "high" else "🟡" if todo.priority == "normal" else "🟢"
                lines.append(
                    f"- {priority_marker} **{todo.file_path}:{todo.line_number}** - {todo.content}\n"
                )
        
        return "\n".join(lines)

