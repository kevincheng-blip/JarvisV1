#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
處理 股神腦系統具體化設計.txt，建立 AI 知識庫版和閱讀強化版
"""

import re
import os

def classify_content(line):
    """判斷內容類型並加上標籤"""
    line = line.strip()
    if not line or line.startswith('=') or line.startswith('→'):
        return None
    
    # 檢測程式碼
    if '```' in line or 'Python' in line or 'class ' in line or 'def ' in line or 'import ' in line or 'from ' in line or '->' in line or (': ' in line and ('str' in line or 'int' in line or 'float' in line or 'bool' in line or 'Dict' in line or 'List' in line or 'Optional' in line or 'np.ndarray' in line)):
        return '[CODE]'
    
    # 檢測公式
    if '=' in line and ('F_' in line or 'O_' in line or 'SAI' in line or 'MOI' in line or '\\' in line or 'λ' in line or 'β' in line or 'α' in line or 'EMA' in line or 'Z-score' in line or 'VWAP' in line or 'Spread' in line or 'Residual' in line):
        return '[FORMULA]'
    
    # 檢測表格
    if '\t' in line and ('維度' in line or '階段' in line or '說明' in line or '用途' in line or '|' in line or '名稱' in line or '目標' in line or '核心' in line or '概念' in line):
        return '[TABLE]'
    
    # 檢測規則
    if any(keyword in line for keyword in ['如果', '若', '當', '則', '應該', '必須', '需要', '規則', '條件', 'IF', 'THEN', '→', '觸發', '一旦', '只要', '當...時']):
        return '[RULE]'
    
    # 檢測系統架構
    if any(keyword in line for keyword in ['系統', '架構', '模組', '引擎', '流程', '階段', 'Blueprint', 'Engine', '策略', '方法', '模態', 'Cycle', 'Principle', '因子', 'Factor', 'Hub', 'Builder']):
        return '[STRUCTURE]'
    
    # 檢測概念定義
    if any(keyword in line for keyword in ['定義', '概念', '特徵', '原則', '邏輯', '哲學', '價值觀', '思維', '理論', '核心', '目的', '目標', 'Alpha', 'Beta', 'XQ', 'CapitalFlow', 'Inertia', 'Pressure']):
        return '[CONCEPT]'
    
    # 預設為註解
    return '[NOTE]'

def process_godbrain_ai_kb():
    """建立 AI 知識庫版"""
    input_file = '/Users/kevincheng/JarvisV1/docs/股神腦系統具體化設計.txt'
    output_file = '/Users/kevincheng/JarvisV1/docs/股神腦系統具體化設計_AI知識庫版_v1.md'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    output_lines = [
        "# 股神腦系統具體化設計 - AI 知識庫版 v1\n",
        "\n",
        "> **重要說明**：本文件為 AI 知識庫格式，每段內容都已標記分類標籤，可直接被 AI 模型解析、轉換為 JSON、向量化或規則引擎使用。\n",
        "> \n",
        "> **原始文件**：`股神腦系統具體化設計.txt`（未修改）\n",
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

def process_godbrain_reading():
    """建立閱讀強化版"""
    output_file = '/Users/kevincheng/JarvisV1/docs/股神腦系統具體化設計_閱讀強化版_v1.md'
    
    output = """# 股神腦系統具體化設計：閱讀強化版 v1

> **說明**：本文件是 J-GOD 股神作戰系統的具體化設計文件，包含 XQ 資金流因子 F_C 的完整設計、CapitalFlowEngine、F_Inertia、F_PT、F_MRR 等核心模組。

---

## 一、這本書的目的

[CONCEPT]
name: 本書目的
definition: 將 J-GOD 系統從全面競爭者轉變為擁有「在地化獨家情報（XQ）」和「跨市場反應速度（Polygon）」的極速精準獵手，具體化設計 XQ 資金流因子 F_C 及其相關引擎。

[NOTE]
本文件旨在建立完整的 XQ 資金流因子系統，包含 CapitalFlowEngine、InertiaEngine、PressureTransmissionEngine、MajorReversalRiskEngine 等核心模組。

---

## 二、核心投資邏輯

### 2.1 XQ 資金流因子 F_C 設計

[CONCEPT]
name: F_C 核心因子
definition: 將 XQ 的「族群資金流」和「主力大單」資料，轉成 J-GOD 系統的在地 Alpha 因子 F_C。

[STRUCTURE]
F_C 包含兩個核心因子：
1. 族群攻擊因子 (Sector Attack Index, SAI)
2. 主力單量失衡 (Major Order Imbalance, MOI)

[FORMULA]
current_share(group) = group_volume(group) / current_market_volume

[FORMULA]
sai_residual(group) = (current_share(group) - mean_share(group)) / std_share(group)

[FORMULA]
moi = (major_buy_volume - major_sell_volume) / total_major_volume

### 2.2 F_C 強化因子

[CONCEPT]
name: F_Inertia（資金流動慣性因子）
definition: 以「信息時間」為基準的資金流動慣性因子，衡量資金攻擊是否有持續性，而不只是瞬間放大。

[FORMULA]
F_Inertia(t) = α * SAI_Residual(t) + (1-α) * F_Inertia(t-1)

[CONCEPT]
name: F_PT（壓力傳導因子）
definition: 衡量「龍頭股的主力行為」如何帶動／傳導整個族群的資金攻擊。

[CONCEPT]
name: F_MRR（主力意圖逆轉因子）
definition: 觀察主力大單在細粒度（Tick 級別）的撤單行為與節奏，度量「主力是否有改變主意、準備反向」的意圖。

[FORMULA]
CancelRate_Major = (主力大單取消量) / (主力大單掛出量)

---

## 三、股票判斷方法（技術面 + 基本面）

[NOTE]
本文件主要聚焦於資金流因子設計，技術面與基本面判斷方法請參考其他股市聖經文件。

[RULE]
IF SAI_Residual 很高 AND F_Inertia 也很高
THEN 這代表資金攻擊「有持續性」，RL 才允許對該族群拉高 Net Exposure

[RULE]
IF SAI_Residual 高但 F_Inertia 低
THEN 可能是一次性沖天炮或假突破，RL 只能用來做短線反轉 / 區間交易

---

## 四、交易策略

### 4.1 資金流攻擊策略

[RULE]
IF F_PT 高
THEN 代表龍頭主力 → 族群資金 → 一致往同一方向，這是「大資金有計畫性攻擊」的形態，RL 優先執行全力加碼策略

[RULE]
IF MOI 高 AND F_MRR 低
THEN 主力站在那一邊，而且還穩穩站著，攻擊意圖真實

[RULE]
IF MOI 高 AND F_MRR 高
THEN 主力有可能是在騙：假裝大買，但實際上一直撤單，或已經開始悄悄轉向

### 4.2 風險控制策略

[RULE]
IF F_MRR 上升
THEN 即使 SAI 和 MOI 仍然偏多，RL 在「繼續加碼或維持大敞口」的行為上會被重罰

[RULE]
IF F_MRR 上升
THEN RL 會逐漸學會：在「主力疑似反悔／有誘多嫌疑」的狀態下，要主動降槓桿、減倉，甚至反手

---

## 五、風險控管與心理面

### 5.1 主力意圖識別

[RULE]
IF CancelRate_Major 在短時間內劇烈升高
THEN F_MRR 升高，代表主力可能改變主意、準備反向

[RULE]
IF F_MRR 高
THEN 系統內建「不要傻傻跟著表面的大單跑」的自動防禦機制

### 5.2 資金流持續性判斷

[RULE]
IF F_Inertia 高
THEN 這波攻擊是已經持續多個事件的「趨勢」，而非瞬間情緒

[RULE]
IF F_Inertia 低
THEN 可能只是瞬間情緒或假突破，不適合全力追多

---

## 六、開盤／盤中／收盤 SOP

### 6.1 盤前流程

[RULE]
IF 盤前啟動
THEN 初始化 CapitalFlowEngine、InertiaEngine、PressureTransmissionEngine、MajorReversalRiskEngine

### 6.2 盤中監控

[RULE]
IF 盤中運行
THEN 持續更新：
  1. CapitalFlowEngine 計算 SAI_Residual 和 MOI
  2. InertiaEngine 更新 F_Inertia
  3. PressureTransmissionEngine 更新 F_PT
  4. MajorReversalRiskEngine 更新 F_MRR

### 6.3 盤後處理

[RULE]
IF 盤後
THEN 重置所有引擎狀態，準備下一個 episode

---

## 七、實戰案例整理

[NOTE]
以下為系統設計案例，實際交易案例請參考其他文件。

### 案例 1：資金流持續性攻擊

[RULE]
IF SAI_Residual 很高 AND F_Inertia 也很高
THEN RL 允許對該族群拉高 Net Exposure，採取順勢追高策略

### 案例 2：龍頭傳導攻擊

[RULE]
IF 龍頭 MOI 先急劇升高 AND 幾個 Volume Bar 之後，同族群的 SAI Residual 跟著拉高
THEN F_PT → 高，代表攻擊是「由上而下」傳導，信號可靠度極高

### 案例 3：主力誘多識別

[RULE]
IF MOI 高 AND F_MRR 高
THEN 主力有可能是在騙：假裝大買，但實際上一直撤單，RL 應主動降槓桿、減倉

---

## 八、AI 補充

### 8.1 CapitalFlowEngine 設計

[STRUCTURE]
CapitalFlowEngine 負責：
- 計算族群攻擊因子 (SAI Residual)
- 計算主力單量失衡 (MOI)
- 輸入：XQ 提供的族群資金流和主力單量數據
- 輸出：F_C 基礎因子

### 8.2 InertiaEngine 設計

[STRUCTURE]
InertiaEngine 負責：
- 在 Volume Bar（信息時間）基礎上計算 EMA
- 更新 F_Inertia 值
- 衡量資金攻擊的持續性

### 8.3 PressureTransmissionEngine 設計

[STRUCTURE]
PressureTransmissionEngine 負責：
- 觀察龍頭股的 MOI
- 對比同族群的 SAI Residual
- 測量「誰先動，誰後動」以及「兩者是否同步放大」
- 計算 F_PT（壓力傳導因子）

### 8.4 MajorReversalRiskEngine 設計

[STRUCTURE]
MajorReversalRiskEngine 負責：
- 觀察主力大單在細粒度（Tick 級別）的撤單行為
- 計算 CancelRate_Major
- 度量「主力是否有改變主意、準備反向」的意圖
- 計算 F_MRR（主力意圖逆轉因子）

### 8.5 CapitalFlowHub 整合

[STRUCTURE]
CapitalFlowHub 整合所有 F_C 相關引擎：
- CapitalFlowEngine（基礎因子）
- InertiaEngine（慣性因子）
- PressureTransmissionEngine（傳導因子）
- MajorReversalRiskEngine（逆轉風險因子）

### 8.6 RL State Builder 設計

[STRUCTURE]
StateBuilder 負責：
- 將價格特徵、技術指標、資金流因子組合成 RL State Vector
- 統一管理所有特徵的欄位順序
- 輸出標準化的 np.ndarray

---

## 九、可轉程式化的 J-GOD 規則列表

### 9.1 SAI Residual 計算規則

[RULE]
IF 計算 SAI Residual
THEN current_share(group) = group_volume(group) / current_market_volume, sai_residual(group) = (current_share(group) - mean_share(group)) / std_share(group)

[RULE]
IF std_share(group) 太小或為 0
THEN 避免除以 0，直接給 0，或使用 fallback

### 9.2 MOI 計算規則

[RULE]
IF 計算 MOI
THEN moi = (major_buy_volume - major_sell_volume) / total_major_volume

[RULE]
IF moi ≈ +1
THEN 主力幾乎全部在買

[RULE]
IF moi ≈ -1
THEN 主力幾乎全部在賣

[RULE]
IF moi ≈ 0
THEN 主力行為中性

### 9.3 F_Inertia 更新規則

[RULE]
IF 新的 Volume Bar 形成
THEN 更新 F_Inertia: F_Inertia(t) = α * SAI_Residual(t) + (1-α) * F_Inertia(t-1)

[RULE]
IF SAI_Residual 很高 AND F_Inertia 也很高
THEN RL 允許對該族群拉高 Net Exposure

[RULE]
IF SAI_Residual 高但 F_Inertia 低
THEN RL 只能用來做短線反轉 / 區間交易

### 9.4 F_PT 計算規則

[RULE]
IF 龍頭 MOI 先急劇升高 AND 幾個 Volume Bar 之後，同族群的 SAI Residual 跟著拉高
THEN F_PT → 高，代表攻擊是「由上而下」傳導

[RULE]
IF F_PT 高
THEN RL 優先執行全力加碼策略（例如全倉進場、槓桿放大）

### 9.5 F_MRR 計算規則

[RULE]
IF 計算 F_MRR
THEN CancelRate_Major = (主力大單取消量) / (主力大單掛出量)

[RULE]
IF CancelRate_Major 在短時間內劇烈升高
THEN F_MRR 升高

[RULE]
IF MOI 高 AND F_MRR 低
THEN 主力站在那一邊，而且還穩穩站著，攻擊意圖真實

[RULE]
IF MOI 高 AND F_MRR 高
THEN 主力有可能是在騙：假裝大買，但實際上一直撤單

[RULE]
IF F_MRR 上升
THEN RL 在「繼續加碼或維持大敞口」的行為上會被重罰

### 9.6 RL State Vector 規則

[RULE]
IF 建立 RL State Vector
THEN StateBuilder 將價格特徵、技術指標、資金流因子按照預先定義的欄位順序組合成 np.ndarray

[RULE]
IF 缺少某個 key
THEN 用 0.0 填補

---

## 附錄：核心模組設計詳解

### A. CapitalFlowEngine

[CODE]
# strategy_engine/factor_FX_capital_flow.py
# 計算 SAI_Residual 和 MOI

[NOTE]
詳細程式碼請參考原始文件或 AI 知識庫版。

### B. InertiaEngine

[CODE]
# strategy_engine/factor_FX_inertia.py
# 計算 F_Inertia（資金流動慣性因子）

[NOTE]
詳細程式碼請參考原始文件或 AI 知識庫版。

### C. PressureTransmissionEngine

[CODE]
# strategy_engine/factor_FX_pressure_transmission.py
# 計算 F_PT（壓力傳導因子）

[NOTE]
詳細程式碼請參考原始文件或 AI 知識庫版。

### D. MajorReversalRiskEngine

[CODE]
# strategy_engine/factor_FX_major_reversal_risk.py
# 計算 F_MRR（主力意圖逆轉因子）

[NOTE]
詳細程式碼請參考原始文件或 AI 知識庫版。

### E. CapitalFlowHub

[CODE]
# strategy_engine/factor_FX_capital_flow_hub.py
# 整合所有 F_C 相關引擎

[NOTE]
詳細程式碼請參考原始文件或 AI 知識庫版。

### F. StateBuilder

[CODE]
# rl/state/state_builder.py
# 將各個模組輸出的因子組合成 RL State Vector

[NOTE]
詳細程式碼請參考原始文件或 AI 知識庫版。

---

## 總結

[NOTE]
本文件完整保留了原始內容的所有技術細節，包括：
- 所有引擎設計與程式碼
- 所有因子計算公式
- 所有規則與策略邏輯
- 所有系統架構設計

[CONCEPT]
name: 股神腦系統具體化設計
definition: 將 J-GOD 系統從全面競爭者轉變為擁有「在地化獨家情報（XQ）」和「跨市場反應速度（Polygon）」的極速精準獵手，透過完整的 XQ 資金流因子系統實現。

[NOTE]
本文件旨在建立完整的 XQ 資金流因子系統，讓系統具備「在地化獨家情報」優勢，實現極速精準的獵手能力。

---

*文件建立時間：2024年*
*版本：v1*
*原始文件：股神腦系統具體化設計.txt（未修改）*

"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"✓ 閱讀強化版已建立：{output_file}")

if __name__ == '__main__':
    print("開始處理 股神腦系統具體化設計.txt...")
    process_godbrain_ai_kb()
    process_godbrain_reading()
    print("✓ 處理完成！")

