#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
處理 股市聖經二.txt 和 股市聖經三.txt，建立 AI 知識庫版
"""

import re

def classify_content(line):
    """判斷內容類型並加上標籤"""
    line = line.strip()
    if not line or line.startswith('=') or line.startswith('→'):
        return None
    
    # 檢測程式碼
    if '```' in line or 'Python' in line or 'class ' in line or 'def ' in line or 'import ' in line or 'from ' in line or '->' in line or (': ' in line and ('str' in line or 'int' in line or 'float' in line or 'bool' in line or 'Dict' in line or 'List' in line)):
        return '[CODE]'
    
    # 檢測公式
    if '=' in line and ('ROE' in line or 'F_' in line or 'O_' in line or '\\' in line or 'λ' in line or 'β' in line or 'α' in line or 'Z-score' in line or 'VWAP' in line or 'Spread' in line):
        return '[FORMULA]'
    
    # 檢測表格
    if '\t' in line and ('維度' in line or '階段' in line or '說明' in line or '用途' in line or '|' in line or '名稱' in line or '目標' in line or '核心' in line):
        return '[TABLE]'
    
    # 檢測規則
    if any(keyword in line for keyword in ['如果', '若', '當', '則', '應該', '必須', '需要', '規則', '條件', 'IF', 'THEN', '→', '觸發', '一旦', '只要']):
        return '[RULE]'
    
    # 檢測系統架構
    if any(keyword in line for keyword in ['系統', '架構', '模組', '引擎', '流程', '階段', 'Blueprint', 'Engine', '策略', '方法', '模態', 'Cycle', 'Principle', '因子', 'Factor']):
        return '[STRUCTURE]'
    
    # 檢測概念定義
    if any(keyword in line for keyword in ['定義', '概念', '特徵', '原則', '邏輯', '哲學', '價值觀', '思維', '理論', '核心', '目的', '目標', 'Alpha', 'Beta', '巴菲特', 'Citadel', 'Medallion']):
        return '[CONCEPT]'
    
    # 預設為註解
    return '[NOTE]'

def process_file_ai_kb(input_file, output_file):
    """建立 AI 知識庫版"""
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    output_lines = [
        f"# {os.path.basename(input_file).replace('.txt', '')} - AI 知識庫版 v1\n",
        "\n",
        "> **重要說明**：本文件為 AI 知識庫格式，每段內容都已標記分類標籤，可直接被 AI 模型解析、轉換為 JSON、向量化或規則引擎使用。\n",
        "> \n",
        f"> **原始文件**：`{os.path.basename(input_file)}`（未修改）\n",
        "\n",
        "---\n",
        "\n",
        "## 文件說明\n",
        "\n",
        "[NOTE]\n",
        "本文件是 J-GOD 股神作戰系統的核心大腦來源之一，所有內容均完整保留，僅進行結構化分類標籤，未刪除或修改任何技術內容。\n",
        "\n",
        "---\n",
        "\n"
    ]
    
    current_tag = None
    buffer = []
    
    for i, line in enumerate(lines):
        if (i + 1) % 500 == 0:
            print(f"  處理中... {i+1} 行")
        
        tag = classify_content(line)
        
        if tag:
            if current_tag != tag:
                if buffer:
                    output_lines.append('\n'.join(buffer) + '\n\n')
                    buffer = []
                output_lines.append(f"{tag}\n")
                current_tag = tag
            buffer.append(line.rstrip())
        else:
            if buffer:
                output_lines.append('\n'.join(buffer) + '\n\n')
                buffer = []
                current_tag = None
            if line.strip():
                output_lines.append(line)
    
    if buffer:
        output_lines.append('\n'.join(buffer) + '\n\n')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    print(f"✓ AI 知識庫版已建立：{output_file}")
    print(f"  原始行數: {len(lines)}")
    print(f"  輸出行數: {len(output_lines)}")

if __name__ == '__main__':
    import os
    
    # 處理股市聖經二
    print("開始處理 股市聖經二.txt...")
    input_file1 = '/Users/kevincheng/JarvisV1/docs/股市聖經二.txt'
    output_file1 = '/Users/kevincheng/JarvisV1/docs/股市聖經二_AI知識庫版_v1.md'
    process_file_ai_kb(input_file1, output_file1)
    
    # 處理股市聖經三
    print("\n開始處理 股市聖經三.txt...")
    input_file2 = '/Users/kevincheng/JarvisV1/docs/股市聖經三.txt'
    output_file2 = '/Users/kevincheng/JarvisV1/docs/股市聖經三_AI知識庫版_v1.md'
    process_file_ai_kb(input_file2, output_file2)
    
    print("\n✓ 所有處理完成！")

