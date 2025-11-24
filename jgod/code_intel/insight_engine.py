"""
洞察引擎：分析模組覆蓋率並指出系統弱點
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import ast
import os

from .scanner import scan_project, FileSummary
from .todo_extractor import TodoExtractor, TodoItem


@dataclass
class ModuleCoverage:
    """模組覆蓋率"""
    module_path: str
    total_files: int
    has_tests: bool
    test_coverage: float  # 0.0-1.0
    todo_count: int
    complexity_score: float


@dataclass
class SystemWeakness:
    """系統弱點"""
    module: str
    weakness_type: str  # "no_tests", "high_todos", "high_complexity"
    severity: str  # "high", "medium", "low"
    description: str
    recommendation: str


class InsightEngine:
    """
    洞察引擎
    
    功能：
    - 分析模組覆蓋率
    - 找出系統弱點
    - 提供改進建議
    """
    
    def __init__(self):
        """初始化洞察引擎"""
        self.todo_extractor = TodoExtractor()
    
    def analyze_module_coverage(
        self,
        root: Optional[Path] = None,
    ) -> List[ModuleCoverage]:
        """
        分析模組覆蓋率
        
        Args:
            root: 專案根目錄
        
        Returns:
            模組覆蓋率列表
        """
        files = scan_project(root)
        
        # 依模組分組
        modules: Dict[str, List[FileSummary]] = {}
        for file in files:
            parts = file.relative_path.split(os.sep)
            if len(parts) >= 2:
                module = os.sep.join(parts[:2])
            else:
                module = "root"
            
            if module not in modules:
                modules[module] = []
            modules[module].append(file)
        
        # 分析每個模組
        coverages = []
        for module, module_files in modules.items():
            # 檢查是否有測試
            test_files = [f for f in module_files if "test" in f.relative_path.lower()]
            has_tests = len(test_files) > 0
            
            # 計算測試覆蓋率（簡化版：有測試檔案就算有覆蓋）
            test_coverage = 1.0 if has_tests else 0.0
            
            # 計算 TODO 數量
            module_path = Path(module) if module != "root" else Path(".")
            todos = self.todo_extractor.extract_from_directory(module_path)
            todo_count = len(todos)
            
            # 計算複雜度（簡化版：檔案數量）
            complexity_score = len(module_files) / 10.0  # 每 10 個檔案 = 1.0 複雜度
            
            coverages.append(ModuleCoverage(
                module_path=module,
                total_files=len(module_files),
                has_tests=has_tests,
                test_coverage=test_coverage,
                todo_count=todo_count,
                complexity_score=complexity_score,
            ))
        
        return coverages
    
    def identify_weaknesses(
        self,
        coverages: List[ModuleCoverage],
    ) -> List[SystemWeakness]:
        """
        識別系統弱點
        
        Args:
            coverages: 模組覆蓋率列表
        
        Returns:
            系統弱點列表
        """
        weaknesses = []
        
        for coverage in coverages:
            # 檢查沒有測試
            if not coverage.has_tests:
                weaknesses.append(SystemWeakness(
                    module=coverage.module_path,
                    weakness_type="no_tests",
                    severity="high",
                    description=f"模組 {coverage.module_path} 沒有測試檔案",
                    recommendation="建議新增測試檔案以確保程式碼品質",
                ))
            
            # 檢查 TODO 過多
            if coverage.todo_count > 5:
                weaknesses.append(SystemWeakness(
                    module=coverage.module_path,
                    weakness_type="high_todos",
                    severity="medium",
                    description=f"模組 {coverage.module_path} 有 {coverage.todo_count} 個 TODO",
                    recommendation="建議清理或完成待辦事項",
                ))
            
            # 檢查複雜度過高
            if coverage.complexity_score > 2.0:
                weaknesses.append(SystemWeakness(
                    module=coverage.module_path,
                    weakness_type="high_complexity",
                    severity="medium",
                    description=f"模組 {coverage.module_path} 複雜度較高（{coverage.complexity_score:.2f}）",
                    recommendation="建議重構以降低複雜度",
                ))
        
        return weaknesses
    
    def generate_insight_report(
        self,
        root: Optional[Path] = None,
    ) -> str:
        """
        產生洞察報告
        
        Args:
            root: 專案根目錄
        
        Returns:
            Markdown 格式的洞察報告
        """
        coverages = self.analyze_module_coverage(root)
        weaknesses = self.identify_weaknesses(coverages)
        
        lines = ["# 系統洞察報告\n"]
        
        # 模組覆蓋率
        lines.append("## 模組覆蓋率\n")
        lines.append("| 模組 | 檔案數 | 測試 | TODO | 複雜度 |")
        lines.append("|------|--------|------|------|--------|")
        
        for coverage in sorted(coverages, key=lambda x: x.module_path):
            test_status = "✅" if coverage.has_tests else "❌"
            lines.append(
                f"| {coverage.module_path} | {coverage.total_files} | "
                f"{test_status} | {coverage.todo_count} | {coverage.complexity_score:.2f} |"
            )
        
        # 系統弱點
        lines.append("\n## 系統弱點\n")
        
        if not weaknesses:
            lines.append("✅ 目前沒有發現明顯弱點。\n")
        else:
            for weakness in sorted(weaknesses, key=lambda x: (x.severity == "high", x.module)):
                severity_icon = "🔴" if weakness.severity == "high" else "🟡" if weakness.severity == "medium" else "🟢"
                lines.append(f"### {severity_icon} {weakness.module}")
                lines.append(f"- **類型**：{weakness.weakness_type}")
                lines.append(f"- **描述**：{weakness.description}")
                lines.append(f"- **建議**：{weakness.recommendation}\n")
        
        return "\n".join(lines)

