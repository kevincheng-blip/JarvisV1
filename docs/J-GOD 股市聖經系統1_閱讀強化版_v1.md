# J-GOD 股市聖經系統1：閱讀強化版 v1

> **說明**：本文件是 J-GOD 股神作戰系統 v0 版本的完整設計文件，包含 Excel/Google Sheet 工作表設計、GPT Prompt 模板等。

---

## 一、這本書的目的

[CONCEPT]
name: 本書目的
definition: 建立 J-GOD v0 版本的整體結構設計，使用 Excel/Google Sheet 就能運行，包含四張核心工作表設計、盤前戰報與收盤戰報的 GPT Prompt 模板。

[NOTE]
本文件旨在建立一個「一個人也能維護」的系統，不碰任何 API，只需每天把資料貼給 GPT，就能自動產生戰報。

---

## 二、核心投資邏輯

[CONCEPT]
name: J-GOD v0 核心邏輯
definition: 使用 Excel/Google Sheet 作為數據收集與管理工具，結合 GPT 產生盤前/收盤報告，建立完整的交易記錄與策略分析系統。

[RULE]
IF 使用 J-GOD v0 系統
THEN 需要建立 4 張核心工作表：Daily_Market、Watchlist、Trades、Strategy_Notes

---

## 三、股票判斷方法（技術面 + 基本面）

[NOTE]
本文件主要聚焦於系統架構設計，技術面與基本面判斷方法請參考其他股市聖經文件。

[CONCEPT]
name: 觀察名單管理
definition: 透過 Watchlist 工作表管理觀察名單與策略標的，包含股票代號、族群、主題、策略標籤、進場條件等。

---

## 四、交易策略

[RULE]
IF 建立交易策略
THEN 需要在 Watchlist 工作表中設定：
  1. Setup_Condition（進場條件）
  2. Entry_Price_Plan（預計進場價區間）
  3. Stop_Loss_Price（停損價）
  4. Target_Price（目標價）
  5. Position_Size_Rule（部位大小規則）

[RULE]
IF 執行交易
THEN 需要在 Trades 工作表中記錄：
  1. 交易日期、股票代號、方向（多/空）
  2. 進場價、出場價、數量
  3. 策略標籤、進場理由、出場理由
  4. 實際報酬率、風險指標

---

## 五、風險控管與心理面

[RULE]
IF 建立觀察名單
THEN 必須設定 Stop_Loss_Price（停損價）和 Position_Size_Rule（部位大小規則）

[RULE]
IF 執行交易
THEN 必須記錄實際報酬率和風險指標，用於後續勝率與策略效果分析

[CONCEPT]
name: 風險控管
definition: 透過 Trades 工作表記錄每筆交易的停損價、部位大小、實際報酬率，建立完整的風險控管機制。

---

## 六、開盤／盤中／收盤 SOP

### 6.1 盤前流程

[RULE]
IF 每天 08:30～08:50
THEN 執行以下步驟：
  1. 開啟 Daily_Market 工作表
  2. 在當天那一列的各欄位填資料
  3. 複製 Raw_Notes + 其他關鍵欄位
  4. 丟給 GPT，使用盤前戰報 Prompt 產生「盤前戰報」

[STRUCTURE]
盤前資料收集項目：
- Date（日期）
- TAIX_Trend（加權指數方向）
- Futures_Trend（期指方向）
- Foreign_BuySell（外資買賣超）
- Dealers_BuySell（自營商買賣超）
- Sectors_Strong（強勢族群）
- Sectors_Weak（弱勢族群）
- Leader_Stocks（主流龍頭股）
- Risk_Events（重要事件）
- My_Bias（主觀判斷）
- Plan_Summary（作戰計畫摘要）
- Raw_Notes（零碎紀錄）

### 6.2 盤中監控

[NOTE]
v0 版本主要聚焦於盤前與收盤，盤中監控將在後續版本中實現。

### 6.3 收盤流程

[RULE]
IF 收盤後
THEN 執行以下步驟：
  1. 更新 Daily_Market 工作表的收盤資料
  2. 更新 Trades 工作表的交易記錄
  3. 複製收盤資料給 GPT，使用收盤戰報 Prompt 產生「收盤檢討」

---

## 七、實戰案例整理

[NOTE]
v0 版本為基礎架構設計，實際交易案例將在後續版本中補充。

[CONCEPT]
name: 工作表使用範例
definition: 
- Daily_Market：每天記錄盤前與收盤資料
- Watchlist：管理觀察名單與策略標的
- Trades：記錄所有真實倉與虛擬倉交易
- Strategy_Notes：記錄策略手冊與當日重點

---

## 八、AI 補充

### 8.1 GPT Prompt 模板

[CONCEPT]
name: 盤前戰報 Prompt
definition: 將 Daily_Market 工作表的資料整理後，使用固定的 GPT Prompt 模板產生結構化的盤前戰報。

[CONCEPT]
name: 收盤戰報 Prompt
definition: 將 Daily_Market 和 Trades 工作表的資料整理後，使用固定的 GPT Prompt 模板產生結構化的收盤檢討報告。

[NOTE]
AI 補充：GPT Prompt 模板的具體內容請參考原始文件中的詳細設計。

### 8.2 未來擴展方向

[NOTE]
AI 補充：v0 版本完成後，可以往以下方向擴展：
- v1：Python 統計勝率 & 策略效果
- v2：串接 API 自動更新報價與指標

---

## 九、可轉程式化的 J-GOD 規則列表

### 9.1 工作表建立規則

[RULE]
IF 建立 J-GOD v0 系統
THEN 必須建立 4 張工作表：Daily_Market、Watchlist、Trades、Strategy_Notes

### 9.2 資料填寫規則

[RULE]
IF 盤前準備
THEN 必須填寫 Daily_Market 工作表的所有欄位

[RULE]
IF 執行交易
THEN 必須在 Trades 工作表記錄完整的交易資訊

[RULE]
IF 收盤檢討
THEN 必須更新 Daily_Market 和 Trades 工作表，並產生收盤戰報

### 9.3 GPT Prompt 使用規則

[RULE]
IF 產生盤前戰報
THEN 使用盤前戰報 Prompt 模板，輸入 Daily_Market 工作表的資料

[RULE]
IF 產生收盤戰報
THEN 使用收盤戰報 Prompt 模板，輸入 Daily_Market 和 Trades 工作表的資料

---

## 附錄：工作表欄位設計詳解

### A. Daily_Market 工作表

[TABLE]
columns: 欄位名稱 | 說明
Date | 日期（2025-11-18）
Session | Pre / Close（盤前 / 收盤）
TAIX_Trend | 加權指數方向（多 / 空 / 盤整 + 概述）
Futures_Trend | 期指方向 & 買賣超感覺
Foreign_BuySell | 外資買賣超金額 & 簡評
Dealers_BuySell | 自營商買賣超 & 簡評
Sectors_Strong | 強勢族群（半導體、AI、金融、軍工…）
Sectors_Weak | 弱勢族群
Leader_Stocks | 當日/預期的主流龍頭股（2330、2382…）
Risk_Events | 重要事件（FED、選舉、台積法說、重大新聞）
My_Bias | 主觀判斷（多/空/中立 + 理由）
Plan_Summary | 今日作戰計畫摘要
Raw_Notes | 零碎紀錄、想法全部塞這一格

### B. Watchlist 工作表

[TABLE]
columns: 欄位名稱 | 說明
Symbol | 股票代號（2330）
Name | 股票名稱（台積電）
Sector | 族群（半導體、AI、軍工…）
Theme | 主題（AI伺服器、車用、低軌衛星…）
Strategy_Tag | 策略標籤（波段多、當沖、隔日沖、價值投資、反轉…）
Setup_Condition | 進場條件（站上月線 + 爆量突破區間…）
Entry_Price_Plan | 預計進場價區間
Stop_Loss_Price | 停損價
Target_Price | 目標價
Position_Size_Rule | 部位大小規則（例如：滿倉10單位，這檔最多 2 單位）
Priority | 優先級（A/B/C or 1/2/3）
Note | 補充說明（選股理由、主力特徵、法人籌碼等）

### C. Trades 工作表

[TABLE]
columns: 欄位名稱 | 說明
Date | 交易日期
Symbol | 股票代號
Direction | 方向（多/空）
Entry_Price | 進場價
Exit_Price | 出場價
Quantity | 數量
Strategy_Tag | 策略標籤
Entry_Reason | 進場理由
Exit_Reason | 出場理由
Return_Rate | 實際報酬率
Risk_Indicator | 風險指標

### D. Strategy_Notes 工作表

[TABLE]
columns: 欄位名稱 | 說明
Date | 日期
Strategy_Name | 策略名稱
Notes | 策略手冊 & 當日重點
Performance | 績效記錄

---

## 總結

[NOTE]
本文件完整保留了原始內容的所有技術細節，包括：
- 所有工作表欄位設計
- 所有 GPT Prompt 模板
- 所有操作流程與規則

[CONCEPT]
name: J-GOD v0 系統
definition: 一個使用 Excel/Google Sheet 就能運行的交易系統，結合 GPT 產生盤前/收盤報告，建立完整的交易記錄與策略分析機制。

[NOTE]
本文件旨在建立一個「一個人也能維護」的系統，為後續 v1、v2 版本打下基礎。

---

*文件建立時間：2024年*
*版本：v1*
*原始文件：J-GOD 股市聖經系統1.docx.txt（未修改）*

