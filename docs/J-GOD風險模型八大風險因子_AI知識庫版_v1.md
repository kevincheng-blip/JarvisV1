# J-GOD 風險模型八大風險因子（AI 知識庫版 v1）

本文件定義 J-GOD 多因子風險模型的核心內容，為 J-GOD Risk Model v1.0 的理論基礎。

---

# Ⅰ. 系統性風險因子 (Systemic Risk Factors)

## R-MKT — 市場系統性風險 (Market)

衡量股票報酬對大盤指數（如加權指數）的敏感度。

公式：

R-MKT = 當期市場指數報酬

---

## R-SIZE — 規模風險 (Size)

捕捉大市值 vs. 小市值之間的系統性差異，小型股具更高波動 + 流動性風險。

公式：

R-SIZE = 小市值組合報酬 − 大市值組合報酬

---

## R-VAL — 價值風險 (Value)

衡量高帳面價值（低股價） vs. 低帳面價值（高股價）公司間報酬差。

公式：

R-VAL = 高 B/M 組合報酬 − 低 B/M 組合報酬

---

## R-MOM — 動量風險 (Momentum)

捕捉過去表現好的股票 vs. 表現差股票的風險差。

公式：

R-MOM = 贏家組合報酬 − 輸家組合報酬

---

# Ⅱ. 特質性與另類風險因子 (Idiosyncratic & Alternative Risk Factors)

## R-LIQ — 流動性風險 (Liquidity)

衡量股票交易的難易程度，低流動性具高價差與清算風險。

公式（其中之一）：

R-LIQ = (成交量 × 股價) / 市值

或使用 Amihud Illiquidity / Bid-Ask Spread

---

## R-VOL — 波動率風險 (Volatility)

捕捉高波動股票 vs. 低波動股票的差異。

公式：

R-VOL = 高波動率組合報酬 − 低波動率組合報酬

---

## R-FX/IR — 匯率/利率風險 (FX / Interest Rate)

衡量股票對匯率變動、利率變動（如公債殖利率）的暴露度。

公式：

R-FX/IR = 主要貨幣匯率變動 + 公債殖利率變動

---

## R-FLOW — 生態圈資金流風險 (Ecosystem Flow Risk)

J-GOD 獨有風險因子。衡量高資金流暴露的股票在資金流逆轉時的拋壓風險。

公式：

R-FLOW = 高 Flow 暴露組合報酬 − 低 Flow 暴露組合報酬

---

# Ⅲ. J-GOD 風險模型的計算流程

## 1. 計算每日八大風險因子報酬

透過組合淨值或迴歸法估算。

## 2. 建立八因子協方差矩陣

使用 120–250 天的歷史數據。

產生 Σ_Risk。

## 3. 計算個股風險暴露 X_i

對每檔股票進行多因子迴歸。

## 4. 計算投資組合總風險

σ²_p = wᵀ X Σ_Risk Xᵀ w + wᵀ Δ w

其中：

- w = 權重向量  
- X = 因子暴露度矩陣  
- Σ_Risk = 八因子協方差矩陣  
- Δ = 特質性風險矩陣  

---

# Ⅳ. 與 J-GOD Alpha Engine / Path A 的整合

- Flow Alpha ↔ R-FLOW（風險補償）

- Reversion Alpha ↔ R-VOL（均值回歸與波動反向）

- Inertia Alpha ↔ R-MOM（動能風險）

- Value/Quality Alpha ↔ R-VAL（價值風險）

- 台股大盤 ↔ R-MKT（市場 β 結構）

- 小/大市值 ↔ R-SIZE（流動性風險）

- 金融 / 電子 / 傳產 ↔ R-FX/IR（匯率 + 利率敏感度）

此文件作為：  
J-GOD Risk Model v1.0 的正式理論定義檔案。

