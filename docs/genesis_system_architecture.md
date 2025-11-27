# Genesis 量化系統 - 核心架構規範 v1.0

> 本文件是 **J-GOD 股神作戰系統 / 創世紀量化系統** 的「唯一權威技術總綱」。

> 所有程式碼實作（data_feed、factor_engine、rl_engine、execution…）都必須以本文件為準。

> 若與其他 docs 檔案描述有衝突，一律以本文件為最高優先。

---

## 0. 目前系統狀態

### 0.1 已完成模組（Step 1–4）

- ✅ **Step 1**：`data_feed/tick_handler.py`  

  - `UnifiedTick` 資料類別  

  - `BaseTickConverter` 抽象基類  

  - `SinopacConverter` 骨架  

  - `MockSinopacAPI` 模擬資料來源  

  - 對應 Roadmap：**數據管道與校準**

- ✅ **Step 2**：`factor_engine/info_time_engine.py`  

  - `VolumeBar`（InfoTime Bar 結構）  

  - `InfoTimeBarGenerator`（基於成交量形成 Bar）  

  - 對應因子：**F_InfoTime（信息時間因子）**

- ✅ **Step 3**：`factor_engine/orderbook_factor.py`  

  - `OrderbookFactorEngine`  

  - 計算：Mid、Spread、LCI（Liquidity Cost Index）等  

  - 對應因子：**F_Orderbook（流動性壁壘 / 訂單簿因子）**

- ✅ **Step 4**：`factor_engine/capital_flow_factor.py`  

  - `CapitalFlowEngine`  

  - 計算：SAI（Smart Aggression Index）、MOI（Momentum of Imbalance）  

  - 對應因子：**F_C（XQ 資金流基礎：SAI & MOI）**

> 後續所有 Step（5–15），一律視這四個模組為既有依賴。

---

## 1. 知識庫來源與文件層級

### 1.1 知識來源

- 11 本 AI 知識庫版 ：

  - 交易心法、RL 架構、各種 F_* 因子構想、公式、對話

- 已存在的兩份設計文件：

  - `docs/創世紀量化系統_15步工程Roadmap_v1.md`

  - `docs/創世紀量化系統_因子依賴關係圖與工程路線圖_v1.md`

### 1.2 權限層級

1. **本檔案：`docs/genesis_system_architecture.md`**

   - 定義：

     - 各模組放哪個目錄

     - 重要資料結構長什麼樣

     - 15 步 Roadmap 的正式版摘要

   - 地位：**最高優先級**

2. **Roadmap / 依賴關係圖 兩份檔案**

   - 作為本檔的「詳細附錄」

   - 若部分描述與本檔不一致，以本檔為準

3. **11 本 AI 知識庫版**

   - 作為思想、心法、更多延伸因子設計的來源

   - 不直接當作程式實作規範

---

## 2. 分層架構與目錄規範

### 2.1 系統分層

1. **Data Layer**

   - 來源：永豐 / XQ / Polygon / 其他行情 API

   - 核心輸出：`UnifiedTick`

   - 目錄：`data_feed/`

2. **InfoTime & Bars Layer**

   - 將 Tick 聚合成 Volume Bar（InfoTime）

   - 核心輸出：`VolumeBar` + F_InfoTime

   - 目錄：`factor_engine/`（`info_time_engine.py`）

3. **Factor Engine Layer**

   - F_Orderbook, F_C, F_CrossAsset, F_Inertia, F_PT, F_MRR, O-Factors, F_Internal…

   - 目錄：`factor_engine/`

4. **RL & State Layer**

   - State Vector 組裝、Reward Engine、Trainer

   - 目錄：`rl_engine/`

5. **Execution & Risk Layer**

   - OrderRouter、TCA、風險控管與對接交易 API

   - 目錄：`execution/`

6. **Diagnostics & Evolution Layer**

   - 系統健康監控、錯誤分析與修復建議

   - 目錄：`diagnostics/`

### 2.2 UI / 戰情室 的隔離原則

- `data_feed/`、`factor_engine/`、`rl_engine/`、`execution/` = **核心計算腦（Core Brain）**

  - 只允許 Python

  - 禁止 HTML / CSS / React / Next / Tailwind 等任何 UI 元件

- 戰情室 / UI = 只負責：

  - 訂閱 core 輸出的 State Vector / RL 決策

  - 顯示與互動

  - 不得把策略邏輯寫在 UI 裡

---

## 3. 核心資料結構規範

### 3.1 `UnifiedTick`（已存在於 Step 1）

檔案：`data_feed/tick_handler.py`

```python
@dataclass
class UnifiedTick:
    timestamp: float      # ns Unix time
    symbol: str
    source: str           # 'sinopac', 'xq', 'polygon', ...
    price: float
    volume: int
    bid_price: float
    ask_price: float
```

**規範：**

- 所有 API 原始 tick 必須轉成 UnifiedTick

- `BaseTickConverter` 為共同接口，各 API Converter 必須繼承它

### 3.2 `VolumeBar`（已存在於 Step 2）

檔案：`factor_engine/info_time_engine.py`

```python
@dataclass
class VolumeBar:
    start_ts: float
    end_ts: float
    symbol: str
    total_volume: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    vwap: float           # Σ(price * volume) / Σ(volume)
    tick_count: int
    avg_bid: float
    avg_ask: float
```

**形成條件：**累積成交量 ≥ volume_threshold（預設 5M）

**作用：**

- 作為 InfoTime 的基本時間單位

- 作為多數因子的共同輸入

---

## 4. 因子概念與依賴總覽

（詳細數學與設計請參考：`docs/創世紀量化系統_因子依賴關係圖與工程路線圖_v1.md`）

### 4.1 已實作因子

**F_InfoTime**

- 來源：VolumeBar 形成速度（Bar 間距）

- 用途：衡量「信息時間密度」

**F_Orderbook**

- 來源：UnifiedTick + Orderbook（Bid1/Ask1）

- 指標：Mid、Spread、LCI（Liquidity Cost Index, bp）

**F_C（資金流基礎）**

- 來源：UnifiedTick（price/volume + Bid/Ask）

- 指標：SAI（Smart Aggression Index）、MOI（Momentum of Imbalance）

### 4.2 待實作因子（之後步驟用）

- **F_CrossAsset**：跨市場壓力 / 共振

- **F_Inertia**：使用 InfoTime Bar 上的 SAI Residual 做 EMA

- **F_PT**：龍頭 MOI vs 族群 SAI 的延遲相關

- **F_MRR**：主力大單取消率，衡量逆轉風險

- **O-Factors**：對所有 F_* 做正交化，得到 O1~O4

- **F_Internal**：從 O1~O4 的方向衝突測算內部壓力

---

## 5. 15 步工程 Roadmap（正式摘要版）

詳細說明仍在：

`docs/創世紀量化系統_15步工程Roadmap_v1.md`

這裡是「狀態標記 + 高層摘要」。

| Step | 步驟名稱 | 關鍵依賴 | 核心輸出 | 狀態 |
|------|----------|----------|----------|------|
| 1 | 數據管道與校準 | 各 API / Mock 資料 | UnifiedTick | ✅ |
| 2 | 信息時間引擎實施（F_InfoTime） | Step 1 | VolumeBar + F_InfoTime | ✅ |
| 3 | 微觀因子硬體加速（F_Orderbook） | Step 1 | F_Orderbook | ✅ |
| 4 | 資金流基礎引擎（F_C：SAI & MOI） | Step 1 | SAI, MOI | ✅ |
| 5 | 跨資產聯動因子（F_CrossAsset） | Step 1 | Cross-Asset Factors | ⬜ |
| 6 | 資金流慣性因子（F_Inertia） | Step 2 + Step 4 | F_Inertia | ⬜ |
| 7 | 壓力傳導因子（F_PT） | Step 2 + Step 4 | F_PT | ⬜ |
| 8 | 主力意圖逆轉因子（F_MRR） | Step 1（訂單事件） | F_MRR | ⬜ |
| 9 | 因子正交化引擎（O-Factor） | Step 3–8 | O1~O4 | ⬜ |
| 10 | 內部壓力因子（F_Internal） | Step 9 | F_Internal | ⬜ |
| 11 | Transformer-RL State Vector | Step 3–10 | State Vector | ⬜ |
| 12 | RL Reward & Memory Engine | Step 10 + Step 11 | Reward / Memory 模組 | ⬜ |
| 13 | 診斷與修復引擎 | Step 12 | 診斷 & 修復指令 | ⬜ |
| 14 | 執行層：OrderRouter & TCA | Step 3 + Step 8 | 實際下單邏輯 / TCA 報告 | ⬜ |
| 15 | 實盤模擬與監測 | Step 1–14 | Paper Trading / 監控系統 | ⬜ |

---

## 6. 之後對 AI 下指令的標準格式

接下來你在 Cursor 下任何實作指令，建議這樣開頭：

「請依照 `docs/genesis_system_architecture.md` 中的 Step X 與對應因子 F_YYY 的定義，

在 `<某個檔案>` 中實作 `<某個 Engine / dataclass>` …」

**例如：**

實作 F_Inertia：

> 請依照 `docs/genesis_system_architecture.md` 中 Step 6 的說明與 F_Inertia 定義，
> 
> 在 `factor_engine/inertia_factor.py` 中實作 `InertiaEngine`，輸入為 F_C 的 SAI Residual（按 InfoTime Bar 序列），輸出為每個族群的 `F_Inertia_{group}`。

---

## 7. 結語

- **11 本 AI 知識庫版** = 創世紀原始聖經（思想、心法、所有對話）

- `docs/創世紀量化系統_15步工程Roadmap_v1.md` & `docs/創世紀量化系統_因子依賴關係圖與工程路線圖_v1.md` = 戰略地圖 & 因子拓樸圖

- `docs/genesis_system_architecture.md` = **法律條文 + 工程總綱（AI、工程師都必須遵守）**

未來每當你：

- 新增一個因子、

- 改一個資料結構、

- 多一個 Step，

請先更新本檔 v1.x → v1.x+1，再請 Cursor 改程式碼。這樣 J-GOD 的大腦就不會「越寫越歪」，而是越來越像你心中的那個終極神級系統。

