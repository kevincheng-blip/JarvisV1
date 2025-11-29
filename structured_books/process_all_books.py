#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: 批量處理 14 本 AI 知識庫文件，生成 STRUCTURED 版本
"""

import os
import re
from pathlib import Path

# 14 本書的列表（依檔名排序）
BOOKS = [
    "J-GOD 股市聖經系統1_AI知識庫版_v1.md",
    "J-GOD 邏輯系統補充_AI知識庫版_v1.md",
    "J-GOD_Book_Complete_v1_AI知識庫版_v1.md",
    "JGOD_STOCK_TRADING_BIBLE_v1_AI知識庫版_v1.md",
    "JGOD_原始開發藍圖_清整強化版_AI知識庫版_v1.md",
    "Path A  歷史回測撈取資料＋分析_AI知識庫版_v1.md",
    "滾動式分析_AI知識庫版_v1.md",
    "股市大自然萬物修復法則_AI知識庫版_v1.md",
    "股市聖經三_AI知識庫版_v1.md",
    "股市聖經二_AI知識庫版_v1.md",
    "股市聖經四_AI知識庫版_v1.md",
    "股神腦系統具體化設計_AI知識庫版_v1.md",
    "邏輯版操作說明書_AI知識庫版_v1.md",
    "雙引擎與自主演化閉環_AI知識庫版_v1.md",
]

def clean_and_structure_content(lines):
    """整理內容，建立清晰的結構"""
    output = []
    skip_empty = False
    
    for line in lines:
        stripped = line.strip()
        
        # 處理標題
        if re.match(r'^#+\s', stripped):
            output.append(f"\n{line}")
            skip_empty = False
            continue
        
        # 處理分隔線
        if stripped == '---' or stripped.startswith('________________'):
            if not skip_empty:
                output.append("\n")
            skip_empty = True
            continue
        
        # 處理標籤（保留但簡化）
        if stripped.startswith('[') and stripped.endswith(']'):
            # 標籤保留但不單獨成行，與下一行內容合併
            continue
        
        # 保留內容行
        if stripped:
            output.append(line)
            skip_empty = False
        elif not skip_empty:
            output.append("\n")
            skip_empty = True
    
    return output

def process_book(source_path, target_path):
    """處理單本書"""
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 讀取標題
        first_line = lines[0].strip() if lines else ""
        title = first_line.replace('# ', '').replace(' - AI 知識庫版 v1', ' - STRUCTURED 版')
        
        # 建立結構化內容
        structured_lines = []
        structured_lines.append(f"# {title}\n\n")
        structured_lines.append("> **說明**：本版本忠於原文，僅做結構化整理，建立清晰的章節標題與分類。\n\n")
        structured_lines.append("---\n\n")
        
        # 整理內容
        content = clean_and_structure_content(lines[1:])
        structured_lines.extend(content)
        
        # 寫入文件
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.writelines(structured_lines)
        
        return True, len(structured_lines)
    
    except Exception as e:
        return False, str(e)

def main():
    """主程序"""
    docs_dir = "docs"
    target_dir = "structured_books"
    
    print("=" * 60)
    print("Phase 1: 生成 14 本 STRUCTURED 版本")
    print("=" * 60)
    print()
    
    results = []
    
    for i, book in enumerate(BOOKS, 1):
        source = os.path.join(docs_dir, book)
        target_name = book.replace('_AI知識庫版_v1.md', '_AI知識庫版_v1_STRUCTURED.md')
        target = os.path.join(target_dir, target_name)
        
        if not os.path.exists(source):
            print(f"[{i:2d}/14] ❌ 跳過（文件不存在）：{book}")
            results.append((book, False, "文件不存在"))
            continue
        
        print(f"[{i:2d}/14] 處理：{book}")
        success, info = process_book(source, target)
        
        if success:
            print(f"      ✅ 完成：{info} 行")
            results.append((book, True, f"{info} 行"))
        else:
            print(f"      ❌ 失敗：{info}")
            results.append((book, False, info))
    
    print()
    print("=" * 60)
    print("處理完成摘要")
    print("=" * 60)
    
    success_count = sum(1 for _, ok, _ in results if ok)
    print(f"成功：{success_count}/14")
    print(f"失敗：{14 - success_count}/14")
    
    # 更新 README
    readme_path = os.path.join(target_dir, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        # 添加處理狀態
        status_section = "\n## Phase 1 處理狀態\n\n"
        for book, success, info in results:
            status = "✅" if success else "❌"
            status_section += f"- {status} {book.replace('_AI知識庫版_v1.md', '_AI知識庫版_v1_STRUCTURED.md')}\n"
        
        readme_content += status_section
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

if __name__ == "__main__":
    main()

