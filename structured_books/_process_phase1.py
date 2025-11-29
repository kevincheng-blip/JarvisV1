#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: 將 14 本 AI 知識庫文件生成 STRUCTURED 版本
只做結構化整理，不改變原文邏輯與意思
"""

import os
import re
from pathlib import Path

def process_book_structured(source_path, target_path):
    """處理單本書，生成 STRUCTURED 版本"""
    
    print(f"📘 處理：{os.path.basename(source_path)}")
    
    # 讀取原文
    with open(source_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 開始整理結構
    output_lines = []
    
    # 添加文件頭
    book_name = Path(source_path).stem.replace('_AI知識庫版_v1', '')
    output_lines.append(f"# {book_name} - STRUCTURED 版\n\n")
    output_lines.append("> **說明**：本版本忠於原文，僅做結構化整理，建立清晰的章節標題與分類。\n\n")
    output_lines.append("---\n\n")
    
    # 處理每一行，整理結構
    current_section = ""
    current_subsection = ""
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 跳過空行和分隔線（暫時）
        if not stripped or stripped.startswith('---'):
            continue
        
        # 處理標題（H1-H3）
        if stripped.startswith('# '):
            output_lines.append(f"\n{stripped}\n")
            current_section = stripped
        elif stripped.startswith('## '):
            output_lines.append(f"\n{stripped}\n")
            current_subsection = stripped
        elif stripped.startswith('### '):
            output_lines.append(f"\n{stripped}\n")
        elif stripped.startswith('#### '):
            output_lines.append(f"\n{stripped}\n")
        
        # 處理標籤分類（保留原文，但整理格式）
        elif stripped.startswith('[') and stripped.endswith(']'):
            tag = stripped
            # 保留標籤，但簡化顯示
            continue  # 暫時跳過標籤行，之後再處理
        
        # 處理一般內容（保留原文）
        else:
            output_lines.append(line)
    
    # 寫入目標文件
    with open(target_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    print(f"✅ 完成：{os.path.basename(target_path)} ({len(output_lines)} 行)")

if __name__ == "__main__":
    # 處理第一本書作為測試
    source = "docs/J-GOD 股市聖經系統1_AI知識庫版_v1.md"
    target = "structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_STRUCTURED.md"
    
    if os.path.exists(source):
        process_book_structured(source, target)
    else:
        print(f"❌ 文件不存在：{source}")

