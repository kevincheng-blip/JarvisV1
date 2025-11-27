# J-GOD 邏輯系統補充：強化重構版 v1

## 這本書的目的

本文件旨在建立 J-GOD 股神作戰系統（Jarvis Global Operation of Delta）的完整架構與實作指南。J-GOD 不是一個小工具，而是一個「個人量化自營部 + 市場情報局 + AI 教練 + 風險管制官」的完整系統。

**核心目標**：
- 建立一套「個人量化自營部級」的交易決策系統
- 整合預測、監控、進化三大核心功能
- 對標 Citadel、Renaissance、Bridgewater、Two Sigma 等頂尖機構
- 從手動版逐步進化到雲端自動化系統

---

## 核心投資邏輯

### 一、J-GOD 系統定位

#### 1. 系統定義
J-GOD 股神作戰系統（Jarvis Global Operation of Delta）是一個完整的投資決策生態系，永遠做三件事：
1. **預測**：大盤 / 期指 / 族群 / 個股 / 爆發機率
2. **監控**：你的真實部位 + 虛擬部位（Paper Trading）
3. **進化**：每天用虛擬倉 & 回測優化策略，讓自己和你一起越來越強

#### 2. 整合功能
所有功能都被整合在 J-GOD 裡：
- ⚡ 大盤方向
- ⚡ 族群方向
- ⚡ 強勢股票
- ⚡ 主力攻擊
- ⚡ 反轉時間
- ⚡ 潛在爆拉股
- ⚡ 真實倉 & 虛擬倉
- ⚡ 即時警報
- ⚡ 期指當沖判斷

### 二、對標頂尖機構的缺失分析

#### 1. 目前 J-GOD 已具備的力量
- ✔ 大盤預測
- ✔ 期指攻防
- ✔ 族群熱力
- ✔ 爆拉股模型
- ✔ 主力方向
- ✔ 盤中反轉
- ✔ 部位監控
- ✔ 虛擬倉
- ✔ 即時警報
- ✔ 五螢幕作戰中心

這些已經超越：散戶、80% 主觀操盤手、大部分自營部、小型對沖基金、多數 KOL、財經老師。

#### 2. 還缺的六大關鍵武器

**缺 1：AI「公司體質」與「基本面」引擎（Fundamental Engine）**
- **目標**：讓 J-GOD 像巴菲特一樣「看穿公司靈魂」
- **功能**：
  - 自動讀台灣所有上市櫃財報
  - 自動讀法說會簡報
  - 計算：毛利率、營益率、ROE/ROA、EPS、負債比、現金流、年成長率 CAGR
  - AI 判斷護城河：競爭壁壘、市佔率、客戶集中度、價格主導力、供應鏈優勢
  - AI 做「質化分析」：管理層可信度、業務模式健康度、產業趨勢
- **輸出**：J-Score 公司健康度（0-100）
  - 70 以上 = 公司超健康
  - 50 = 普通
  - 30 = 雷股體質

**缺 2：AI「多策略組合」模型（Multi-Strategy Engine）**
- **目標**：讓 J-GOD 不是一種玩法，是「20 種策略同時運作」
- **包含策略**：
  1. 趨勢（Trend Following）
  2. 動能（Momentum）
  3. 反轉（Mean Reversion）
  4. 價值（Value）
  5. 成長（Growth）
  6. 事件（Event Driven）
  7. Pair Trading（價差套利）
  8. 市場中性（Market Neutral）
  9. Volatility Trading（波動策略）
  10. 指標共識策略（Composite Signals）
  11. 流程套利（短線掃缺口策略）
  12. 隱含突破策略（Breakout AI）
- **特色**：所有策略會告訴你「今天哪一套強」、告訴你「哪套不能用」、自動切換策略權重

**缺 3：AI「機器學習預測」引擎（ML Forecast Engine）**
- **模型包含**：
  - LightGBM
  - XGBoost
  - Random Forest
  - LSTM（時序模型）
  - Transformer Financial Models
  - AutoML Hyperparameter Tuning
  - PCA + 因子模型
- **可預測**：
  - 大盤收紅 / 收黑機率
  - 個股未來 5 日上漲機率
  - 族群資金流向
  - 爆發股的加速度
  - 反轉時間
  - 期指尾盤方向

**缺 4：AI「期權」與「波動度」分析（Options Engine）**
- **功能**：
  - 台指選擇權 OI 分析
  - IV（隱含波動度）
  - Skew（多空偏移）
  - IV Crush / IV Boost
  - 大單期權佈局
  - 合約風險集中點（Gamma Exposure）
  - 最大痛苦值（Max Pain）
- **輸出**：
  - 大盤未來可能爆拉 / 崩跌的機率
  - 外資真正押注的方向
  - 市場恐慌 / 貪婪程度
  - 未來 1 天波動區間

**缺 5：AI「資金流大數據」分析（Money Flow Engine）**
- **資金來源**：
  - 台幣匯率
  - 外資買賣超
  - 北上資金（陸股）
  - 美股資金流向
  - ETF 流入流出
  - AI 概念（NVDA/META/MSFT）
  - 比特幣風險資金流
  - 債券殖利率
  - 宏觀指標（PMI、CPI 方向）
- **輸出**：
  - 資金是「流入台股」還是「撤離台股」
  - 哪個族群今天得到最多資金
  - 哪個族群今天死掉
  - 全球市場「風險 ON / OFF」

**缺 6：J-GOD 的「人格」與「最終任務」**
- **J-GOD 的人格**：
  - 冷靜
  - 精準
  - 不 FOMO
  - 像老練操盤手
  - 不放情緒
  - 不做預言，只算機率
  - 不怕停損
  - 永遠保留子彈
  - 風險永遠第一
- **J-GOD 的使命**：最大化你的資金報酬，同時最小化風險，並讓 Kevin 成為世界級操盤手
- **J-GOD 的投資哲學**：趨勢為主、反轉為輔、事件加速、資金主導、風險為先

### 三、J-GOD v∞ 完全體架構

J-GOD v∞（完全體）擁有：
- ✔ 巴菲特（質化投資）
- ✔ Renaissance（量化預測）
- ✔ Citadel（期權視角）
- ✔ Bridgewater（宏觀）
- ✔ Two Sigma（AI 模型）
- ✔ GPT/AI 新時代

這是**量化基金級超級 AI 系統**。

---

## 股票判斷方法

### 一、技術面判斷

#### 1. 大盤方向判斷（期指預測模組）

**判斷規則**：
- 如果 今日收紅機率 > 60% 且 預估漲跌點數區間為正，則 大盤偏多
- 如果 今日收黑機率 > 60% 且 預估漲跌點數區間為負，則 大盤偏空
- 如果 盤中反轉機率 > 30%，則 需要留意盤中轉折
- 如果 尾盤拉抬機率 > 50%，則 尾盤可能上攻
- 如果 尾盤殺盤機率 > 50%，則 尾盤可能下殺

**盤勢標籤判斷**：
- 如果 多空力道指標強烈偏多 且 期指 vs 現貨背離狀態正常，則 盤勢標籤 = 強多
- 如果 多空力道指標偏多 且 期指 vs 現貨背離狀態正常，則 盤勢標籤 = 偏多
- 如果 多空力道指標中性，則 盤勢標籤 = 中性
- 如果 多空力道指標偏空，則 盤勢標籤 = 偏空
- 如果 多空力道指標強烈偏空，則 盤勢標籤 = 強空
- 如果 期指 vs 現貨背離狀態異常，則 盤勢標籤 = 洗盤或搖擺

#### 2. 個股強弱判斷（即時雷達）

**異常量判斷**：
- 如果 當前量 / 過去平均量 > 2.0，則 異常量（爆量）
- 如果 異常量出現 且 價格突破關鍵價，則 短線爆拉訊號
- 如果 異常量出現 且 價格跌破關鍵價，則 短線急殺訊號

**異常大單判斷**：
- 如果 大單數量 > X 張（可設定），則 異常大單
- 如果 異常大單出現 且 方向為買，則 主力進場
- 如果 異常大單出現 且 方向為賣，則 主力出貨

**族群共振判斷**：
- 如果 該股所在族群同步放量，則 族群共振強度高
- 如果 族群共振強度高 且 個股異常量，則 強烈做多訊號

#### 3. 部位監控判斷（Position Guardian）

**偏離預測判斷**：
- 如果 實際走勢偏離預測 > 閾值，則 觸發警報
- 如果 偏離程度 > 強烈警告閾值，則 警報等級 = 🔴 強烈警告
- 如果 偏離程度 > 中度風險閾值 且 <= 強烈警告閾值，則 警報等級 = 🟠 中度風險
- 如果 偏離程度 <= 中度風險閾值，則 警報等級 = 🟢 一切正常

**主力倒貨判斷**：
- 如果 主力大單方向轉為賣 且 持續時間 > 閾值，則 主力倒貨
- 如果 主力倒貨 且 價格開始下跌，則 觸發 🔴 強烈警告

**族群轉弱判斷**：
- 如果 族群資金流轉為負 且 持續時間 > 閾值，則 族群轉弱
- 如果 族群轉弱 且 個股也轉弱，則 觸發 🟠 中度風險

**外資/投信突然砍判斷**：
- 如果 外資/投信買賣超突然轉為負 且 幅度 > 閾值，則 外資/投信突然砍
- 如果 外資/投信突然砍 且 個股價格開始下跌，則 觸發 🔴 強烈警告

### 二、基本面判斷

#### 1. 公司體質判斷（Fundamental Engine）

**J-Score 判斷**：
- 如果 J-Score >= 70，則 公司超健康，適合長期持有
- 如果 J-Score >= 50 且 < 70，則 公司普通，需要進一步分析
- 如果 J-Score < 30，則 雷股體質，應避免投資

**護城河判斷**：
- 如果 競爭壁壘高 且 市佔率高 且 價格主導力強，則 護城河強
- 如果 護城河強 且 J-Score >= 70，則 強烈建議長期持有

**質化分析判斷**：
- 如果 管理層可信度高 且 業務模式健康度好 且 產業趨勢向上，則 質化評分高
- 如果 質化評分高 且 J-Score >= 70，則 適合價值投資

### 三、綜合判斷邏輯

**多因子共振判斷**：
- 如果 技術面強 且 基本面強（J-Score >= 70） 且 族群資金流強 且 ML 預測上漲機率高，則 **強烈做多**
- 如果 技術面弱 且 基本面弱（J-Score < 30） 且 族群資金流弱 且 ML 預測下跌機率高，則 **強烈做空**
- 如果 技術面強 但 基本面弱（J-Score < 30），則 **只適合短線，不適合長期持有**

---

## 交易策略

### 一、多策略組合策略

#### 1. 趨勢策略（Trend Following）
- **進場條件**：
  - 如果 價格突破關鍵阻力位 且 成交量放大 且 趨勢指標向上，則 進場做多
- **出場條件**：
  - 如果 價格跌破趨勢線 或 成交量萎縮，則 出場
- **停損條件**：
  - 如果 價格跌破進場價 - 3%，則 停損

#### 2. 反轉策略（Mean Reversion）
- **進場條件**：
  - 如果 價格超跌（RSI < 30） 且 成交量放大 且 反轉訊號出現，則 進場做多
- **出場條件**：
  - 如果 價格回到正常區間（RSI > 50） 或 反轉訊號消失，則 出場
- **停損條件**：
  - 如果 價格繼續下跌超過進場價 - 5%，則 停損

#### 3. 價值策略（Value）
- **進場條件**：
  - 如果 J-Score >= 70 且 價格低於內在價值 且 護城河強，則 進場做多
- **出場條件**：
  - 如果 價格達到內在價值 或 J-Score 下降 < 50，則 出場
- **停損條件**：
  - 如果 J-Score 下降 < 30，則 停損

#### 4. 成長策略（Growth）
- **進場條件**：
  - 如果 年成長率 CAGR > 20% 且 營益率上升 且 產業趨勢向上，則 進場做多
- **出場條件**：
  - 如果 年成長率 CAGR 下降 < 10% 或 營益率下降，則 出場
- **停損條件**：
  - 如果 年成長率 CAGR 轉為負，則 停損

#### 5. 動能策略（Momentum）
- **進場條件**：
  - 如果 價格加速度 > 閾值 且 成交量放大 且 動能指標向上，則 進場做多
- **出場條件**：
  - 如果 價格加速度轉為負 或 動能指標轉弱，則 出場
- **停損條件**：
  - 如果 價格跌破進場價 - 2%，則 停損

#### 6. 事件策略（Event Driven）
- **進場條件**：
  - 如果 重大利多事件發生 且 GPT 判斷強度為 A/B 級 且 技術面配合，則 進場做多
- **出場條件**：
  - 如果 事件影響消退 或 技術面轉弱，則 出場
- **停損條件**：
  - 如果 事件影響轉為負面，則 停損

#### 7. 價差套利策略（Pair Trading）
- **進場條件**：
  - 如果 兩個高度相關股票的價差 Z-score > 2.0，則 做多被錯殺、做空被高估
- **出場條件**：
  - 如果 價差 Z-score 回歸到 0，則 出場
- **停損條件**：
  - 如果 價差 Z-score 繼續擴大超過 3.0，則 停損

#### 8. 市場中性策略（Market Neutral）
- **進場條件**：
  - 如果 個股 Alpha > 閾值 且 市場 Beta 接近 0，則 進場做多
- **出場條件**：
  - 如果 個股 Alpha 轉為負 或 市場 Beta 偏離 0，則 出場
- **停損條件**：
  - 如果 個股 Alpha < -閾值，則 停損

### 二、策略選擇邏輯

**自動策略選擇規則**：
- 如果 今天是趨勢盤 且 趨勢策略勝率高，則 優先使用趨勢策略
- 如果 今天是震盪盤 且 反轉策略勝率高，則 優先使用反轉策略
- 如果 今天是事件盤 且 事件策略勝率高，則 優先使用事件策略
- 如果 多個策略一致看多，則 提高做多信心
- 如果 多個策略一致看空，則 提高做空信心
- 如果 策略意見分歧，則 降低倉位或觀望

---

## 風險控管與心理面

### 一、部位監控風控

#### 1. 偏離預測風控
- **規則**：
  - 如果 實際走勢偏離預測 > 強烈警告閾值，則 建議立刻處理（停損/減碼/鎖利）
  - 如果 實際走勢偏離預測 > 中度風險閾值 且 <= 強烈警告閾值，則 提醒你注意，可以由你判斷需不需要調整
  - 如果 實際走勢偏離預測 <= 中度風險閾值，則 波動還在預期內

#### 2. 主力倒貨風控
- **規則**：
  - 如果 主力倒貨 且 價格開始下跌，則 觸發 🔴 強烈警告，建議立刻減碼或停損

#### 3. 族群轉弱風控
- **規則**：
  - 如果 族群轉弱 且 個股也轉弱，則 觸發 🟠 中度風險，建議減碼或出場

#### 4. 外資/投信突然砍風控
- **規則**：
  - 如果 外資/投信突然砍 且 個股價格開始下跌，則 觸發 🔴 強烈警告，建議立刻處理

### 二、系統級風控

#### 1. 最大單筆風險
- **規則**：
  - 如果 單筆交易風險 > 最大單筆風險設定，則 拒絕交易或減少倉位

#### 2. 單日最大虧損
- **規則**：
  - 如果 當日總虧損 > 單日最大虧損設定，則 停止所有新交易

#### 3. 最多同時持股數量
- **規則**：
  - 如果 當前持股數量 >= 最多同時持股數量設定，則 拒絕新交易

### 三、心理面與紀律

#### 1. J-GOD 人格準則
- **冷靜**：不情緒化決策
- **精準**：只算機率，不做預言
- **不 FOMO**：不追不該追的
- **像老練操盤手**：該退就退、該殺就殺
- **不怕停損**：停損是保護，不是失敗
- **永遠保留子彈**：永遠保留一定比例現金
- **風險永遠第一**：風險控制優先於獲利

#### 2. 交易紀律
- **規則**：
  - 如果 不符合 J-GOD 建議，則 不執行交易
  - 如果 觸發停損條件，則 立即執行停損，不猶豫
  - 如果 觸發停利條件，則 執行停利，不貪心
  - 如果 市場狀態不明，則 觀望，不強迫交易

---

## 實務操作步驟

### 一、開盤前準備（盤前 30-60 分鐘）

#### 1. J-GOD 自動準備
- 今日大盤預測報告
- 今日族群強弱
- 今日潛在爆發股 Top List
- 今日期指偏多/偏空/區間
- 今日關鍵事件 & 可能受影響標的

#### 2. 使用者動作
- 看螢幕 1（市場宇宙）+ 螢幕 3（你部位）
- 決定：今天要偏多？偏空？休息日？

### 二、盤中操作（戰鬥時間）

#### 1. 螢幕監控
- **螢幕 1**：看市場大方向有沒有走偏預測
- **螢幕 2**：盯你正在操作的股票/期指
- **螢幕 3**：看自己部位的變化
- **螢幕 5**：隨時看有無警報彈出

#### 2. 交易流程
- 你下單 → 告訴股神 → 股神記錄 & 監控

### 三、收盤後結算（復盤+進化）

#### 1. J-GOD 自動產出
- 今日真實倉績效
- 今日虛擬倉績效
- 兩者差異原因
- 你當日最好的決策/最差的決策
- 若用股神的建議全做，會發生什麼事

#### 2. 自我進化
- 每天疊加，就是你和股神一起變成真正的「頂尖操盤手」的過程

---

## 實戰案例整理

### 案例一：大盤預測準確

**情境**：
- J-GOD 盤前預測：大盤偏多機率 68%，預估區間 +40 ~ +90 點
- 實際結果：大盤上漲 +65 點

**判斷**：
- J-GOD 預測準確，符合預期

**行動**：
- 如果 有跟隨 J-GOD 建議做多，則 獲利
- 如果 沒有跟隨，則 檢討為什麼沒有跟隨

### 案例二：觀察股 Top 5 表現

**情境**：
- J-GOD 盤前選出觀察股 Top 5：2330、2369、8046、6531、6669
- 實際結果：2330 上漲 2.5%、2369 上漲 1.8%、8046 上漲 3.2%、6531 下跌 0.5%、6669 上漲 1.2%

**判斷**：
- 4 檔上漲，1 檔下跌，整體表現良好

**行動**：
- 如果 有跟隨 J-GOD 建議買入，則 獲利
- 如果 沒有跟隨，則 檢討為什麼沒有跟隨

### 案例三：部位監控警報

**情境**：
- 你持有 2330，J-GOD 預測應該持續強勢
- 實際結果：2330 突然轉弱，觸發 🟠 中度風險警報

**判斷**：
- 部位偏離預測，需要留意

**行動**：
- 如果 觸發中度風險，則 可以減碼或出場
- 如果 觸發強烈警告，則 建議立刻處理（停損/減碼/鎖利）

---

## AI 延伸補強

### 一、系統架構設計

#### 1. 雲端主機（J-GOD Server）
- **功能**：
  - 跑所有 J-GOD 的程式邏輯
  - 資料抓取（行情、籌碼、財報）
  - 預測模型（大盤、個股、期指）
  - 虛擬交易引擎
  - 警報引擎
- **特性**：永遠開著，不綁個人電腦

#### 2. 雲端資料庫（J-GOD DB）
- **存儲內容**：
  - 歷史價格、因子、指標
  - 真實交易紀錄
  - 虛擬交易紀錄
  - 每天大盤/個股預測結果
  - 每一個警報產生的時間、原因
  - J-GOD 的設定（停損規則、資金上限、策略開關）
- **特性**：只要 DB 在，你換幾台電腦都沒差

#### 3. 外部資料來源（Data APIs）
- **台股資料**：FinMind / TDX / XQ SDK
- **期指、選擇權**：期交所 / 第三方 API
- **財報、基本面**：TEJ / FinMind / 公開資訊觀測站爬蟲
- **美股 & ADR & 匯率**：Polygon / Alpha Vantage / 其他國外 API

#### 4. 多螢幕控制台（5 個螢幕）
- **特性**：Web 面板（瀏覽器打開一個網址），被切成 5 個區域/Tab
- **換電腦流程**：
  1. 插上 5 個螢幕
  2. 開瀏覽器登入 J-GOD
  3. 一模一樣

### 二、資料架構設計

#### 1. symbols 表（股票 & 產品清單）
- **欄位**：symbol、name、type、sector、market

#### 2. prices 表（歷史 & 盤中價格）
- **欄位**：symbol、datetime、open、high、low、close、volume、turnover

#### 3. factors 表（技術 + 籌碼 + 資金 + 基本面指標）
- **欄位**：symbol、date、ma_5、ma_20、rsi_14、kd_j、foreign_buy、it_buy、dealer_buy、margin_change、short_change、fundamental_score、sector_money_flow_score、option_iv、option_skew

#### 4. predictions 表（J-GOD 每天的預測）
- **欄位**：symbol、date/time、horizon、prob_up、prob_down、target_price_1、target_price_2、target_price_3、model_type、confidence_score

#### 5. signals 表（實際給你的「操作建議」）
- **欄位**：symbol、datetime、action、entry_range_low、entry_range_high、take_profit_1、take_profit_2、stop_loss、strategy_id、reason

#### 6. trades_real 表（你的真實交易）
- **欄位**：user_id、symbol、datetime、side、qty、price、from_signal_id、notes

#### 7. trades_paper 表（虛擬交易）
- **欄位**：（同 trades_real）+ mode（auto/manual）

#### 8. alerts 表（警報紀錄）
- **欄位**：alert_id、datetime、level、symbol、type、message、resolved

#### 9. user_profile/settings 表（你的偏好 & 風控）
- **欄位**：最大單筆風險、單日最大虧損、最多同時持股數量、偏好多頭/空頭/波段/當沖、是否允許晚上看美股影響策略、各種策略的開關

### 三、策略引擎核心流程

#### 1. 盤前準備（Pre-Market）
- 從 DB 抓最新：價格/籌碼/基本面/事件
- Fundamental Engine 判斷：哪些公司體質優秀/爛到要避開
- Multi-Strategy Engine 根據：今天是趨勢盤？震盪盤？事件盤？幫每個策略分配權重
- ML Engine 給出：大盤今日漲跌機率、各股/族群短期上漲機率
- Options Engine + Global Money Flow 判斷：今天整體風險高/低、是否適合加碼/減碼
- 最後合成一份：《J-GOD 盤前戰情報告》

#### 2. 盤中即時決策（Real-Time）
- 每 X 秒（例如 5 秒）跑一次
- 更新大盤/期指/個股最新行情
- 檢查：哪些股票觸發進場價格、哪些到達停利區、哪些跌破停損
- Position Guardian 檢查：你「真實倉」有沒有變危險、有沒有偏離原本預測太多
- Alert Engine：若某項條件觸發 → 產生警報

#### 3. 收盤評估 & 自我進化（After-Market）
- 拿「預測」vs「實際結果」
- 拿「signal」vs「trades_real」
- 拿「trades_real」vs「trades_paper」
- ML Engine 用這些資料更新模型參數
- 生出一份：《今日戰後檢討報告》

---

## J-GOD 系統可吸收的規則

### 一、系統定位規則

[RULE]
IF system_name = "J-GOD"
THEN system_type = "個人量化自營部 + 市場情報局 + AI 教練 + 風險管制官"

[RULE]
IF jgod_core_function = "預測"
THEN predict_targets = ["大盤", "期指", "族群", "個股", "爆發機率"]

[RULE]
IF jgod_core_function = "監控"
THEN monitor_targets = ["真實部位", "虛擬部位"]

[RULE]
IF jgod_core_function = "進化"
THEN evolution_method = ["虛擬倉", "回測", "優化策略"]

### 二、五螢幕配置規則

[RULE]
IF screen = "Screen 1"
THEN display_content = ["大盤方向矩陣", "期指攻防總覽", "關鍵宏觀指標", "事件面雷達簡表"]

[RULE]
IF screen = "Screen 2"
THEN display_content = ["關注股票3-5檔+期指", "短線爆拉/異常行為", "期指專區"]

[RULE]
IF screen = "Screen 3"
THEN display_content = ["真實倉", "虛擬倉", "部位守護神", "你vs股神績效儀表板"]

[RULE]
IF screen = "Screen 4"
THEN display_content = ["歷史回測結果", "模型訓練", "不同策略績效比較", "新特徵實驗", "模擬不同參數", "報表輸出"]

[RULE]
IF screen = "Screen 5"
THEN display_content = ["即時警報", "系統健康監控"]

### 三、期指預測規則

[RULE]
IF futures_prediction_engine_runs
THEN calculate = [
    "今日收紅/收黑機率",
    "預估漲跌點數區間",
    "多空攻防狀態",
    "盤中反轉機率",
    "尾盤拉抬/殺盤機率",
    "最佳進場/停利/停損延伸區間"
]

[RULE]
IF prob_up > 60 AND estimated_range > 0
THEN market_direction = "偏多"

[RULE]
IF prob_down > 60 AND estimated_range < 0
THEN market_direction = "偏空"

[RULE]
IF reversal_probability > 30
THEN need_to_watch_reversal = true

[RULE]
IF tail_lift_probability > 50
THEN tail_may_go_up = true

[RULE]
IF tail_kill_probability > 50
THEN tail_may_go_down = true

### 四、虛擬交易規則

[RULE]
IF paper_trading_system_runs
THEN features = [
    "與真實行情同步",
    "你可以按「虛擬買/虛擬賣」",
    "J-GOD也會根據自己的訊號下虛擬單",
    "每日/每週/每月統計虛擬績效",
    "與你的真實績效比較"
]

[RULE]
IF paper_trade_mode = "Auto"
THEN jgod_auto_execute = true

[RULE]
IF paper_trade_mode = "Manual"
THEN user_manual_execute = true

### 五、交易日誌規則

[RULE]
IF user_executes_real_trade
THEN log_to_trade_log(
    symbol=user_input.symbol,
    qty=user_input.qty,
    price=user_input.price,
    timestamp=current_time,
    market_state=current_market_state,
    jgod_suggestion=previous_jgod_signal
)

[RULE]
IF trade_logged
THEN analyze = [
    "算你的勝率、平均報酬、最大回撤",
    "分析你是偏好追高、撿便宜、拉回買",
    "找出最賺錢的策略類型",
    "找出最虧錢的行為模式（例如愛凹單、不停損）"
]

### 六、部位監控規則

[RULE]
IF position_guardian_checks
THEN check_every_second = [
    "當初預測應該怎麼走",
    "現在實際走勢有沒有偏離",
    "族群有沒有一起轉弱",
    "主力有沒有開始出貨",
    "外資/投信/自營這5-15分鐘內動作有沒有變"
]

[RULE]
IF position_deviation > strong_warning_threshold
THEN alert_level = "🔴 強烈警告"
AND suggested_action = "建議立刻處理（停損/減碼/鎖利）"

[RULE]
IF position_deviation > medium_risk_threshold AND position_deviation <= strong_warning_threshold
THEN alert_level = "🟠 中度風險"
AND suggested_action = "提醒你注意，可以由你判斷需不需要調整"

[RULE]
IF position_deviation <= medium_risk_threshold
THEN alert_level = "🟢 一切正常"
AND suggested_action = "波動還在預期內"

[RULE]
IF main_force_dumping AND price_starting_to_fall
THEN trigger_alert = "🔴 強烈警告"

[RULE]
IF sector_turning_weak AND stock_also_turning_weak
THEN trigger_alert = "🟠 中度風險"

[RULE]
IF foreign_it_suddenly_selling AND price_starting_to_fall
THEN trigger_alert = "🔴 強烈警告"

### 七、即時警報規則

[RULE]
IF alert_engine_detects
THEN alert_types = [
    "市場級：大盤急殺、大盤急拉、成交量急凍/爆量",
    "族群級：半導體突然由紅翻綠、AI/車用/金融突然爆量",
    "個股級：你持有的股：主力倒貨、轉弱、脫離股神預測軌道",
    "期指級：多空反轉、尾盤攻防異常",
    "系統級：API異常、資料延遲、策略模組失效"
]

[RULE]
IF market_crash_detected
THEN alert_level = "critical"
AND alert_message = "大盤急殺"

[RULE]
IF market_surge_detected
THEN alert_level = "critical"
AND alert_message = "大盤急拉"

[RULE]
IF main_force_dumping_detected
THEN alert_level = "warning"
AND alert_message = "主力倒貨"

[RULE]
IF sector_reversal_detected
THEN alert_level = "warning"
AND alert_message = "族群反轉"

[RULE]
IF futures_reversal_detected
THEN alert_level = "warning"
AND alert_message = "期指盤中反轉"

[RULE]
IF position_deviation_detected
THEN alert_level = "info"
AND alert_message = "你的持股偏離股神預測"

[RULE]
IF system_anomaly_detected
THEN alert_level = "critical"
AND alert_message = "系統異常：API掛掉/資料延遲/某模組失效"

### 八、資料架構規則

[RULE]
IF create_symbols_table
THEN columns = ["symbol", "name", "type", "sector", "market"]

[RULE]
IF create_prices_table
THEN columns = ["symbol", "datetime", "open", "high", "low", "close", "volume", "turnover"]

[RULE]
IF create_factors_table
THEN columns = ["symbol", "date", "ma_5", "ma_20", "rsi_14", "kd_j", "foreign_buy", "it_buy", "dealer_buy", "margin_change", "short_change", "fundamental_score", "sector_money_flow_score", "option_iv", "option_skew"]

[RULE]
IF create_predictions_table
THEN columns = ["symbol", "date/time", "horizon", "prob_up", "prob_down", "target_price_1", "target_price_2", "target_price_3", "model_type", "confidence_score"]

[RULE]
IF create_signals_table
THEN columns = ["symbol", "datetime", "action", "entry_range_low", "entry_range_high", "take_profit_1", "take_profit_2", "stop_loss", "strategy_id", "reason"]

[RULE]
IF create_trades_real_table
THEN columns = ["user_id", "symbol", "datetime", "side", "qty", "price", "from_signal_id", "notes"]

[RULE]
IF create_trades_paper_table
THEN columns = ["(同trades_real)", "mode (auto/manual)"]

[RULE]
IF create_alerts_table
THEN columns = ["alert_id", "datetime", "level", "symbol", "type", "message", "resolved"]

[RULE]
IF create_user_profile_settings_table
THEN columns = ["最大單筆風險", "單日最大虧損", "最多同時持股數量", "偏好多頭/空頭/波段/當沖", "是否允許晚上看美股影響策略", "各種策略的開關"]

### 九、策略引擎流程規則

[RULE]
IF pre_market_phase
THEN steps = [
    "從DB抓最新：價格/籌碼/基本面/事件",
    "Fundamental Engine判斷：哪些公司體質優秀/爛到要避開",
    "Multi-Strategy Engine根據：今天是趨勢盤？震盪盤？事件盤？幫每個策略分配權重",
    "ML Engine給出：大盤今日漲跌機率、各股/族群短期上漲機率",
    "Options Engine + Global Money Flow判斷：今天整體風險高/低、是否適合加碼/減碼",
    "最後合成一份：《J-GOD 盤前戰情報告》"
]

[RULE]
IF real_time_phase
THEN steps = [
    "每X秒（例如5秒）跑一次",
    "更新大盤/期指/個股最新行情",
    "檢查：哪些股票觸發進場價格、哪些到達停利區、哪些跌破停損",
    "Position Guardian檢查：你「真實倉」有沒有變危險、有沒有偏離原本預測太多",
    "Alert Engine：若某項條件觸發→產生警報"
]

[RULE]
IF after_market_phase
THEN steps = [
    "拿「預測」vs「實際結果」",
    "拿「signal」vs「trades_real」",
    "拿「trades_real」vs「trades_paper」",
    "ML Engine用這些資料更新模型參數",
    "生出一份：《今日戰後檢討報告》"
]

### 十、版本路線規則

[RULE]
IF version = "v0"
THEN tools = ["Google雲端硬碟", "Excel/Google Sheet", "Google Doc", "GPT"]
AND features = ["J-GOD盤前戰報（由GPT產出）", "交易日誌/虛擬交易紀錄（Excel）", "收盤檢討（文字+數字）"]
AND do_not_do = ["程式", "API", "伺服器"]

[RULE]
IF version = "v1"
THEN tools = ["你電腦上的Python", "Excel"]
AND features = ["統計勝率、報酬率", "幫你做簡單排序、策略效果分析"]
AND do_not_need = ["伺服器", "付費API"]

[RULE]
IF version = "v2"
THEN tools = ["Python", "Streamlit/Flask"]
AND features = ["用瀏覽器看J-GOD面板（大盤、觀察股、部位）"]
AND run_location = "你電腦跑，網址是localhost，不對外開放"

[RULE]
IF version = "v3"
THEN migrate_to = "雲端伺服器"
AND use_database = "雲端資料庫"
AND enable_features = ["五螢幕戰情室正式上線"]

### 十一、資料遷移規則

[RULE]
IF design_for_migration
THEN follow_principles = [
    "資料先用CSV/Excel存，但結構照「未來資料庫的欄位」來設計",
    "程式寫成「讀檔→處理→輸出」，不要綁死某一台電腦的路徑",
    "設定值（API key、路徑）→放一個config.json/.env，之後搬到伺服器只要改這些設定就好"
]

[RULE]
IF migrate_to_server
THEN steps = [
    "把資料檔+程式整個壓成一包",
    "丟到雲端主機",
    "裝一樣的Python環境",
    "改一下設定（例如：從讀本機CSV改成讀雲端DB）"
]

### 十二、J-Score 判斷規則

[RULE]
IF jscore >= 70
THEN company_health = "超健康"
AND investment_suggestion = "適合長期持有"

[RULE]
IF jscore >= 50 AND jscore < 70
THEN company_health = "普通"
AND investment_suggestion = "需要進一步分析"

[RULE]
IF jscore < 30
THEN company_health = "雷股體質"
AND investment_suggestion = "應避免投資"

### 十三、多策略選擇規則

[RULE]
IF market_type = "趨勢盤" AND trend_strategy_win_rate > threshold
THEN priority_strategy = "趨勢策略"

[RULE]
IF market_type = "震盪盤" AND reversal_strategy_win_rate > threshold
THEN priority_strategy = "反轉策略"

[RULE]
IF market_type = "事件盤" AND event_strategy_win_rate > threshold
THEN priority_strategy = "事件策略"

[RULE]
IF multiple_strategies_agree_on_long
THEN long_confidence = "提高"

[RULE]
IF multiple_strategies_agree_on_short
THEN short_confidence = "提高"

[RULE]
IF strategies_disagree
THEN position_size = "降低"
OR action = "觀望"

### 十四、J-GOD 人格規則

[RULE]
IF jgod_personality = "冷靜"
THEN decision_making_style = "客觀分析，不情緒化"

[RULE]
IF jgod_personality = "精準"
THEN prediction_style = "只算機率，不做預言"

[RULE]
IF jgod_personality = "不FOMO"
THEN avoid_actions = ["追不該追的", "FOMO式進場"]

[RULE]
IF jgod_personality = "像老練操盤手"
THEN behavior = ["該退就退", "該殺就殺", "不怕停損"]

[RULE]
IF jgod_personality = "風險永遠第一"
THEN priority = "風險控制優先於獲利"

[RULE]
IF jgod_personality = "永遠保留子彈"
THEN cash_reserve = "永遠保留一定比例現金"

---

## 總結

本文件提供了 J-GOD 股神作戰系統的完整架構與實作指南，從系統定位、核心功能、五螢幕配置、核心模組、對標頂尖機構的缺失分析，到系統架構、資料架構、策略引擎流程，以及版本路線與實作階段。

**核心價值**：
1. **完整系統架構**：從手動版到雲端自動化系統的完整路線圖
2. **對標頂尖機構**：整合巴菲特、Citadel、Renaissance、Bridgewater、Two Sigma 的視角
3. **可程式化規則**：所有規則都轉換成 IF/THEN 格式，方便未來程式化
4. **資料架構設計**：完整的資料表結構，方便未來建立資料庫
5. **策略引擎流程**：從盤前準備到盤中決策到收盤進化的完整流程

**下一步行動**：
1. 階段 0：J-GOD v0（完全手動版，Excel + Google Doc + GPT）
2. 階段 1：J-GOD v1（半自動本機版，Python + Excel）
3. 階段 2：J-GOD v1.5（本機 Web 介面版，Streamlit/Flask）
4. 階段 3：J-GOD v2（開始連免費或便宜的 API）
5. 階段 4：J-GOD v3（雲端搬家 + 自動化）

---

**文件版本**：v1.0  
**建立日期**：2025-01-XX  
**適用系統**：J-GOD 股神作戰系統

