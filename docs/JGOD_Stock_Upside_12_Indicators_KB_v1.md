# J-GOD 股票上漲判斷模型（12 指標）— KB 版本 v1.0

**版本**: 1.0  
**最後更新**: 2025-12-04  
**用途**: Rule-Based Filter、LLM 推論、Path A/B/C 訓練

本文件為 J-GOD Prediction Engine 的基礎知識庫。

---

====================================================

[#SECTION] 1. 價格結構（Price Structure）

====================================================

[#INDICATOR]

Code: P01

Name: 趨勢斜率（Trend Slope）

Category: Price

Definition: 透過高點/低點結構與 MA20/M60 斜率判斷趨勢方向。

Logic:
  - MA20 斜率 > 0 → 上漲機率提高。
  - 高低點結構上升 = 主升段前置訊號。

Usage_Rules:
  - 不得單獨使用，須搭配量能結構。
  - 趨勢破壞時，所有指標優先降權。

---

[#INDICATOR]

Code: P02

Name: 多頭均線排列（MA20 > MA60 > MA120）

Category: Price

Definition: 判斷主力成本與趨勢的三線排列。

Logic:
  - 三線多頭 = 主升段結構。
  - 股價在 MA20 之上 = 最強。

Usage_Rules:
  - 不適用於極短線盤整股。

---

[#INDICATOR]

Code: P03

Name: 量能結構（Volume Structure）

Category: Price

Definition: 放量上漲 / 縮量回檔的完整比對。

Logic:
  - 放量上漲＝主力買進。
  - 回檔縮量＝洗盤成功。

Usage_Rules:
  - 長黑爆量 = 出貨訊號（權重負向）。

---

[#INDICATOR]

Code: P04

Name: 套牢壓力（VAP Supply Zone）

Category: Price

Definition: 檢查上方成交密集區是否形成壓力。

Logic:
  - 上方無壓力 → 容易飆。
  - VAP 壓力越深，越難突破。

Usage_Rules:
  - 需搭配趨勢、量能同時判斷。

---

====================================================

[#SECTION] 2. 籌碼（Capital Flow）

====================================================

[#INDICATOR]

Code: C01

Name: 法人買賣（外資 / 投信 / 自營）

Category: Capital

Definition: 連續買超天數與買超金額。

Logic:
  - 投信連買 ≥ 3 天 → 最強。
  - 外資連續偏多 → 中長線趨勢。

Usage_Rules:
  - 三大法人同買時，上漲機率最大。

---

[#INDICATOR]

Code: C02

Name: 大戶持股比例（Major Holders）

Category: Capital

Definition: 前 15% 大戶持股變化。

Logic:
  - 主力吸籌＝大戶持股上升。
  - 大戶減碼＝風險警訊。

Usage_Rules:
  - 散戶比率需同步降低才有效。

---

[#INDICATOR]

Code: C03

Name: 散戶比率（Retail Participation）

Category: Capital

Definition: 散戶持股比例佔比。

Logic:
  - 散戶高 → 容易套牢、漲不動。
  - 散戶低 → 主力易拉抬。

Usage_Rules:
  - 極端時（散戶大增）權重負向。

---

====================================================

[#SECTION] 3. 財報基本面（Fundamental）

====================================================

[#INDICATOR]

Code: F01

Name: 成長動能（Revenue / Profit Growth）

Category: Fundamental

Definition: 收入、毛利、淨利是否年增、季增。

Logic:
  - 三率三升 = 中長線主升段。
  - YOY 跳水時，技術面失效。

Usage_Rules:
  - 單季不可單獨使用，需看 3 季趨勢。

---

[#INDICATOR]

Code: F02

Name: 毛利率趨勢（GM Trend）

Category: Fundamental

Definition: 毛利率是否連續走高。

Logic:
  - 毛利率提升＝產品競爭力增加。

Usage_Rules:
  - 高毛利股比低毛利股權重更高。

---

[#INDICATOR]

Code: F03

Name: 自由現金流（FCF）

Category: Fundamental

Definition: 營運現金流 − 資本支出。

Logic:
  - FCF > 0 → 真成長。
  - FCF < 0 → 財務風險。

Usage_Rules:
  - 3 年負 FCF → 長期降評。

---

====================================================

[#SECTION] 4. 事件與情緒（Catalyst & Sentiment）

====================================================

[#INDICATOR]

Code: E01

Name: 事件觸發（Event-driven）

Category: Catalyst

Definition: 新訂單 / AI 題材 / 併購 / 法說會上修。

Logic:
  - 事件常為起漲主因。

Usage_Rules:
  - 事件強 + 籌碼強 = 大波段。

---

[#INDICATOR]

Code: S01

Name: 市場情緒（Market Sentiment）

Category: Sentiment

Definition: NASDAQ、台積電、VIX、匯率、量能等。

Logic:
  - 情緒正向 → 個股更容易漲。
  - 情緒負向 → 所有多頭都變弱。

Usage_Rules:
  - 必須先判斷市場方向，再看個股。

---

====================================================

[#SECTION] 5. 綜合規則（Scoring Summary）

====================================================

Logic:
  - 若 12 指標滿足 ≥ 8 → 主升段候選。
  - 若滿足 5–7 → 強勢股區間。
  - 若滿足 ≤ 3 → 無上漲空間。
  - 籌碼逆轉（散戶暴增、大戶減碼）→ 直接降評。

---

End of KB File.

