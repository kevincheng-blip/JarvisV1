#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 & 3: 生成 ENHANCED 和 CORRECTED 版本
批量處理所有14本書
"""

import os
import re
from pathlib import Path

def enhance_structured_content(structured_lines):
    """
    Phase 2: 在 STRUCTURED 基礎上添加程序化說明和白話注解
    將複雜推導拆成更清楚的步驟
    """
    enhanced = []
    i = 0
    
    while i < len(structured_lines):
        line = structured_lines[i]
        stripped = line.strip()
        
        enhanced.append(line)
        
        # 檢測策略規則段落，添加程序化說明
        if re.search(r'Rules_Entry|進場條件|Rules_Exit|出場條件|Stop_Loss|停損', stripped, re.IGNORECASE):
            # 找到策略規則段落，添加註解
            enhanced.append("\n**[程式化說明]**\n")
            enhanced.append("此規則可轉為 Python 函數式判斷：\n\n")
            enhanced.append("```python\n")
            enhanced.append("# 示例結構：\n")
            enhanced.append("# def check_entry_condition(data, indicators):\n")
            enhanced.append("#     return condition_1 and condition_2 and condition_3\n")
            enhanced.append("```\n\n")
            enhanced.append("**[白話註解]**\n")
            enhanced.append("這段規則的意思是：當滿足所有條件時，系統才會產生進場訊號。\n\n")
        
        # 檢測公式或計算段落
        if re.search(r'計算|公式|score|分數|平均|mean|std', stripped, re.IGNORECASE):
            enhanced.append("\n**[程式化說明]**\n")
            enhanced.append("此計算可用 NumPy/Pandas 實現：\n\n")
            enhanced.append("```python\n")
            enhanced.append("# import numpy as np\n")
            enhanced.append("# result = np.mean(data)  # 或其他計算\n")
            enhanced.append("```\n\n")
        
        # 檢測系統架構或模組段落
        if re.search(r'Engine|模組|模塊|系統架構|架構', stripped, re.IGNORECASE):
            enhanced.append("\n**[程式化說明]**\n")
            enhanced.append("此模組可對應到 Python 類別（class）或套件結構。\n\n")
            enhanced.append("**[白話註解]**\n")
            enhanced.append("這是一個功能單元，可以獨立開發與測試。\n\n")
        
        # 檢測資料結構段落
        if re.search(r'欄位|field|資料表|table|資料結構', stripped, re.IGNORECASE):
            enhanced.append("\n**[程式化說明]**\n")
            enhanced.append("此結構可用 dataclass 或 DataFrame 表示。\n\n")
        
        i += 1
    
    return enhanced

def correct_enhanced_content(enhanced_lines):
    """
    Phase 3: 在 ENHANCED 基礎上補公式、糾錯、外部補強
    標註來源層級：[原文]、[重寫整理]、[補充說明]、[外部知識補強]、[修正建議]
    """
    corrected = []
    i = 0
    
    while i < len(enhanced_lines):
        line = enhanced_lines[i]
        stripped = line.strip()
        
        # 保留 ENHANCED 內容
        corrected.append(line)
        
        # 檢測需要補公式的地方
        if re.search(r'標準差|Standard Deviation|std\(|方差', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("樣本標準差公式（ddof=1，無偏估計）：\n\n")
            corrected.append("$$\n")
            corrected.append("\\sigma = \\sqrt{\\frac{1}{n-1} \\sum_{i=1}^{n} (x_i - \\bar{x})^2}\n")
            corrected.append("$$\n\n")
            corrected.append("Python 實作：`np.std(data, ddof=1)`\n")
            corrected.append("母體標準差（ddof=0）：`np.std(data, ddof=0)`\n\n")
        
        # 檢測技術指標
        if re.search(r'RSI|Relative Strength Index', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("RSI 標準計算公式（Wilder's Smoothing）：\n\n")
            corrected.append("1. 計算價格變化：$\\Delta P = P_t - P_{t-1}$\n")
            corrected.append("2. 分離上漲與下跌：\n")
            corrected.append("   - Gain = $\\max(\\Delta P, 0)$\n")
            corrected.append("   - Loss = $\\max(-\\Delta P, 0)$\n")
            corrected.append("3. 計算平均 Gain 與 Loss（EMA 平滑）：\n")
            corrected.append("   - $\\text{AvgGain} = \\text{EMA}(Gain, n)$\n")
            corrected.append("   - $\\text{AvgLoss} = \\text{EMA}(Loss, n)$\n")
            corrected.append("4. RSI = $100 - \\frac{100}{1 + \\frac{\\text{AvgGain}}{\\text{AvgLoss}}}$\n\n")
            corrected.append("常見參數：n=14（日線）\n\n")
        
        if re.search(r'MACD|Moving Average Convergence Divergence', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("MACD 標準計算：\n\n")
            corrected.append("1. EMA12 = EMA(價格, 12)\n")
            corrected.append("2. EMA26 = EMA(價格, 26)\n")
            corrected.append("3. MACD Line = EMA12 - EMA26\n")
            corrected.append("4. Signal Line = EMA(MACD Line, 9)\n")
            corrected.append("5. Histogram = MACD Line - Signal Line\n\n")
        
        if re.search(r'Sharpe|夏普|Sharpe Ratio', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("Sharpe Ratio 標準公式：\n\n")
            corrected.append("$$\n")
            corrected.append("\\text{Sharpe} = \\frac{R_p - R_f}{\\sigma_p}\n")
            corrected.append("$$\n\n")
            corrected.append("其中：\n")
            corrected.append("- $R_p$ = 投資組合平均報酬率\n")
            corrected.append("- $R_f$ = 無風險利率（通常為0或國債利率）\n")
            corrected.append("- $\\sigma_p$ = 投資組合報酬率標準差\n\n")
            corrected.append("年化 Sharpe = 日 Sharpe × $\\sqrt{252}$（假設252個交易日）\n\n")
        
        if re.search(r'最大回撤|Max Drawdown|MDD', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("最大回撤（Max Drawdown）計算：\n\n")
            corrected.append("1. 計算累積淨值序列：$C_t = \\prod_{i=1}^{t} (1 + r_i)$\n")
            corrected.append("2. 計算歷史最高點：$P_t = \\max(C_1, C_2, ..., C_t)$\n")
            corrected.append("3. 計算回撤：$D_t = \\frac{P_t - C_t}{P_t}$\n")
            corrected.append("4. 最大回撤 = $\\max(D_1, D_2, ..., D_T)$\n\n")
            corrected.append("Python 實作：\n")
            corrected.append("```python\n")
            corrected.append("cumulative = (1 + returns).cumprod()\n")
            corrected.append("running_max = cumulative.expanding().max()\n")
            corrected.append("drawdown = (cumulative - running_max) / running_max\n")
            corrected.append("max_drawdown = drawdown.min()\n")
            corrected.append("```\n\n")
        
        if re.search(r'勝率|Win Rate|win_rate', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("勝率計算公式：\n\n")
            corrected.append("$$\n")
            corrected.append("\\text{Win Rate} = \\frac{\\text{獲利交易數}}{\\text{總交易數}} = \\frac{N_{win}}{N_{total}}\n")
            corrected.append("$$\n\n")
            corrected.append("注意：通常定義「獲利交易」為 $P_nL > 0$（或 $P_nL > \\epsilon$，避免手續費造成的小虧）。\n\n")
        
        if re.search(r'賺賠比|Risk Reward|R multiple', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("平均賺賠比（Average R-Multiple）計算：\n\n")
            corrected.append("1. 每筆交易 R = $\\frac{\\text{實際獲利/虧損}}{\\text{初始風險}}$（風險通常為停損距離）\n")
            corrected.append("2. 平均 R = $\\frac{1}{N} \\sum_{i=1}^{N} R_i$\n\n")
            corrected.append("或簡化版（不考慮風險單位）：\n")
            corrected.append("- 平均獲利 = $\\frac{1}{N_{win}} \\sum_{i: win} PnL_i$\n")
            corrected.append("- 平均虧損 = $\\frac{1}{N_{loss}} \\sum_{i: loss} |PnL_i|$\n")
            corrected.append("- 賺賠比 = $\\frac{\\text{平均獲利}}{\\text{平均虧損}}$\n\n")
        
        # 檢測 Beta 或相關性計算
        if re.search(r'Beta|beta|Beta係數|迴歸係數', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("Beta 係數計算公式（資本資產定價模型，CAPM）：\n\n")
            corrected.append("$$\n")
            corrected.append("\\beta = \\frac{\\text{Cov}(R_i, R_m)}{\\text{Var}(R_m)} = \\frac{\\sigma_{i,m}}{\\sigma_m^2}\n")
            corrected.append("$$\n\n")
            corrected.append("其中：\n")
            corrected.append("- $R_i$ = 資產報酬率\n")
            corrected.append("- $R_m$ = 市場報酬率\n")
            corrected.append("- $\\sigma_{i,m}$ = 資產與市場的協方差\n")
            corrected.append("- $\\sigma_m^2$ = 市場報酬率方差\n\n")
            corrected.append("Python 實作：`beta = np.cov(asset_returns, market_returns)[0,1] / np.var(market_returns)`\n\n")
        
        # 檢測相關性（Correlation）
        if re.search(r'相關性|Correlation|corr\(|相關係數', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("皮爾遜相關係數（Pearson Correlation）公式：\n\n")
            corrected.append("$$\n")
            corrected.append("\\rho = \\frac{\\text{Cov}(X, Y)}{\\sigma_X \\sigma_Y} = \\frac{E[(X-\\mu_X)(Y-\\mu_Y)]}{\\sigma_X \\sigma_Y}\n")
            corrected.append("$$\n\n")
            corrected.append("Python 實作：`np.corrcoef(x, y)[0, 1]` 或 `df.corr()`\n\n")
        
        # 檢測 CAGR
        if re.search(r'CAGR|年化報酬|Compound Annual', stripped, re.IGNORECASE):
            corrected.append("\n**[外部知識補強]**\n")
            corrected.append("年化複合報酬率（CAGR）計算公式：\n\n")
            corrected.append("$$\n")
            corrected.append("\\text{CAGR} = \\left(\\frac{V_{end}}{V_{start}}\\right)^{\\frac{1}{n}} - 1\n")
            corrected.append("$$\n\n")
            corrected.append("其中：\n")
            corrected.append("- $V_{end}$ = 終值\n")
            corrected.append("- $V_{start}$ = 初值\n")
            corrected.append("- $n$ = 年數\n\n")
            corrected.append("若為日報酬率轉年化：$\\text{CAGR} = (1 + \\bar{r})^{252} - 1$（252個交易日）\n\n")
        
        i += 1
    
    return corrected

def process_single_book(book_base_name):
    """處理單本書的 Phase 2 和 Phase 3"""
    structured_file = f"structured_books/{book_base_name}_AI知識庫版_v1_STRUCTURED.md"
    enhanced_file = f"structured_books/{book_base_name}_AI知識庫版_v1_ENHANCED.md"
    corrected_file = f"structured_books/{book_base_name}_AI知識庫版_v1_CORRECTED.md"
    
    if not os.path.exists(structured_file):
        return False, f"STRUCTURED 文件不存在: {structured_file}"
    
    try:
        # 讀取 STRUCTURED 版本
        with open(structured_file, 'r', encoding='utf-8') as f:
            structured_content = f.read()
            structured_lines = structured_content.splitlines(keepends=True)
        
        # 提取標題
        first_line = structured_lines[0].strip() if structured_lines else ""
        title_match = re.match(r'^#\s+(.+?)\s+-', first_line)
        if title_match:
            base_title = title_match.group(1)
        else:
            base_title = book_base_name
        
        # Phase 2: 生成 ENHANCED
        enhanced_lines = enhance_structured_content(structured_lines)
        
        enhanced_output = []
        enhanced_output.append(f"# {base_title} - ENHANCED 版\n\n")
        enhanced_output.append("> **說明**：本版本在 STRUCTURED 基礎上，拆解邏輯步驟，添加程序化說明與白話注解。\n\n")
        enhanced_output.append("> **原則**：不糾錯、不補外部資料、不改原意，只讓邏輯更清楚。\n\n")
        enhanced_output.append("---\n\n")
        enhanced_output.extend(enhanced_lines[1:] if enhanced_lines else [])
        
        with open(enhanced_file, 'w', encoding='utf-8') as f:
            f.writelines(enhanced_output)
        
        # Phase 3: 生成 CORRECTED（基於 ENHANCED）
        corrected_lines = correct_enhanced_content(enhanced_output)
        
        corrected_output = []
        corrected_output.append(f"# {base_title} - CORRECTED 版\n\n")
        corrected_output.append("> **說明**：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。\n\n")
        corrected_output.append("> **來源標記**：[原文] | [重寫整理] | [補充說明] | [外部知識補強] | [修正建議]\n\n")
        corrected_output.append("---\n\n")
        corrected_output.extend(corrected_lines[1:] if corrected_lines else [])
        
        with open(corrected_file, 'w', encoding='utf-8') as f:
            f.writelines(corrected_output)
        
        return True, (len(enhanced_output), len(corrected_output))
    
    except Exception as e:
        import traceback
        return False, f"{str(e)}\n{traceback.format_exc()}"

def main():
    """主程序"""
    BOOKS = [
        "J-GOD 股市聖經系統1",
        "J-GOD 邏輯系統補充",
        "J-GOD_Book_Complete_v1",
        "JGOD_STOCK_TRADING_BIBLE_v1",
        "JGOD_原始開發藍圖_清整強化版",
        "Path A  歷史回測撈取資料＋分析",
        "滾動式分析",
        "股市大自然萬物修復法則",
        "股市聖經三",
        "股市聖經二",
        "股市聖經四",
        "股神腦系統具體化設計",
        "邏輯版操作說明書",
        "雙引擎與自主演化閉環",
    ]
    
    print("=" * 60)
    print("Phase 2 & 3: 生成 ENHANCED 和 CORRECTED 版本")
    print("=" * 60)
    print()
    
    results = []
    
    for i, book_base in enumerate(BOOKS, 1):
        print(f"[{i:2d}/14] 處理：{book_base}")
        
        success, info = process_single_book(book_base)
        
        if success:
            enhanced_lines, corrected_lines = info
            print(f"      ✅ ENHANCED: {enhanced_lines} 行")
            print(f"      ✅ CORRECTED: {corrected_lines} 行")
            results.append((book_base, True, info))
        else:
            print(f"      ❌ 失敗：{info[:100]}")
            results.append((book_base, False, info))
    
    print()
    print("=" * 60)
    success_count = sum(1 for _, ok, _ in results if ok)
    print(f"Phase 2 & 3 完成：{success_count}/14 成功")
    
    return success_count == 14

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

