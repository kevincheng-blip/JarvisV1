# ==============================================================

[#TITLE] J-GOD 股票上漲判斷模型（60 指標）— KB 版本 v1.0

# ==============================================================

Purpose:

- 作為 Prediction Engine 的基礎知識庫。

- 供 LLM 推論、Rule-based 判斷、Path A/B/C 因子使用。

- 各指標皆為可解析、可程式化、可量化的資訊單位。

==============================================================

[#SECTION] 1. 價格結構（Price Structure / Technical）12 指標

==============================================================

[#INDICATOR]

Code: P01

Name: 趨勢斜率（Trend Slope）

Category: Price

Definition: 透過 MA20、MA60 的斜率與高低點結構（HH/HL）判斷趨勢方向。

Logic:
  - MA20 slope > 0 → 多頭偏多。
  - 趨勢上升＝股票最容易上漲的條件。
  - 趨勢破壞（跌破前低）則進入警戒。

Usage_Rules:
  - 不得單獨使用，須搭配 P07 量能結構。

Data_Source:
  - Price: taiwan_stock_price
  - Derived: MA, slope, HH/HL

Risk_Warning:
  - 假突破常在量能不足時出現。

---

[#INDICATOR]

Code: P02

Name: 多頭均線排列（MA20 > MA60 > MA120）

Category: Price

Definition: 三條均線判斷長中短期趨勢排列。

Logic:
  - MA20 > MA60 > MA120 = 主升段最強形態。
  - 股價站上 MA20 = 進行式多頭。

Usage_Rules:
  - 平盤量能太低時，MA 容易被假突破。

Data_Source:
  - Price: taiwan_stock_price
  - Indicator: MA20/60/120

Risk_Warning:
  - 均線延遲性高，需配合斜率與量能。

---

[#INDICATOR]

Code: P03

Name: 均線糾結突破（MA Squeeze Breakout）

Category: Price

Definition: 多條均線密集糾結後的突破方向。

Logic:
  - 糾結後上突破 → 多頭動能會加速。

Usage_Rules:
  - 不看單日，需至少連續兩日突破。

Data_Source:
  - Price: taiwan_stock_price

Risk_Warning:
  - 假突破率高於均線排列。

---

[#INDICATOR]

Code: P04

Name: K 棒結構（K-line Structure）

Category: Price

Definition: 重要 K 棒型態：長紅、吞噬、紅三兵、長下影等。

Logic:
  - 多方 K 棒表示買盤主動性強。
  - 長上影帶量＝警告。

Usage_Rules:
  - 須搭配 P07 (Volume) 才有效。

Data_Source:
  - Price: taiwan_stock_price

Risk_Warning:
  - K 棒單日訊號不可靠，需搭配趨勢。

---

[#INDICATOR]

Code: P05

Name: 支撐/壓力（Support & Resistance）

Category: Price

Definition: 由歷史密集交易區計算關鍵 S/R 區域。

Logic:
  - 壓力突破＝常伴隨放量。

Usage_Rules:
  - 不可使用過短時間尺度判斷。

Data_Source:
  - Price: taiwan_stock_price

Risk_Warning:
  - 若無量能支撐，突破易失敗。

---

[#INDICATOR]

Code: P06

Name: 缺口（Gap）

Category: Price

Definition: 向上/向下跳空缺口的性質。

Logic:
  - 突破缺口＝強勢信號。
  - 衰竭缺口＝反轉訊號。

Usage_Rules:
  - 需搭配 P07 Volume。

Data_Source:
  - Price: taiwan_stock_price

Risk_Warning:
  - 高波動股常出現假缺口。

---

[#INDICATOR]

Code: P07

Name: 量能結構（Volume Structure）

Category: Price

Definition: 分辨放量上漲、縮量下跌、爆量長黑。

Logic:
  - 縮量回檔＝洗盤。
  - 放量上攻＝主力進場。

Usage_Rules:
  - 股價下跌＋放量＝危險訊號。

Data_Source:
  - Price: taiwan_stock_price

Risk_Warning:
  - 遇成交量異常（除權息）需調整。

---

[#INDICATOR]

Code: P08

Name: 量價背離（Volume-Price Divergence）

Category: Price

Definition: 價漲量縮、價跌量增等背離現象。

Logic:
  - 價跌量增＝有主力倒貨嫌疑。

Usage_Rules:
  - 需至少三日資料確認。

Data_Source:
  - Price: taiwan_stock_price

Risk_Warning:
  - 短線股常有假訊號。

---

[#INDICATOR]

Code: P09

Name: 布林通道（Bollinger Band）

Category: Price

Definition: 判斷波動度與突破。

Logic:
  - 突破上軌＝動能啟動。

Usage_Rules:
  - 不適用極低量股票。

Data_Source:
  - Price: taiwan_stock_price

Risk_Warning:
  - 上軌突破後可能立刻回測。

---

[#INDICATOR]

Code: P10

Name: RSI / KD / MACD（Momentum）

Category: Price

Definition: 動能指標綜合判斷。

Logic:
  - RSI > 50 = 多方優勢。
  - KD <20 金叉 = 短線買點。

Usage_Rules:
  - 須搭配趨勢，不可單獨用。

Data_Source:
  - Price: taiwan_stock_price

Risk_Warning:
  - KD 在盤整股失效率高。

---

[#INDICATOR]

Code: P11

Name: ATR 波動度（ATR）

Category: Price

Definition: 計算市場波動度。

Logic:
  - 波動低＝可能準備爆發。

Usage_Rules:
  - 適合波段判斷。

Data_Source:
  - Price: taiwan_stock_price

Risk_Warning:
  - 損失控管必須搭配 ATR。

---

[#INDICATOR]

Code: P12

Name: 套牢壓力（VAP）

Category: Price

Definition: 透過 VAP 計算上方/下方壓力。

Logic:
  - 上方無壓力＝爆發可能高。

Usage_Rules:
  - VAP 要有至少 6 個月資料。

Data_Source:
  - Price + 自行計算 VAP

Risk_Warning:
  - 新上市股票無法使用。

---

==============================================================

[#SECTION] 2. 籌碼結構（Capital Flow）9 指標

==============================================================

[#INDICATOR]

Code: C01

Name: 外資買賣超（Foreign Investors）

Category: Capital

Definition: 外資連續買賣超趨勢。

Logic:
  - 連買≥3日＝中線偏多。

Usage_Rules:
  - 與投信共振最重要。

Data_Source:
  - taiwan_stock_institutional_investors

Risk_Warning:
  - 指數調整日容易失真。

---

[#INDICATOR]

Code: C02

Name: 投信買賣超（Investment Trust）

Category: Capital

Definition: 投信買賣超趨勢。

Logic:
  - 投信連買＝最強訊號。

Usage_Rules:
  - 投信與外資同向＝高勝率。

Data_Source:
  - institutional_investors

Risk_Warning:
  - 投信易在月底作帳，需額外過濾。

---

[#INDICATOR]

Code: C03

Name: 自營商買賣（Dealer）

Category: Capital

Definition: 自營商避險/套利部位。

Logic:
  - 偏短線參考。

Usage_Rules:
  - 不可單獨作多空判斷。

Data_Source:
  - institutional_investors

---

[#INDICATOR]

Code: C04

Name: 大戶持股比（Major Holders）

Category: Capital

Definition: 前 15% 大戶比率。

Logic:
  - 上升＝主力吸籌。

Usage_Rules:
  - 必須搭配散戶比下降才有效。

Data_Source:
  - taiwan_stock_shareholding

---

[#INDICATOR]

Code: C05

Name: 散戶比率（Retail Ratio）

Category: Capital

Definition: 散戶持股比例。

Logic:
  - 散戶越多＝越難漲。

Usage_Rules:
  - 融資大增時同步增加＝警訊。

Data_Source:
  - taiwan_stock_shareholding

---

[#INDICATOR]

Code: C06

Name: 分點籌碼（Broker Branch）

Category: Capital

Definition: 主力分點買賣超行為。

Logic:
  - 特定主力連續買＝重大訊號。

Usage_Rules:
  - 須過濾當沖分點。

Data_Source:
  - taiwan_stock_day_trading

---

[#INDICATOR]

Code: C07

Name: 主力成本（Weighted Cost）

Category: Capital

Definition: 透過分點與價量推估主力成本。

Logic:
  - 股價 > 主力成本＝多頭控制。

Usage_Rules:
  - 新股無法使用。

Data_Source:
  - Price + day_trading

---

[#INDICATOR]

Code: C08

Name: 融資（Margin）

Category: Capital

Definition: 融資餘額與變化。

Logic:
  - 融資爆量＝危險。

Usage_Rules:
  - 與散戶比率一起看。

Data_Source:
  - taiwan_stock_margin_purchase_short_sale

---

[#INDICATOR]

Code: C09

Name: 融券（Short）

Category: Capital

Definition: 融券餘額與變化。

Logic:
  - 增加＝可能軋空。

Usage_Rules:
  - 必須搭配價格走勢。

Data_Source:
  - margin_purchase_short_sale

---

==============================================================

[#SECTION] 3. 財報 Fundamental 8 指標

==============================================================

[#INDICATOR]

Code: F01

Name: 營收（Revenue Growth）

Category: Fundamental

Definition: 月營收年增率/季增率。

Logic:
  - 三季連增＝公司成長確立。

Usage_Rules:
  - 單月不可單獨使用。

Data_Source:
  - taiwan_stock_month_revenue

---

[#INDICATOR]

Code: F02

Name: 毛利率（Gross Margin）

Category: Fundamental

Definition: 毛利率趨勢變化。

Logic:
  - 連3季走升＝超強訊號。

Data_Source:
  - income_statement

---

[#INDICATOR]

Code: F03

Name: 營益率（Operating Margin）

Category: Fundamental

Definition: EPS 與營益表中的營業利益率。

Logic:
  - 代表經營效率。

Data_Source:
  - income_statement

---

[#INDICATOR]

Code: F04

Name: EPS（Earnings）

Category: Fundamental

Definition: 每股盈餘。

Logic:
  - 持續上升→價值上升。

Data_Source:
  - financial_statements

---

[#INDICATOR]

Code: F05

Name: 自由現金流（FCF）

Category: Fundamental

Definition: OCF - Capex。

Logic:
  - FCF > 0 = 企業體質健康。

Data_Source:
  - cash_flows_statement

---

[#INDICATOR]

Code: F06

Name: ROE / ROA

Category: Fundamental

Definition: 股東與資產報酬率。

Logic:
  - ROE 長期提高＝優質企業。

Data_Source:
  - balance_sheet

---

[#INDICATOR]

Code: F07

Name: 負債比（Debt Ratio）

Category: Fundamental

Definition: 總負債/總資產。

Logic:
  - 負債過高＝財務風險。

Data_Source:
  - balance_sheet

---

[#INDICATOR]

Code: F08

Name: 股東權益成長（Equity Growth）

Category: Fundamental

Definition: 股東權益趨勢。

Logic:
  - 權益增＝公司強化。

Data_Source:
  - balance_sheet

---

==============================================================

[#SECTION] 4. 題材與事件 Catalyst 7 指標

==============================================================

[#INDICATOR]

Code: K01

Name: 法說會（Guidance）

Category: Catalyst

Definition: 公司財測上修/下修。

Logic:
  - 上修＝股價大漲。

Data_Source:
  - News (爬蟲 / API)

---

[#INDICATOR]

Code: K02

Name: 新訂單（New Orders）

Category: Catalyst

Definition: 新案、AI/伺服器接單等。

Logic:
  - 新訂單＝基本面最強催化。

Data_Source:
  - News

---

[#INDICATOR]

Code: K03

Name: 併購/擴產（M&A）

Category: Catalyst

Definition: 公司重大投資行為。

Logic:
  - 擴產＝本益比提升可能。

Data_Source:
  - News

---

[#INDICATOR]

Code: K04

Name: 大客戶導入（TSMC/Nvidia/Apple）

Category: Catalyst

Definition: 供應鏈重大事件。

Logic:
  - 最強題材之一。

Data_Source:
  - News

---

[#INDICATOR]

Code: K05

Name: 政策題材（Military/Green）

Category: Catalyst

Definition: 政府政策扶持產業。

Logic:
  - 政策保護＝趨勢可長期。

Data_Source:
  - News

---

[#INDICATOR]

Code: K06

Name: ETF 變動（MSCI/富時/台灣50）

Category: Catalyst

Definition: ETF 納入/剔除。

Logic:
  - 對籌碼影響大。

Data_Source:
  - News + ETF Data

---

[#INDICATOR]

Code: K07

Name: 熱門題材（AI/生技/軍工）

Category: Catalyst

Definition: 市場熱門故事。

Logic:
  - 題材王永遠是盤面強股。

Data_Source:
  - News

---

==============================================================

[#SECTION] 5. 市場情緒 Sentiment 6 指標

==============================================================

[#INDICATOR]

Code: S01

Name: 台積電方向（2330）

Category: Sentiment

Definition: 台灣市場主領航股。

Logic:
  - 2330 多→大盤多。

Data_Source:
  - Price(2330)

---

[#INDICATOR]

Code: S02

Name: NASDAQ 方向

Category: Sentiment

Definition: 全球科技股情緒來源。

Logic:
  - NASDAQ 上漲＝台股科技易強勢。

Data_Source:
  - Yahoo Finance

---

[#INDICATOR]

Code: S03

Name: 台幣匯率

Category: Sentiment

Definition: 外資匯入匯出。

Logic:
  - 台幣升＝外資買股。

Data_Source:
  - taiwan_exchange_rate

---

[#INDICATOR]

Code: S04

Name: 美債殖利率（10Y）

Category: Sentiment

Definition: 利率方向影響科技估值。

Logic:
  - 殖利率下降＝科技股漲。

Data_Source:
  - us_treasury_yield

---

[#INDICATOR]

Code: S05

Name: VIX 恐慌指數

Category: Sentiment

Definition: 全球風險情緒。

Logic:
  - VIX 低＝風險偏好提升。

Data_Source:
  - Yahoo Finance

---

[#INDICATOR]

Code: S06

Name: 大盤成交量

Category: Sentiment

Definition: 市場整體活絡度。

Logic:
  - 量增＝多頭啟動。

Data_Source:
  - Price (index/0050)

---

==============================================================

[#SECTION] 6. 量化風控 Quant 6 指標

==============================================================

[#INDICATOR]

Code: Q01

Name: Sharpe Ratio

Category: Quant

Definition: 報酬/風險比。

Logic:
  - Sharpe 高＝報酬效率好。

Data_Source:
  - Price (derived)

---

[#INDICATOR]

Code: Q02

Name: 波動度（ATR）

Category: Quant

Definition: 市場波動度。

Logic:
  - 波動低＝適合波段。

Data_Source:
  - Price

---

[#INDICATOR]

Code: Q03

Name: 最大回撤 MDD

Category: Quant

Definition: 高點回撤最大幅度。

Logic:
  - MDD 大＝風險高。

Data_Source:
  - Price

---

[#INDICATOR]

Code: Q04

Name: Beta 系統性風險

Category: Quant

Definition: 與大盤連動性。

Logic:
  - Beta 高＝更敏感。

Data_Source:
  - Price

---

[#INDICATOR]

Code: Q05

Name: 因子暴露（Momentum/Value/Quality）

Category: Quant

Definition: 股票在各因子下的暴露度。

Logic:
  - Momentum 高＝主升段可能性高。

Data_Source:
  - Price (derived)

---

[#INDICATOR]

Code: Q06

Name: 持股集中度（Weight Concentration）

Category: Quant

Definition: 單檔在投資組合中的占比。

Logic:
  - 過高＝風控不佳。

Data_Source:
  - Portfolio Engine

---

==============================================================

[#SECTION] 7. 綜合規則 Scoring Summary

==============================================================

Logic:
  - 若 48 核心指標滿足 ≥35 → 明確多頭。
  - 若滿足 25–34 → 偏多。
  - 若滿足 15–24 → 中性。
  - 若滿足 <15 → 偏空。
  - 若籌碼逆轉（大戶減、散戶增）→ 立即降評。

==============================================================

[#SECTION] 8. 衍生品與微觀籌碼（Derivatives & Microstructure）X 系列

==============================================================

[#INDICATOR]

Code: X01

Name: 個股選擇權隱含波動率（IV Level）

Category: Derivatives

Definition: 以該股票相關選擇權的隱含波動率水準作為風險與情緒指標。

Logic:
  - IV 明顯抬升＝市場對該股未來波動預期增加。

Data_Source:
  - Options / TAIFEX / 第三方衍生品資料

Usage_Rules:
  - 僅適用有選擇權商品的標的。

---

[#INDICATOR]

Code: X02

Name: IV Skew（看跌 vs 看漲）

Category: Derivatives

Definition: 比較相同到期日、不同履約價看跌 vs 看漲的隱含波動率差異。

Logic:
  - Put IV >> Call IV＝避險需求強（偏空情緒）。

Data_Source:
  - Options

Usage_Rules:
  - 當 IV 整體偏低時，skew 訊號較弱。

---

[#INDICATOR]

Code: X03

Name: 個股 Put/Call Ratio

Category: Derivatives

Definition: 個股選擇權 Put/Call 成交量或未平倉量比值。

Logic:
  - Ratio 明顯 > 1＝偏空。

Data_Source:
  - Options

---

[#INDICATOR]

Code: X04

Name: 指數 VIX / 等價波動指標

Category: Derivatives

Definition: 以大盤或相關 VIX 指標觀察恐慌程度。

Logic:
  - 高 VIX＝風險偏好下降。

Data_Source:
  - Index Volatility Data

---

[#INDICATOR]

Code: X05

Name: 期貨正逆價差（Futures Basis）

Category: Derivatives

Definition: 期貨 vs 現貨價差。

Logic:
  - 大幅正價差＝市場偏多。

Data_Source:
  - TAIFEX + Index Price

---

[#INDICATOR]

Code: X06

Name: 期貨價差變化（Basis Change）

Category: Derivatives

Definition: 基差日內與數日變化。

Logic:
  - 基差快速縮小＝多方撤退或空方回補。

Data_Source:
  - TAIFEX

---

[#INDICATOR]

Code: X07

Name: 外資指數期貨淨部位

Category: Derivatives

Definition: 外資在台指期/小台指的多空口數差。

Logic:
  - 淨多增加＝偏多。

Data_Source:
  - CFTC / TAIFEX 公開數據

---

[#INDICATOR]

Code: X08

Name: 外資期貨部位變化率

Category: Derivatives

Definition: 外資期貨淨部位的日變化量。

Logic:
  - 快速翻空＝短線風險拉高。

Data_Source:
  - TAIFEX

---

[#INDICATOR]

Code: X09

Name: 個股成交筆數集中度

Category: Microstructure

Definition: 成交筆數是否集中於少數時間/價位。

Logic:
  - 高集中度＝可能有主力掃貨或倒貨。

Data_Source:
  - Tick / 分價量

---

[#INDICATOR]

Code: X10

Name: 委買委賣深度不平衡（Orderbook Imbalance）

Category: Microstructure

Definition: 買盤 vs 賣盤掛單量的差異。

Logic:
  - 買單遠大於賣單＝短線支撐強。

Data_Source:
  - Orderbook（F_Orderbook 引擎）

---

[#INDICATOR]

Code: X11

Name: 最佳五檔掛單變化速度

Category: Microstructure

Definition: 五檔掛單更新頻率與方向。

Logic:
  - 快速撤買＋掛賣＝賣壓主導。

Data_Source:
  - Orderbook

---

[#INDICATOR]

Code: X12

Name: 當沖比率（Day Trading Ratio）

Category: Microstructure

Definition: 當日成交中屬於當沖部位之比例。

Logic:
  - 當沖比極高＝波動放大但趨勢可靠度下降。

Data_Source:
  - taiwan_stock_day_trading

---

[#INDICATOR]

Code: X13

Name: 一檔跳動成交佔比（One-Tick Trades）

Category: Microstructure

Definition: 價格只跳動一檔的成交比率。

Logic:
  - 比例高＝流動性佳、掛單密集。

Data_Source:
  - Tick Data

---

[#INDICATOR]

Code: X14

Name: 大單成交占比（Block Trade Ratio）

Category: Microstructure

Definition: 單筆金額超過門檻的大單占比。

Logic:
  - 大單占比高＝主力活躍。

Data_Source:
  - Tick / Broker Data

---

[#INDICATOR]

Code: X15

Name: 開盤前撮合不平衡

Category: Microstructure

Definition: 開盤前集合競價買賣不平衡程度。

Logic:
  - 嚴重偏買或偏賣＝當日方向參考。

Data_Source:
  - Pre-open Orderbook

---

[#INDICATOR]

Code: X16

Name: 收盤撮合不平衡

Category: Microstructure

Definition: 收盤前最後撮合掛單方向與量。

Logic:
  - 收盤被強力拉高/壓低＝隔日易延續。

Data_Source:
  - Closing Auction Data

---

==============================================================

[#SECTION] 9. Meta / Composite / Regime 綜合指標 M 系列

==============================================================

[#INDICATOR]

Code: M01

Name: 價格結構總分（Price_Composite_Score）

Category: Meta

Definition: 由所有 P 系列指標計算的綜合分數。

Logic:
  - 分數高＝技術面結構健康。

Data_Source:
  - Derived from P01–P12

---

[#INDICATOR]

Code: M02

Name: 籌碼總分（Capital_Composite_Score）

Category: Meta

Definition: 由 C 系列指標加權而成。

Logic:
  - 顯示主力與法人資金偏向。

Data_Source:
  - Derived from C01–C09

---

[#INDICATOR]

Code: M03

Name: 財報體質總分（Fundamental_Composite_Score）

Category: Meta

Definition: 將 F 系列整體量化。

Logic:
  - 高分＝體質優、長線可持有。

Data_Source:
  - Derived from F01–F08

---

[#INDICATOR]

Code: M04

Name: 題材強度分數（Catalyst_Score）

Category: Meta

Definition: 將 K 系列事件與題材量化。

Logic:
  - 強題材＋高分＝最適合作波段。

Data_Source:
  - Derived from K01–K07

---

[#INDICATOR]

Code: M05

Name: 市場情緒分數（Sentiment_Score）

Category: Meta

Definition: 將 S 系列指標合成單一情緒溫度。

Logic:
  - 高分＝風險偏好提高。

Data_Source:
  - Derived from S01–S06

---

[#INDICATOR]

Code: M06

Name: 風控健全度分數（Quant_Risk_Score）

Category: Meta

Definition: 綜合 Sharpe、MDD、波動度的風險品質指標。

Logic:
  - 高分＝風險報酬結構佳。

Data_Source:
  - Derived from Q01–Q06

---

[#INDICATOR]

Code: M07

Name: 成長品質分數（Growth_Quality_Score）

Category: Meta

Definition: 以 F01/F02/F05 與穩定度衡量成長的「品質」而非僅速度。

Logic:
  - 成長穩定＋現金流健康＝高分。

Data_Source:
  - Derived from Fundamental

---

[#INDICATOR]

Code: M08

Name: 價值便宜度分數（Value_Attractiveness）

Category: Meta

Definition: 綜合 PE/PB/PS 與產業平均算出的相對便宜程度。

Logic:
  - 越便宜＝反彈潛力越大（搭配其他指標使用）。

Data_Source:
  - Valuation Metrics

---

[#INDICATOR]

Code: M09

Name: 動能分數（Momentum_Score）

Category: Meta

Definition: 將價格動能、成交量與趨勢綜合成單一數值。

Logic:
  - 高分＝主升段機率高。

Data_Source:
  - Derived from P 系列 + Volume

---

[#INDICATOR]

Code: M10

Name: 籌碼穩定度（Capital_Stability）

Category: Meta

Definition: 觀察大戶持股、散戶比、法人行為的穩定性。

Logic:
  - 穩定且偏多＝主力控盤良好。

Data_Source:
  - Derived from C 系列

---

[#INDICATOR]

Code: M11

Name: 流動性品質（Liquidity_Quality）

Category: Meta

Definition: 結合成交量、價差、orderbook 深度的流動性評分。

Logic:
  - 高流動性＝進出成本低。

Data_Source:
  - Price + Orderbook

---

[#INDICATOR]

Code: M12

Name: 波動 regime 判定（Volatility_Regime）

Category: Meta

Definition: 區分低波 / 常態波 / 高波三種 regime。

Logic:
  - 決定適合的策略（波段/當沖/避險）。

Data_Source:
  - Derived from ATR/StdDev

---

[#INDICATOR]

Code: M13

Name: 大盤相關度（Index_Correlation）

Category: Meta

Definition: 該股與大盤或產業指數的相關係數。

Logic:
  - 高相關＝受大盤影響大。

Data_Source:
  - Price (stock + index)

---

[#INDICATOR]

Code: M14

Name: 產業相對強弱（Sector_Relative_Strength）

Category: Meta

Definition: 該股表現相對同產業指數強弱。

Logic:
  - 長期跑贏產業＝領頭股特徵。

Data_Source:
  - Sector Index

---

[#INDICATOR]

Code: M15

Name: ETF 壓力／支撐分數（ETF_Flow_Impact）

Category: Meta

Definition: ETF 持股與被動資金流對股價的影響程度。

Logic:
  - ETF 大量加碼/賣出＝對股價有實質拉扯力。

Data_Source:
  - ETF Constituents & Flow

---

[#INDICATOR]

Code: M16

Name: 短線過熱程度（ShortTerm_Overheat）

Category: Meta

Definition: 結合 RSI、漲幅、成交量判斷短線過熱。

Logic:
  - 高分＝短線拉回風險高。

Data_Source:
  - Technical + Volume

---

[#INDICATOR]

Code: M17

Name: 修正潛力（Pullback_Potential）

Category: Meta

Definition: 在多頭結構下回檔幅度與位置的評估。

Logic:
  - 高分＝回檔是佈局點而非崩盤。

Data_Source:
  - Price + Volume

---

[#INDICATOR]

Code: M18

Name: 反轉潛力（Reversal_Potential）

Category: Meta

Definition: 以 K 棒、籌碼與情緒綜合判斷底部 / 頂部反轉機率。

Logic:
  - 高分＝容易出現 V 型或 W 型反轉。

Data_Source:
  - P + C + S 系列

---

[#INDICATOR]

Code: M19

Name: 法人共識強度（Institutional_Consensus）

Category: Meta

Definition: 外資 + 投信 + 券商報告方向的一致性。

Logic:
  - 高分＝方向較明確。

Data_Source:
  - C 系列 + Research Reports

---

[#INDICATOR]

Code: M20

Name: 新聞風險分數（News_Risk_Score）

Category: Meta

Definition: 以 NLP 分析新聞中負面關鍵字比例。

Logic:
  - 負面比例高＝事件風險提高。

Data_Source:
  - News / NLP

---

[#INDICATOR]

Code: M21

Name: 交易擁擠度（Crowded_Trade）

Category: Meta

Definition: 當市場與法人部位極度集中於少數熱門股。

Logic:
  - 擁擠度高＝一旦反轉殺傷巨大。

Data_Source:
  - ETF/Top 10 Holdings

---

[#INDICATOR]

Code: M22

Name: 估值安全邊際（Margin_of_Safety）

Category: Meta

Definition: 以估值與產業週期評估安全邊際。

Logic:
  - 高分＝長線布局空間大。

Data_Source:
  - Valuation + Macro

---

[#INDICATOR]

Code: M23

Name: 週期位置判斷（Cycle_Position）

Category: Meta

Definition: 判斷該產業處於景氣循環的哪個階段。

Logic:
  - 初升/成長後段/衰退，對估值與風險有不同含義。

Data_Source:
  - Macro + Industry Data

---

[#INDICATOR]

Code: M24

Name: 股利穩定度（Dividend_Stability）

Category: Meta

Definition: 配息紀錄是否穩定且有成長。

Logic:
  - 高分＝防禦型標的。

Data_Source:
  - Dividend History

---

[#INDICATOR]

Code: M25

Name: 股東結構健康度（Shareholder_Structure_Health）

Category: Meta

Definition: 大股東、員工持股、集中度是否合理。

Logic:
  - 太分散或太集中都可能有風險。

Data_Source:
  - Shareholding

---

[#INDICATOR]

Code: M26

Name: 財務槓桿風險（Leverage_Risk）

Category: Meta

Definition: 綜合負債比、利息保障倍數等指標。

Logic:
  - 高槓桿＋景氣反轉＝風險大。

Data_Source:
  - Balance Sheet

---

[#INDICATOR]

Code: M27

Name: 現金儲備安全度（Cash_Buffer）

Category: Meta

Definition: 現金與等價物相對營收與負債的比率。

Logic:
  - 現金充足＝抗風險能力佳。

Data_Source:
  - Balance Sheet + Cash Flow

---

[#INDICATOR]

Code: M28

Name: 估值泡沫風險（Valuation_Bubble_Risk）

Category: Meta

Definition: 當 PE/PB 遠高於歷史與同業水準。

Logic:
  - 高分＝泡沫風險大。

Data_Source:
  - Valuation

---

[#INDICATOR]

Code: M29

Name: 多空力道平衡（Bull_Bear_Balance）

Category: Meta

Definition: 綜合多空籌碼與情緒的力量對比。

Logic:
  - 偏多或偏空過度時反轉風險上升。

Data_Source:
  - C + S 系列

---

[#INDICATOR]

Code: M30

Name: 波段結構完整度（Swing_Structure_Quality）

Category: Meta

Definition: 觀察波段是否具有健康的上漲 + 回檔結構。

Logic:
  - 完整結構＝主升段特徵。

Data_Source:
  - Price

---

[#INDICATOR]

Code: M31

Name: 主力控盤成熟度（Operator_Control_Maturity）

Category: Meta

Definition: 透過分點、量價、籌碼變化評估主力的洗盤/出貨節奏。

Logic:
  - 成熟控盤＝走勢較不會亂震。

Data_Source:
  - C 系列 + Microstructure

---

[#INDICATOR]

Code: M32

Name: 風險回報比（Reward_Risk_Ratio）

Category: Meta

Definition: 預期報酬 vs 風險的比值。

Logic:
  - 高分才值得出手。

Data_Source:
  - Price + Quant

---

[#INDICATOR]

Code: M33

Name: 策略匹配度（Strategy_Fit）

Category: Meta

Definition: 該股是否適合當前採用的策略類型（當沖/波段/長線）。

Logic:
  - 不同策略對波動與流動性需求不同。

Data_Source:
  - Derived from 多個指標

---

[#INDICATOR]

Code: M34

Name: 交易成本影響（Trading_Cost_Impact）

Category: Meta

Definition: 手續費、滑價、點差對策略績效的影響。

Logic:
  - 交易成本過高＝短線策略不適用。

Data_Source:
  - Tick + Broker Fee

---

[#INDICATOR]

Code: M35

Name: 系統性風險暴露（Systematic_Risk_Exposure）

Category: Meta

Definition: 該股對整體市場與宏觀事件的敏感度。

Logic:
  - 高暴露＝遇黑天鵝時跌幅會放大。

Data_Source:
  - Beta + Macro

---

[#INDICATOR]

Code: M36

Name: 非系統性風險暴露（Idiosyncratic_Risk）

Category: Meta

Definition: 個股特有風險，例如公司治理、單一客戶依賴度。

Logic:
  - 高分＝需謹慎控管部位。

Data_Source:
  - Fundamental + News

---

==============================================================

# End of KB extension for 100-indicator framework

==============================================================

