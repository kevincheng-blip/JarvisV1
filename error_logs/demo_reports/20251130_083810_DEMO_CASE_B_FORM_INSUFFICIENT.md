# J-GOD 錯誤分析報告
**事件 ID**: DEMO_CASE_B_FORM_INSUFFICIENT
**分析時間**: 2025-11-30 08:38:10

---

## 1. 錯誤基本資訊

- **標的**: 2330
- **時間框架**: 5m
- **方向**: long
- **預測結果**: up
- **實際結果**: down
- **損益**: -500.00
- **錯誤類型**: timing
- **標籤**: intraday, concept

**備註**: 預測「> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。」相關的市場行為，但僅有概念定義，缺乏可執行的規則來判斷時機。

---

## 2. 分類結果

**分類**: `UTILIZATION_GAP`

**說明**: 運用落差：知識庫中已有相關規則，但未被使用


---

## 3. 相關知識項目

### RULE

- **> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。** (ID: RULE_0001)
- **勝率計算公式：** (ID: RULE_0002)
  - 標籤: exit, entry, intraday, stop_loss, risk
- **> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。** (ID: RULE_0003)
- **J-GOD 核心模組架構:** (ID: RULE_0004)
  - 標籤: entry, intraday, stop_loss, risk, position_sizing
- **```python** (ID: RULE_0007)
  - 標籤: entry, intraday, stop_loss, risk, position_sizing
- **row1: RealTrades_真實交易 | 日期、時間、代號、名稱、多空、口數/股數、成交價、成本含手續稅、策略標籤、來自股神訊號、SignalID、預設停損價、預設停利價、實際出場價、出場日期、** (ID: RULE_0009)
  - 標籤: risk, exit, entry, stop_loss
- **年化複合報酬率（CAGR）計算公式：** (ID: RULE_0011)
  - 標籤: risk, entry, stop_loss
- **本文件完整保留了原始TXT文件的所有內容，並為每一段加上了適當的分類標籤。所有公式、規則、程式碼、表格、系統架構都已完整保留，可直接被AI模型解析、轉換為JSON、向量化或規則引擎使用。** (ID: RULE_0014)
- **> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。** (ID: RULE_0015)
- **勝率計算公式：** (ID: RULE_0016)
  - 標籤: exit, entry, intraday, stop_loss, risk
- **> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。** (ID: RULE_0017)
- **本手冊整合了 J-GOD 系統的核心交易哲學、技術方法、系統架構與實戰指南，** (ID: RULE_0018)
  - 標籤: exit, entry, intraday, stop_loss, risk
- **> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。** (ID: RULE_0019)
- **勝率計算公式：** (ID: RULE_0020)
  - 標籤: exit, entry, intraday, stop_loss, risk
- **> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。** (ID: RULE_0021)
- **```python** (ID: RULE_0023)
  - 標籤: risk, intraday, entry
- **Sharpe Ratio 標準公式：** (ID: RULE_0024)
  - 標籤: risk
- **```python** (ID: RULE_0027)
  - 標籤: intraday, entry
- **> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。** (ID: RULE_0028)
- **```python** (ID: RULE_0030)
  - 標籤: risk


---

## 4. 系統判斷

### 運用落差分析

- 規則 RULE_0001 (> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。) 存在但未被使用
- 規則 RULE_0002 (勝率計算公式：) 存在但未被使用
- 規則 RULE_0003 (> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。) 存在但未被使用
- 規則 RULE_0004 (J-GOD 核心模組架構:) 存在但未被使用
- 規則 RULE_0007 (```python) 存在但未被使用

**問題**: 明明存在但未使用的規則


---

## 5. 建議補強方向


---

## 6. 後續動作

- 檢查為何 39 條相關規則未被觸發
- 檢視規則觸發條件是否過於嚴格

---

## 7. 查詢資訊

**查詢字串**: `timing intraday concept symbol 2330 timeframe 5m up vs down 預測「> 說明：本版本在 ENHANCED 基礎上，補齊公式、統計定義、量化金融標準算法，並標註所有補強的來源層級。」相關的市場行為，但僅有概念定義，缺乏可執行的規則來判斷時機。`

**查詢時間**: 2025-11-30 08:38:10.312572

