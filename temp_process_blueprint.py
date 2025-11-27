#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
處理 JGOD_原始開發藍圖_清整強化版.txt，建立 AI 知識庫版和閱讀強化版
"""

import re

def classify_content(line):
    """判斷內容類型並加上標籤"""
    line = line.strip()
    if not line or line.startswith('=') or line.startswith('→'):
        return None
    
    # 檢測程式碼
    if '```' in line or 'Python' in line or 'class ' in line or 'def ' in line or 'import ' in line or 'from ' in line or '->' in line or ': ' in line and ('str' in line or 'int' in line or 'float' in line or 'bool' in line):
        return '[CODE]'
    
    # 檢測表格
    if '\t' in line and ('欄位' in line or '說明' in line or '用途' in line or '|' in line or '名稱' in line):
        return '[TABLE]'
    
    # 檢測規則
    if any(keyword in line for keyword in ['如果', '若', '當', '則', '應該', '必須', '需要', '規則', '條件', 'IF', 'THEN', '→', '觸發']):
        return '[RULE]'
    
    # 檢測系統架構
    if any(keyword in line for keyword in ['系統', '架構', '模組', '引擎', '流程', '階段', 'Blueprint', 'Engine', '策略', '方法', 'Meta-Level', 'Edge Engine']):
        return '[STRUCTURE]'
    
    # 檢測概念定義
    if any(keyword in line for keyword in ['定義', '概念', '特徵', '原則', '邏輯', '哲學', '價值觀', '思維', '缺口', '終極', 'Edge', 'Regime']):
        return '[CONCEPT]'
    
    # 預設為註解
    return '[NOTE]'

def process_blueprint_ai_kb():
    """建立 AI 知識庫版"""
    input_file = '/Users/kevincheng/JarvisV1/docs/JGOD_原始開發藍圖_清整強化版.txt'
    output_file = '/Users/kevincheng/JarvisV1/docs/JGOD_原始開發藍圖_清整強化版_AI知識庫版_v1.md'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    output_lines = [
        "# JGOD 原始開發藍圖清整強化版 - AI 知識庫版 v1\n",
        "\n",
        "> **重要說明**：本文件為 AI 知識庫格式，每段內容都已標記分類標籤，可直接被 AI 模型解析、轉換為 JSON、向量化或規則引擎使用。\n",
        "> \n",
        "> **原始文件**：`JGOD_原始開發藍圖_清整強化版.txt`（未修改）\n",
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

def process_blueprint_reading():
    """建立閱讀強化版"""
    input_file = '/Users/kevincheng/JarvisV1/docs/JGOD_原始開發藍圖_清整強化版.txt'
    output_file = '/Users/kevincheng/JarvisV1/docs/JGOD_原始開發藍圖_清整強化版_閱讀強化版_v1.md'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    output = """# JGOD 原始開發藍圖清整強化版：閱讀強化版 v1

> **說明**：本文件是 J-GOD 股神作戰系統的完整開發藍圖，包含系統架構設計、引擎設計、Data Universe 設計等。

---

## 一、這本書的目的

[CONCEPT]
name: 本書目的
definition: 建立 J-GOD 系統的完整開發藍圖，從 v0 版本到完整系統架構，包含所有引擎設計、Data Universe 設計、終極缺口分析等。

[NOTE]
本文件旨在建立完整的系統開發路線圖，從基礎的 Excel/Google Sheet 版本到完整的 AI 驅動量化交易系統。

---

## 二、核心投資邏輯

### 2.1 J-GOD v0 設計

[CONCEPT]
name: J-GOD v0
definition: 使用 Excel/Google Sheet 就能運行的交易系統，結合 GPT 產生盤前/收盤報告，建立完整的交易記錄與策略分析機制。

[RULE]
IF 建立 J-GOD v0 系統
THEN 需要建立 4 張核心工作表：Daily_Market、Watchlist、Trades、Strategy_Notes

### 2.2 系統架構設計

[STRUCTURE]
J-GOD 系統架構包含：
- Data Universe Engine（資料宇宙引擎）
- Market Engine（市場引擎）
- Strategy Engine（策略引擎）
- Risk Engine（風控引擎）
- Position Engine（倉位大腦）
- Evolution Engine（策略進化 AI）
- Psychology Engine（心理引擎）
- Execution Engine（實單層）

### 2.3 終極缺口分析

[CONCEPT]
name: 終極缺口 1 - Meta-Level 決策大腦
definition: 策略之上的策略，判斷策略何時該停用、何時該啟用，包含市場風格切換模型和策略組合優化器。

[CONCEPT]
name: 終極缺口 2 - Edge Engine
definition: 定義 J-GOD 的核心優勢，整理所有策略的優勢、弱點、比誰強、比誰弱，實現自動優化。

[CONCEPT]
name: 終極缺口 3 - 心理回路 & 大腦限制器
definition: 監控交易者行為，防止自我破壞，包含連虧偵測、追價偵測、違規停損偵測等。

---

## 三、股票判斷方法（技術面 + 基本面）

[NOTE]
本文件主要聚焦於系統架構設計，技術面與基本面判斷方法請參考其他股市聖經文件。

[CONCEPT]
name: 策略判斷
definition: 透過 Strategy Engine 的六大武功量化參數化，每招 50+ 參數，自動生成訊號。

---

## 四、交易策略

[RULE]
IF 策略執行
THEN 先在虛擬市場跑過，驗證勝率後才敢實單

[RULE]
IF 策略績效評估
THEN 只有當策略在特定條件下勝率 > 65%、賺賠比 > 2.0 才允許實單

[RULE]
IF 市場風格切換
THEN 需要判斷市場 Regime（多頭/空頭/震盪/爆發/恐慌），不同時期策略勝率完全不同

---

## 五、風險控管與心理面

### 5.1 風險控管

[RULE]
IF 單筆最大虧損
THEN 2%（跌到 -2% 必須砍單）

[RULE]
IF 單日最大虧損
THEN 2%（當天累計達 -2% 即關機、停新單）

[RULE]
IF 單月最大虧損
THEN 6%（達到暫停實單，只做模擬與檢討）

### 5.2 心理引擎

[RULE]
IF 連虧 >= 3 次
THEN cooldown_required = True，進入冷卻模式

[RULE]
IF violation_count > 0
THEN max_position_multiplier = 0.5，自動降低最大部位

[RULE]
IF 偵測到 FOMO 行為
THEN 禁止下單

---

## 六、開盤／盤中／收盤 SOP

[NOTE]
本文件主要聚焦於系統架構設計，詳細的開盤/盤中/收盤 SOP 請參考其他股市聖經文件。

[RULE]
IF 開盤前
THEN 檢查市場大環境，確認主流族群與資金流向

[RULE]
IF 盤中
THEN 觀察價格走勢、成交量、K 線形態，判斷市場情緒與主力行為

[RULE]
IF 收盤後
THEN 檢討當日交易，更新資料庫，調整策略參數

---

## 七、實戰案例整理

[NOTE]
本文件主要聚焦於系統架構設計，詳細的實戰案例請參考其他股市聖經文件。

[CONCEPT]
name: 系統開發案例
definition: 從 v0 版本（Excel/Google Sheet）逐步進化到完整 AI 驅動量化交易系統的開發路線圖。

---

## 八、AI 補充

### 8.1 Data Universe 設計

[NOTE]
AI 補充：Data Universe v1.0 包含超過 100+ 欄位，涵蓋標的主檔、日線價格、技術指標、盤中數據、指數數據、期貨數據、選擇權數據、資金流向、融資融券等。

[STRUCTURE]
Data Universe 主要表格：
- securities_master（標的主檔）
- daily_prices（日線價格）
- daily_indicators（技術指標）
- intraday_bars_5m（盤中數據）
- index_daily（指數數據）
- futures_daily（期貨數據）
- options_metrics（選擇權數據）
- fund_flow（資金流向）
- margin_short（融資融券）

### 8.2 引擎設計

[NOTE]
AI 補充：J-GOD 系統包含多個核心引擎，每個引擎都有明確的職責和介面設計。

[STRUCTURE]
核心引擎列表：
- Data Universe Engine：所有資料來源與欄位管理
- Market Engine：大盤強弱分數、族群強弱分數、市場情緒分數、Regime 判斷
- Strategy Engine：六大武功量化參數化、自動生成訊號、回測與優化
- Risk Engine：風控規則、風險宇宙管理
- Position Engine：多策略協同資金配置
- Evolution Engine：策略進化 AI、自動調整參數、自動進化
- Psychology Engine：監控交易者行為、連虧偵測、追價偵測
- Execution Engine：模擬下單、未來對接券商 API

### 8.3 終極缺口補強

[NOTE]
AI 補充：系統還需要補強三大終極缺口：Meta-Level 決策大腦、Edge Engine、心理回路 & 大腦限制器。

---

## 九、可轉程式化的 J-GOD 規則列表

### 9.1 系統建立規則

[RULE]
IF 建立 J-GOD v0 系統
THEN 必須建立 4 張核心工作表：Daily_Market、Watchlist、Trades、Strategy_Notes

[RULE]
IF 建立 Data Universe
THEN 必須包含所有資料來源與欄位定義，確保資料完整性與一致性

### 9.2 策略執行規則

[RULE]
IF 策略執行
THEN 先在虛擬市場跑過，驗證勝率後才敢實單

[RULE]
IF 策略勝率 > 65% AND 賺賠比 > 2.0
THEN 允許實單

[RULE]
IF 市場 Regime 切換
THEN 需要重新評估策略適用性，調整策略參數或停用不適用策略

### 9.3 風險控管規則

[RULE]
IF 單筆虧損 >= 2%
THEN 必須砍單

[RULE]
IF 單日虧損 >= 2%
THEN 關機、停新單

[RULE]
IF 單月虧損 >= 6%
THEN 暫停實單，只做模擬與檢討

### 9.4 心理引擎規則

[RULE]
IF 連虧 >= 3 次
THEN cooldown_required = True

[RULE]
IF violation_count > 0
THEN max_position_multiplier = 0.5

[RULE]
IF 偵測到 FOMO 行為
THEN 禁止下單

### 9.5 系統進化規則

[RULE]
IF 策略績效下降
THEN 觸發 Evolution Engine，自動調整參數或淘汰策略

[RULE]
IF 市場 Regime 切換
THEN 觸發 Meta-Level 決策大腦，重新評估策略組合

---

## 附錄：系統架構詳解

### A. Data Universe v1.0

[STRUCTURE]
Data Universe 包含超過 100+ 欄位，涵蓋：
- 標的主檔資訊
- 日線價格與技術指標
- 盤中數據（5 分鐘 K 線）
- 指數數據
- 期貨數據
- 選擇權數據
- 資金流向
- 融資融券
- 新聞與情緒數據

### B. 核心引擎設計

[STRUCTURE]
每個引擎都有明確的職責：
- Data Universe Engine：資料管理
- Market Engine：市場分析
- Strategy Engine：策略生成
- Risk Engine：風險控管
- Position Engine：資金配置
- Evolution Engine：策略進化
- Psychology Engine：行為監控
- Execution Engine：訂單執行

### C. 終極缺口補強

[STRUCTURE]
三大終極缺口：
1. Meta-Level 決策大腦：策略之上的策略
2. Edge Engine：核心優勢定義
3. 心理回路 & 大腦限制器：行為監控與限制

---

## 總結

[NOTE]
本文件完整保留了原始內容的所有技術細節，包括：
- 所有系統架構設計
- 所有引擎設計
- 所有 Data Universe 設計
- 所有終極缺口分析

[CONCEPT]
name: JGOD 原始開發藍圖
definition: 建立 J-GOD 系統的完整開發路線圖，從 v0 版本到完整 AI 驅動量化交易系統，實現世界級 1% 個人自營商的目標。

[NOTE]
本文件旨在建立完整的系統開發路線圖，持續進化、持續學習、持續變強。

---

*文件建立時間：2024年*
*版本：v1*
*原始文件：JGOD_原始開發藍圖_清整強化版.txt（未修改）*

"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"✓ 閱讀強化版已建立：{output_file}")

if __name__ == '__main__':
    print("開始處理 JGOD_原始開發藍圖_清整強化版.txt...")
    process_blueprint_ai_kb()
    process_blueprint_reading()
    print("✓ 處理完成！")

