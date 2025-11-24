"""
專案掃描器：掃描專案中的程式碼與文件檔案
"""
import os
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class FileSummary:
    """檔案摘要資訊"""
    relative_path: str  # 相對於 repo root 的路徑
    extension: str  # 副檔名
    size_bytes: int  # 檔案大小（位元組）
    preview_lines: List[str]  # 檔案前 10 行，去掉換行


def find_repo_root(start_path: Optional[Path] = None) -> Path:
    """
    從指定路徑開始向上尋找 repo root
    
    Repo root 的判斷標準：
    1. 包含 .git 目錄
    2. 包含 pyproject.toml 檔案
    3. 如果都沒找到，使用 fallback: Path(__file__).resolve().parents[2]
    
    Args:
        start_path: 起始搜尋路徑，如果為 None 則使用當前檔案位置
    
    Returns:
        repo root 的 Path 物件
    """
    if start_path is None:
        # 使用當前檔案位置作為起始點
        start_path = Path(__file__).resolve()
    
    current = start_path if start_path.is_dir() else start_path.parent
    
    # 向上搜尋直到找到 repo root 或到達系統根目錄
    while current != current.parent:
        # 檢查是否包含 .git 目錄
        if (current / ".git").exists() and (current / ".git").is_dir():
            return current
        
        # 檢查是否包含 pyproject.toml
        if (current / "pyproject.toml").exists():
            return current
        
        current = current.parent
    
    # 如果都沒找到，使用 fallback
    fallback = Path(__file__).resolve().parents[2]
    return fallback


def scan_project(root: Optional[Path] = None) -> List[FileSummary]:
    """
    掃描專案中的檔案
    
    只處理以下副檔名的檔案：
    - .py
    - .yaml
    - .yml
    - .md
    - .txt
    
    會忽略以下目錄：
    - .git
    - .venv
    - __pycache__
    - .pytest_cache
    - .mypy_cache
    - .idea
    - .vscode
    - dist
    - build
    
    Args:
        root: 專案根目錄，如果為 None 則自動偵測
    
    Returns:
        檔案摘要列表
    """
    # 如果 root 為 None，自動偵測 repo root
    if root is None:
        root = find_repo_root()
    else:
        root = Path(root).resolve()
    
    # 允許的副檔名
    allowed_extensions = {".py", ".yaml", ".yml", ".md", ".txt"}
    
    # 要忽略的目錄名稱
    ignored_dirs = {
        ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
        ".idea", ".vscode", "dist", "build"
    }
    
    results: List[FileSummary] = []
    
    # 遞迴掃描所有檔案
    for file_path in root.rglob("*"):
        # 跳過非檔案項目
        if not file_path.is_file():
            continue
        
        # 計算相對路徑
        try:
            relative_path = str(file_path.relative_to(root))
            relative_path_parts = file_path.relative_to(root).parts
        except ValueError:
            # 如果無法計算相對路徑，跳過
            continue
        
        # 檢查路徑中是否包含要忽略的目錄
        if any(part in ignored_dirs for part in relative_path_parts):
            continue
        
        # 檢查副檔名
        if file_path.suffix.lower() not in allowed_extensions:
            continue
        
        # 取得檔案大小
        try:
            size_bytes = file_path.stat().st_size
        except OSError:
            size_bytes = 0
        
        # 讀取前 10 行作為預覽
        preview_lines: List[str] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f):
                    if i >= 10:
                        break
                    # 去掉換行符號
                    preview_lines.append(line.rstrip("\n\r"))
        except (OSError, UnicodeDecodeError):
            # 如果無法讀取，使用空列表
            preview_lines = []
        
        # 建立 FileSummary
        file_summary = FileSummary(
            relative_path=relative_path,
            extension=file_path.suffix.lower(),
            size_bytes=size_bytes,
            preview_lines=preview_lines
        )
        
        results.append(file_summary)
    
    return results


def write_markdown_report(files: List[FileSummary], output_path: Path) -> None:
    """
    產生 Markdown 格式的系統地圖報告
    
    Args:
        files: 檔案摘要列表
        output_path: 輸出檔案路徑
    """
    # 確保輸出目錄存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 依頂層資料夾分組
    groups: Dict[str, List[FileSummary]] = {}
    
    for file_summary in files:
        parts = file_summary.relative_path.split(os.sep)
        
        # 判斷 group key
        if len(parts) >= 2 and parts[0] == "jgod":
            # jgod 下的檔案，使用前兩層作為 group
            group_key = os.sep.join(parts[:2])
        elif len(parts) >= 1:
            # 其他檔案，使用第一層作為 group
            group_key = parts[0]
        else:
            # 根目錄下的檔案
            group_key = "root"
        
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(file_summary)
    
    # 產生 Markdown 內容
    lines = [
        "# J-GOD 系統地圖（自動生成）",
        "",
        "產生自：Code Intelligence Engine scanner  ",
        f"總檔案數：{len(files)}",
        "",
        "## 模組分佈",
        ""
    ]
    
    # 依 group 排序（root 放最後）
    sorted_groups = sorted(
        groups.items(),
        key=lambda x: (x[0] == "root", x[0])
    )
    
    for group_key, group_files in sorted_groups:
        # 標題
        lines.append(f"### {group_key}")
        lines.append("")
        
        # 列出檔案
        for file_summary in sorted(group_files, key=lambda x: x.relative_path):
            size_str = f"{file_summary.size_bytes:,} B"
            lines.append(f"- {os.path.basename(file_summary.relative_path)}  （{size_str}）")
        
        lines.append("")
    
    # 寫入檔案
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    # 解析命令列參數
    parser = argparse.ArgumentParser(
        description="掃描專案並產生系統地圖"
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        default=False,
        help="產生 Markdown 系統地圖報告"
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default="docs/JGOD_system_map.md",
        help="報告輸出路徑（預設：docs/JGOD_system_map.md）"
    )
    
    args = parser.parse_args()
    
    # 執行掃描
    files = scan_project()
    
    # 如果指定要寫報告
    if args.write_report:
        report_path = Path(args.report_path)
        write_markdown_report(files, report_path)
        print(f"已產生系統地圖：{report_path}")
    else:
        # 維持原本的行為：列出總檔案數 + 前幾個檔案清單
        print(f"總共掃描了 {len(files)} 個檔案\n")
        
        # 印出前 20 個檔案的簡單清單
        print("path ┊ ext ┊ size")
        print("-" * 60)
        
        for file_summary in files[:20]:
            # 格式化檔案大小
            size_str = f"{file_summary.size_bytes:,} B"
            print(f"{file_summary.relative_path} ┊ {file_summary.extension} ┊ {size_str}")
        
        if len(files) > 20:
            print(f"\n... 還有 {len(files) - 20} 個檔案未顯示")

