# J-GOD 錯誤分析報告
**事件 ID**: DEMO_CASE_A_UTILIZATION_GAP
**分析時間**: 2025-11-30 08:38:10

---

## 1. 錯誤基本資訊

- **標的**: 2330
- **時間框架**: 1d
- **方向**: long
- **預測結果**: hit_tp
- **實際結果**: hit_sl
- **損益**: -2000.00
- **錯誤類型**: stop_loss
- **標籤**: exit, entry, intraday

**備註**: 預測會到達目標價，但實際上觸及停損。與「勝率計算公式：」相關但該規則未被觸發。

---

## 2. 分類結果

**分類**: `UTILIZATION_GAP`

**說明**: 運用落差：知識庫中已有相關規則，但未被使用


---

## 3. 相關知識項目

### RULE

- **勝率計算公式：** (ID: RULE_0002)
  - 標籤: exit, entry, intraday, stop_loss, risk
- **J-GOD 核心模組架構:** (ID: RULE_0004)
  - 標籤: entry, intraday, stop_loss, risk, position_sizing
- **```python** (ID: RULE_0005)
  - 標籤: risk, entry, stop_loss
- **J-GOD 系統架構:** (ID: RULE_0006)
  - 標籤: risk, entry, stop_loss
- **```python** (ID: RULE_0007)
  - 標籤: entry, intraday, stop_loss, risk, position_sizing
- **- 檢查：哪些股票觸發進場價格、哪些到達停利區、哪些跌破停損** (ID: RULE_0008)
  - 標籤: risk, position_sizing, entry, stop_loss
- **row1: RealTrades_真實交易 | 日期、時間、代號、名稱、多空、口數/股數、成交價、成本含手續稅、策略標籤、來自股神訊號、SignalID、預設停損價、預設停利價、實際出場價、出場日期、** (ID: RULE_0009)
  - 標籤: risk, exit, entry, stop_loss
- **年化複合報酬率（CAGR）計算公式：** (ID: RULE_0011)
  - 標籤: risk, entry, stop_loss
- **definition: 最強的交易系統都有固定人格。J-GOD的人格定為：冷靜、精準、不FOMO、像老練操盤手、不放情緒、不做預言只算機率、不怕停損、永遠保留子彈、風險永遠第一。** (ID: RULE_0012)
  - 標籤: risk, entry, stop_loss
- **勝率計算公式：** (ID: RULE_0016)
  - 標籤: exit, entry, intraday, stop_loss, risk
- **本手冊整合了 J-GOD 系統的核心交易哲學、技術方法、系統架構與實戰指南，** (ID: RULE_0018)
  - 標籤: exit, entry, intraday, stop_loss, risk
- **勝率計算公式：** (ID: RULE_0020)
  - 標籤: exit, entry, intraday, stop_loss, risk
- **```python** (ID: RULE_0023)
  - 標籤: risk, intraday, entry
- **```python** (ID: RULE_0027)
  - 標籤: intraday, entry
- **```python** (ID: RULE_0037)
  - 標籤: intraday
- **您提出的五大階段在概念上是正確的，但從系統論和認知科學的角度看，可以被更精煉、更具指導意義地組織為三大核心階段（或稱「循環模態」），以更好地體現其生命體般的自我進化特性。** (ID: RULE_0042)
  - 標籤: risk, position_sizing, intraday
- **```python** (ID: RULE_0044)
  - 標籤: entry, intraday, stop_loss, risk, position_sizing
- **⚙️ II. 系統架構與數據整合 (Python & API)** (ID: RULE_0046)
  - 標籤: entry, intraday, stop_loss, risk, position_sizing
- **\beta = \frac{\text{Cov}(R_i, R_m)}{\text{Var}(R_m)} = \frac{\sigma_{i,m}}{\sigma_m^2}** (ID: RULE_0048)
  - 標籤: risk, position_sizing, intraday, entry
- **"AI_Concept": 1.5e6,** (ID: RULE_0050)
  - 標籤: risk, position_sizing, exit, entry


---

## 4. 系統判斷

### 運用落差分析

- 規則 RULE_0002 (勝率計算公式：) 存在但未被使用
- 規則 RULE_0004 (J-GOD 核心模組架構:) 存在但未被使用
- 規則 RULE_0005 (```python) 存在但未被使用
- 規則 RULE_0006 (J-GOD 系統架構:) 存在但未被使用
- 規則 RULE_0007 (```python) 存在但未被使用

**問題**: 明明存在但未使用的規則


---

## 5. 建議補強方向


---

## 6. 後續動作

- 檢查為何 24 條相關規則未被觸發
- 檢視規則觸發條件是否過於嚴格

---

## 7. 查詢資訊

**查詢字串**: `stop_loss exit entry intraday symbol 2330 timeframe 1d hit_tp vs hit_sl 預測會到達目標價，但實際上觸及停損。與「勝率計算公式：」相關但該規則未被觸發。`

**查詢時間**: 2025-11-30 08:38:10.181891

