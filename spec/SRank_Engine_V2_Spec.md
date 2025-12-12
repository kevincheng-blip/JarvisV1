# S-Rank Engine V2 規格書

**文件版本：** 1.0  
**最後更新：** 2025-12-13  
**目標讀者：** 後端工程師、前端工程師、架構師

---

## 1. 目標

### 1.1 為何做

S-Rank Engine V1 主要用於策略績效評估與排名，但缺乏「即時推薦」與「權重自動更新」機制。V2 的目標是：

1. **策略推薦系統**：根據預測時間軸的穩定性與趨勢，自動推薦最適合的策略組合
2. **權重自動更新**：基於 metrics（trend_slope, stability_grade, volatility）動態計算策略權重
3. **可觀測性**：提供 rationale（理由）與 metrics 透明化，讓決策者理解推薦依據

### 1.2 要解決什麼問題

- **策略選擇困難**：面對多種策略（trend_follow, mean_reversion, breakout, risk_off, momentum），決策者難以判斷當下最適合的策略
- **權重設定主觀**：現有權重多為固定或手動設定，缺乏資料驅動的動態調整
- **缺乏推薦依據**：無法解釋「為何推薦此策略」，缺乏可追溯性

### 1.3 成功指標

- ✅ 推薦 API 能在 200ms 內回應（即時計算）
- ✅ 權重總和 = 1.0（softmax normalize）
- ✅ 無資料時仍回 200（NO_DATA grade，不拋錯）
- ✅ 推薦理由（rationale）可讀且符合邏輯
- ✅ 測試覆蓋率 > 80%（contract + smoke）

---

## 2. 核心邏輯

### 2.1 Metrics 計算

沿用 `jgod/observer/prediction_stability.py` 的計算邏輯，但擴充為策略推薦專用：

**輸入：**
- `timeline_items`: `[{date, final_score}]`（從 PredictionSnapshot 或 timeline endpoint 取得）

**輸出 Metrics：**
- `n_points`: 資料點數
- `score_std`: 分數標準差
- `max_abs_delta`: 最大日間絕對變化
- `trend_slope`: 趨勢斜率（簡單線性回歸）
- `stability_grade`: `"NO_DATA" | "STABLE" | "WATCH" | "VOLATILE"`

**計算方式：**
- 純 Python 實作（不引入 numpy/pandas）
- 線性回歸：`slope = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)`
- 標準差：`std = sqrt(Σ(x - mean)² / n)`

### 2.2 策略池（固定，v2.0）

目前硬編在 `recommender.py`，未來可擴充為可配置：

```python
STRATEGY_POOL = [
    "trend_follow",      # 趨勢跟隨
    "mean_reversion",    # 均值回歸
    "breakout",          # 突破
    "risk_off",          # 風險規避
    "momentum",           # 動量
]
```

### 2.3 權重計算（Rule-based v1）

**策略評分公式：**
```
strategy_score = base_weight(strategy) 
                + a * trend_component 
                + b * stability_component 
                - c * volatility_penalty
```

**各策略的 base_weight（固定）：**
- `trend_follow`: 0.3
- `mean_reversion`: 0.2
- `breakout`: 0.2
- `risk_off`: 0.15
- `momentum`: 0.15

**Component 計算：**
- `trend_component`: 若 `trend_slope > 0`，trend_follow/momentum 加分；若 `trend_slope < 0`，mean_reversion 加分
- `stability_component`: 若 `stability_grade == "STABLE"`，所有策略加分；若 `"VOLATILE"`，risk_off 加分
- `volatility_penalty`: `score_std` 越高，所有策略扣分（但 risk_off 扣分較少）

**係數（可調整）：**
- `a = 0.2` (trend weight)
- `b = 0.3` (stability weight)
- `c = 0.15` (volatility penalty)

**Softmax Normalize：**
```python
exp_scores = [exp(s) for s in strategy_scores]
sum_exp = sum(exp_scores)
weights = [exp_s / sum_exp for exp_s in exp_scores]
```

確保 `sum(weights) == 1.0`（浮點誤差內）。

### 2.4 推薦演算法

**輸入：**
- `symbol`: 股票代碼
- `timeline_items`: 預測時間軸（最近 N 筆，預設 60）
- `k`: 推薦 Top K 策略（預設 5）

**流程：**
1. 計算 metrics（n_points, score_std, max_abs_delta, trend_slope, stability_grade）
2. 若 `n_points < 5` 或 `stability_grade == "NO_DATA"`，回傳空推薦（items=[]）
3. 對每個策略計算 `strategy_score`
4. 排序取 Top K
5. Softmax normalize 得到 weights
6. 生成 rationale（文字說明）

**Rationale 生成（rule-based）：**
- 若 `trend_slope > 0.1`：推薦 trend_follow/momentum
- 若 `trend_slope < -0.1`：推薦 mean_reversion
- 若 `stability_grade == "VOLATILE"`：推薦 risk_off
- 若 `stability_grade == "STABLE"`：推薦所有策略（但權重不同）

### 2.5 Empty-State 處理

- **無 timeline 資料**：回傳 `items=[]`, `stability_grade="NO_DATA"`, `metrics.n_points=0`
- **資料不足**（n_points < 5）：同上
- **API 層級**：一律回 200（不拋 404），前端顯示空狀態 UI

---

## 3. API / Storage 變動

### 3.1 API Endpoints

#### GET `/api/v1/s-rank-v2/recommendation/{symbol}?limit=60&k=5`

**用途：** 即時計算推薦（不存檔）

**Request:**
- Path: `symbol` (string)
- Query: `limit` (int, default=60), `k` (int, default=5)

**Response (200):**
```json
{
  "symbol": "2330",
  "start_date": "2025-11-01",
  "end_date": "2025-12-13",
  "metrics": {
    "n_points": 45,
    "score_std": 0.1234,
    "max_abs_delta": 0.25,
    "trend_slope": 0.05,
    "stability_grade": "STABLE"
  },
  "items": [
    {
      "strategy": "trend_follow",
      "weight": 0.35,
      "score": 0.85
    },
    {
      "strategy": "momentum",
      "weight": 0.28,
      "score": 0.72
    }
  ],
  "weights": {
    "trend_follow": 0.35,
    "momentum": 0.28,
    "mean_reversion": 0.15,
    "breakout": 0.12,
    "risk_off": 0.10
  },
  "rationale": {
    "trend_follow": "趨勢斜率為正，適合趨勢跟隨策略",
    "momentum": "動量指標顯示持續上升趨勢"
  }
}
```

**Empty State (200):**
```json
{
  "symbol": "NO_SYMBOL",
  "start_date": null,
  "end_date": null,
  "metrics": {
    "n_points": 0,
    "score_std": 0.0,
    "max_abs_delta": 0.0,
    "trend_slope": 0.0,
    "stability_grade": "NO_DATA"
  },
  "items": [],
  "weights": {},
  "rationale": {}
}
```

#### POST `/api/v1/s-rank-v2/recompute/{symbol}?limit=60&k=5`

**用途：** 計算並存檔 snapshot

**Request:**
- Path: `symbol` (string)
- Query: `limit` (int, default=60), `k` (int, default=5)

**Response (200):**
```json
{
  "snapshot_id": "snapshot-uuid",
  "created_at": "2025-12-13T10:00:00Z",
  "symbol": "2330",
  "start_date": "2025-11-01",
  "end_date": "2025-12-13",
  "metrics": {...},
  "items": [...],
  "weights": {...},
  "rationale": {...}
}
```

#### GET `/api/v1/s-rank-v2/latest/{symbol}`

**用途：** 讀取最新 snapshot

**Response (200):**
- 有資料：回傳 snapshot JSON（同上）
- 無資料：回傳 empty state（NO_DATA）

### 3.2 Storage Schema

**JSONL File:** `data/s_rank_v2/recommendations.jsonl`

**每筆記錄：**
```json
{
  "snapshot_id": "uuid",
  "created_at": "2025-12-13T10:00:00Z",
  "symbol": "2330",
  "start_date": "2025-11-01",
  "end_date": "2025-12-13",
  "items": [
    {"strategy": "trend_follow", "weight": 0.35, "score": 0.85}
  ],
  "weights": {
    "trend_follow": 0.35,
    "momentum": 0.28
  },
  "metrics": {
    "n_points": 45,
    "score_std": 0.1234,
    "max_abs_delta": 0.25,
    "trend_slope": 0.05,
    "stability_grade": "STABLE"
  },
  "rationale": {
    "trend_follow": "趨勢斜率為正，適合趨勢跟隨策略"
  }
}
```

**Storage API：**
- `save_snapshot(snapshot: RecommendationSnapshot) -> None`
- `load_latest(symbol: str) -> Optional[RecommendationSnapshot]`
- `list_latest(n: int = 10) -> List[RecommendationSnapshot]`

### 3.3 測試策略

**Contract Test：**
1. `test_recommendation_200_and_schema`: 驗證 200 + JSON 結構 + weights sum ≈ 1.0
2. `test_recompute_and_latest`: 驗證 recompute → latest 能讀到
3. `test_no_data_handling`: 驗證無資料時仍 200（NO_DATA）

**Smoke Test：**
- `test_s_rank_v2_recommendation_health_check`: GET `/api/v1/s-rank-v2/recommendation/2330` should be 200（允許 items empty）

**測試資料獨立性：**
- 不依賴真實資料庫
- 必要時 mock timeline 取得函式
- 或使用永遠可用的 fallback（空 timeline → NO_DATA）

---

## 4. v2 → v3 演進路徑

### 4.1 短期（v2.1）

- **可配置策略池**：從 YAML/JSON 讀取策略定義
- **更多 Metrics**：加入 volume_ratio, rsi, macd 等技術指標
- **Rationale 增強**：使用模板引擎生成更詳細的理由

### 4.2 中期（v2.5）

- **RL 整合**：使用強化學習動態調整權重係數（a, b, c）
- **Doctrine Patch 掛鉤**：當 Doctrine 更新時，自動觸發 recompute
- **A/B Test 整合**：比較不同權重計算方式的績效

### 4.3 長期（v3.0）

- **多因子模型**：整合市場情緒、宏觀指標、個股基本面
- **即時更新**：WebSocket 推送推薦更新
- **歷史回測**：驗證推薦策略的歷史績效

---

## 5. 技術約束

- **無外部依賴**：不引入 numpy/pandas（純 Python）
- **儲存格式**：JSONL（與 doctrine patch 一致）
- **API 版本**：`/api/v1/s-rank-v2`（與現有 `/api/v1/s-rank` 並存）
- **測試覆蓋**：Contract + Smoke，不依賴真實資料

---

## 6. v0.5.1-B2: Performance-Driven Recommendation

### 6.1 設計目標

v0.5.0-B1 的 rule-based 推薦（基於 score stats）升級為**績效驅動推薦**：

1. **Strategy Performance Feed**：為每個策略計算真實績效指標（sharpe, MDD, turnover, decay）
2. **Alpha Decay Management**：偵測策略績效衰退，自動降低權重
3. **風險懲罰**：MaxDD、Volatility、Turnover 過高時降低推薦權重
4. **雙模式支援**：`mode=signals`（舊版 rule-based）與 `mode=performance`（新版績效驅動）

### 6.2 Strategy Performance Feed

**模組位置：** `jgod/strategy_perf/`

**Deterministic Evaluator：**
- 輸入：symbol, prediction timeline (scores), strategy_id
- 輸出 metrics（per strategy, per symbol）：
  - `n_points`: 資料點數
  - `avg_return_proxy`: 平均報酬代理指標
  - `sharpe_proxy`: Sharpe Ratio 代理指標
  - `max_drawdown_proxy`: 最大回撤代理指標
  - `turnover_proxy`: 換手率代理指標
  - `decay_slope`: 績效衰退斜率（負值越大＝衰退越快）
  - `grade`: `"NO_DATA" | "GOOD" | "WATCH" | "BAD"`

**計算邏輯（純 Python，不依賴外部回測）：**
1. 將 score series 轉成 signal series（依策略偏好：trend_follow 看 score>0 做多，mean_reversion 看 score<0 做多）
2. 計算 return_proxy：`ret_t = position_{t-1} * (score_t - score_{t-1})`
3. 累積 equity curve，計算：
   - `avg_return_proxy = mean(ret)`
   - `sharpe_proxy = mean(ret) / (std(ret) + eps)`
   - `max_drawdown_proxy`: 從 equity curve 計算 MDD
   - `turnover_proxy`: position 變化次數 / n_points
   - `decay_slope`: 對最近 window 的 rolling sharpe_proxy 做線性回歸斜率

**Grade 判斷：**
- `NO_DATA`: n_points < 10
- `GOOD`: sharpe_proxy >= 0.8 and max_drawdown_proxy <= 0.2 and decay_slope >= -0.01
- `WATCH`: sharpe_proxy >= 0.3 and max_drawdown_proxy <= 0.35
- `BAD`: otherwise

**Storage：**
- JSONL: `data/strategy_perf/perf_snapshots.jsonl`
- 每筆 snapshot: `{snapshot_id, created_at, symbol, limit, window, items: [{strategy_id, metrics...}]}`

### 6.3 S-Rank V2 Performance Mode

**推薦公式（mode=performance）：**
```
strategy_score = w1*sharpe_proxy 
                - w2*max_drawdown_proxy 
                - w3*turnover_proxy 
                + w4*avg_return_proxy 
                - w5*decay_penalty
```

其中：
- `decay_penalty = max(0, -decay_slope) * k`（衰退越快，懲罰越大）
- 係數建議：`w1=0.4, w2=0.2, w3=0.1, w4=0.2, w5=0.1`
- 仍用 softmax normalize 得 weights（sum=1.0）

**Rationale 生成：**
- 必須提到「績效驅動」與「衰退/風險」原因（繁中，1-2 行/策略）
- 例如：「基於績效指標，sharpe_proxy=0.85，但 decay_slope=-0.05 顯示近期衰退，建議謹慎使用」

### 6.4 API 變動

**新增 Endpoints：**
- `GET /api/v1/strategy-perf/latest/{symbol}` - 讀取最新績效 snapshot
- `POST /api/v1/strategy-perf/recompute/{symbol}?limit=60&window=20` - 計算並存檔績效 snapshot

**更新 Endpoints：**
- `GET /api/v1/s-rank-v2/recommendation/{symbol}?mode=performance&limit=60&k=5` - 支援 mode 參數（預設 performance）
- `POST /api/v1/s-rank-v2/recompute/{symbol}?mode=performance&limit=60&k=5` - 支援 mode 參數

### 6.5 未來接 PathA 真績效的替換點

- `jgod/strategy_perf/evaluator.py` 的 `evaluate_strategy_performance()` 可替換為真實回測結果
- `jgod/s_rank_v2/recommender.py` 的 `recommend_from_performance()` 已抽象化，只需確保 perf_items 格式一致

---

**文件結束**

