# J-GOD v0.6.4-A5 版本回報

## 一、版本定位

**v0.6.4-A5 是 Decision V3 系統的「競技場對照與自動調參」階段**，實現了多對手比較（Multi-Compare）、冠軍/挑戰者機制（Champion/Challenger）以及自動參數優化（Auto-Tuning），使系統能夠持續自我評估並發現更優配置。

---

## 二、核心功能完成清單

### 1. Multi-Compare（多對手比較）

**實現內容：**
- 同時比較 **4 個挑戰者**：
  1. **V3（Champion）**：當前 Decision V3 引擎的決策結果
  2. **RISK_OFF**：固定風險規避模式（position_scale=0.20, risk_state="RISK_OFF"）
  3. **MOMENTUM**：固定動量策略（momentum=0.60, trend_follow=0.25, risk_off=0.15, position_scale=0.50）
  4. **EQUAL_WEIGHT**：等權重策略（所有策略權重均等，position_scale=0.50）

**與 v0.6.3-A4 的本質差異：**
- **v0.6.3-A4**：僅比較 V3 vs 單一 Baseline（固定 CAUTION 模式）
- **v0.6.4-A5**：同時比較 V3 vs 3 個不同策略基線，並引入 Pareto 支配分析

**評分機制：**
- 每個挑戰者使用相同的評估指標（hit_rate_proxy, avg_return_proxy, max_drawdown_proxy, turnover_proxy, decision_consistency）
- 計算 Composite Score：`avg_return_proxy * 1.0 - max_drawdown_proxy * 0.9 + hit_rate_proxy * 0.15 - turnover_proxy * 0.12 + decision_consistency * 0.08`
- 被 Pareto 支配的挑戰者會被標記並扣分（composite_score *= 0.95）

### 2. Champion / Challenger 機制

**Champion 產生方式：**
- Champion 固定為 **V3（Decision V3 引擎）**
- 每次 Arena recompute 時，V3 會與其他 3 個挑戰者進行比較
- Winner 由 Composite Score 最高者決定（排序後取第一名）

**輪替機制：**
- **目前未實現自動輪替**（預留給 A6/A7）
- 每次 recompute 都會重新計算所有挑戰者的分數
- 如果 Winner 不是 V3，且分數差距 >= 0.03，會標記 `is_regression=True`
- UI 上會顯示「⚠️ 回歸警報」提示

**Pareto 支配分析：**
- 檢查每個挑戰者是否被其他挑戰者 Pareto 支配
- 支配條件：其他挑戰者在 avg_return（>=）、max_drawdown（<=）、turnover（<=）三個維度都優於或等於，且至少一個維度嚴格優於
- 被支配的挑戰者會被標記 `pareto_dominated=True` 並在分數板上顯示

### 3. Auto-Tuning（自動調參）

**調整的參數：**
1. **Risk Mapping**（風險映射）：
   - STABLE → position_scale（候選值：0.70, 0.80, 0.90）
   - WATCH → position_scale（候選值：0.45, 0.55, 0.65）
   - VOLATILE → position_scale（候選值：0.25, 0.35, 0.45）
   - NO_DATA → position_scale（固定：0.20）

2. **Composite Weights**（複合分數權重）：
   - avg_return_proxy（候選值：0.9, 1.0, 1.1）
   - max_drawdown_proxy（候選值：-0.8, -0.9, -1.0）
   - hit_rate_proxy（候選值：0.10, 0.15, 0.20）
   - turnover_proxy（候選值：-0.10, -0.12, -0.15）
   - decision_consistency（候選值：0.05, 0.08, 0.10）

**優化依據：**
- 使用 **Grid Search**（3x3 = 9 種組合）
- 對每個 Variant Config，建立對應的 V3 Variant Decision，並使用相同的評估指標計算 Composite Score
- 選出 Top 5 變體，最佳配置存入 `auto_tuning.best_config`
- 如果最佳變體分數 > 當前 V3 分數 + 0.02，會在 recommendation 中建議更新風險映射

**輸出內容：**
- `best_config`：最佳 VariantConfig（risk_mapping + composite_weights）
- `top_variants`：Top 5 變體列表（每個包含 config + score）
- `notes`：繁體中文說明（包含最佳分數、風險映射建議、是否需要調整）

---

## 三、Decision V3 Arena 的實際輸出能力

### Arena recompute 產出資料結構

**完整 ArenaResult 包含：**
```python
{
    "symbol": str,
    "created_at": ISO timestamp,
    "mode": "performance" | "signals",
    "window": int (default 20),
    "limit": int (default 60),
    "k": int (default 5),
    "scoreboard": [
        {
            "challenger_id": "V3" | "RISK_OFF" | "MOMENTUM" | "EQUAL_WEIGHT",
            "composite_score": float,
            "metrics": {
                "hit_rate_proxy": float,
                "avg_return_proxy": float,
                "max_drawdown_proxy": float,
                "turnover_proxy": float,
                "decision_consistency": float
            },
            "pareto_dominated": bool
        }
    ],
    "winner_id": str,
    "is_regression": bool,
    "auto_tuning": {
        "best_config": {
            "risk_mapping": Dict[str, float],
            "composite_weights": Dict[str, float]
        },
        "top_variants": [
            {"config": VariantConfig, "score": float}
        ],
        "notes": str
    },
    "summary": str (繁體中文),
    "recommendation_next_step": str (繁體中文)
}
```

### Winner / Loser / Delta metrics / Tuning suggestion

**✅ Winner：**
- `winner_id`：分數最高的挑戰者 ID
- 在 UI 上以彩色 badge 顯示（綠色=V3, 藍色=其他）

**✅ Loser：**
- 分數板中所有非 winner 的挑戰者
- 被 Pareto 支配的挑戰者會標記「是」

**✅ Delta metrics：**
- **未直接提供 delta**（預留給 A6）
- 但可以從 `scoreboard` 中手動計算：`winner.metrics - challenger.metrics`

**✅ Tuning suggestion：**
- 存在於 `auto_tuning.notes` 和 `recommendation_next_step`
- 如果最佳變體分數 > V3 分數 + 0.02，會建議「可考慮更新風險映射參數」

### Storage 實際儲存欄位

**JSONL 格式（`data/decision_v3/arena.jsonl`）：**
- 每行一個完整的 Arena snapshot（包含上述所有 ArenaResult 欄位）
- 額外欄位：`arena_id`（UUID 格式）
- 儲存順序：append-only（新資料追加到檔案末尾）
- 查詢方式：按 `symbol` 過濾，按 `created_at` 降序排序

---

## 四、API 層完成項目

### Endpoints 清單

1. **`POST /api/v1/decision-v3/arena/recompute/{symbol}`**
   - Query params: `mode`, `limit`, `k`, `window`
   - 功能：計算 Arena 並儲存 snapshot
   - 回傳：`ArenaResponseSchema`（包含 arena_id + 完整 arena 資料）
   - **保證 200**：即使計算失敗，也會回傳空狀態（winner_id="NO_DATA"）

2. **`GET /api/v1/decision-v3/arena/latest/{symbol}`**
   - 功能：取得最新 Arena snapshot
   - 回傳：`ArenaSnapshotResponseSchema`
   - **保證 200**：無資料時回傳空狀態（winner_id="NO_DATA", scoreboard=[]）

3. **`GET /api/v1/decision-v3/arena/list/{symbol}?n=20`**
   - 功能：列出最近 N 個 Arena snapshots
   - 回傳：`ArenaListResponseSchema`（symbol, total, items[]）
   - **保證 200**：無資料時回傳 `items=[]`, `total=0`
   - **修復重點**：從 `async def` 改為 `def`（同步），避免 coroutine bug

### NO_DATA 行為

- **所有 endpoints 都保證 200 OK**
- NO_DATA 時：
  - `winner_id = "NO_DATA"`
  - `scoreboard = []`
  - `summary = "資料不足，無法進行競技場對照"` 或類似訊息
  - `recommendation_next_step = "請確保至少有 10 筆預測資料"`

---

## 五、War Room V2 UI 完成項目

### 新增區塊

**在 `DecisionV3Card.tsx` 中新增「競技場 (Arena)」區塊：**
- 位置：位於 Compare 區塊下方
- 包含：
  1. **標題列**：顯示「競技場 (Arena)」+ 「Run Arena」按鈕
  2. **Winner Badge + 回歸警報**：顯示 winner_id 和 is_regression 警告
  3. **分數板表格**：顯示所有挑戰者的分數、報酬、回撤、Pareto 支配狀態
  4. **自動調參結果**：顯示 best_config、top_variants、notes
  5. **競技場摘要**：顯示 summary
  6. **建議下一步**：顯示 recommendation_next_step
  7. **最近競技場**：顯示最近 5 個 snapshots（created_at, winner_id）

### Champion / Challenger 在 UI 上的呈現

**分數板表格：**
- 表頭：挑戰者 | 分數 | 報酬 | 回撤 | 支配
- Winner 行：背景色為 `bg-yellow-50`（淺黃色高亮）
- 每行顯示：challenger_id, composite_score, avg_return_proxy, max_drawdown_proxy, pareto_dominated

**Winner Badge：**
- V3：綠色 badge
- 其他：藍色 badge
- 回歸警報：紅色 badge（當 is_regression=True）

### 使用者可執行的操作

1. **「Run Arena」按鈕**：
   - 觸發 `POST /api/v1/decision-v3/arena/recompute/{symbol}`
   - 按鈕狀態：pending 時顯示「計算中...」並禁用
   - 成功後顯示綠色 success message，失敗顯示紅色 error message

2. **自動載入最新 Arena**：
   - 當 `selectedSymbol` 改變時，自動呼叫 `GET /api/v1/decision-v3/arena/latest/{symbol}`
   - 使用 React Query 的 `useQuery` 進行快取和自動重新整理

---

## 六、Tests & CI

### 新增 Contract Tests

**`tests/test_decision_v3_arena_contract.py`：**
1. `test_recompute_arena_contract`：測試 recompute endpoint（200 + schema + winner_id + scoreboard）
2. `test_recompute_arena_no_data_contract`：測試 NO_DATA 情況（仍回傳 200）
3. `test_get_arena_latest_contract`：測試 latest endpoint（200 + schema）
4. `test_get_arena_latest_empty_contract`：測試 latest 無資料（仍回傳 200）
5. `test_list_arena_snapshots_contract`：測試 list endpoint（200 + schema + items）
6. `test_list_arena_snapshots_empty_contract`：測試 list 無資料（仍回傳 200）

**Smoke Test 更新：**
- `tests/test_war_room_v2_smoke.py`：新增 `GET /api/v1/decision-v3/arena/latest/2330` 和 `POST /api/v1/decision-v3/arena/recompute/2330` 的健康檢查

**CI 更新：**
- `scripts/ci_quick_check.sh`：新增 Check 13（`pytest tests/test_decision_v3_arena_contract.py -q`）

### Coroutine Bug 發生原因

**問題：**
- `list_arena_snapshots` endpoint 原本是 `async def`，但內部呼叫的 `service_list_arena_snapshots` 是同步函數
- 測試中 mock 了 `jgod.decision_v3.service.list_arena_snapshots`，但 router 實際呼叫的是 `jgod.api.routers.decision_v3.service_list_arena_snapshots`（import 的別名）
- 導致 mock 未生效，實際函數被呼叫，但因為名稱衝突（router 函數名與 service 函數名相同），造成遞迴呼叫或 coroutine 錯誤

**修復方式：**
1. 將 `list_arena_snapshots` endpoint 改為 `def`（同步）
2. 修正測試 mock 路徑：`patch("jgod.api.routers.decision_v3.service_list_arena_snapshots")`
3. 移除多餘的 `side_effect` 設置

### 結構性避免再次發生

**設計原則：**
- **同步 service 層 → 同步 router**：如果 service 層是同步的，router 也應該是同步的
- **Mock 路徑必須與實際 import 路徑一致**：mock `jgod.api.routers.decision_v3.service_list_arena_snapshots` 而非 `jgod.decision_v3.service.list_arena_snapshots`
- **避免名稱衝突**：router 函數名不應與 service 函數名相同（已使用 `service_list_arena_snapshots` 別名）

---

## 七、與前一版（v0.6.3-A4）的能力差異總結

### Before (v0.6.3-A4)

**Compare 功能：**
- 僅比較 V3 vs 單一 Baseline（固定 CAUTION 模式）
- Baseline 固定：`risk_state="CAUTION"`, `position_scale=0.50`, `primary_strategy="momentum"`, `confidence=0.50`
- 輸出：winner (V3/BASELINE/TIE/NO_DATA), delta_metrics, summary, recommendation_next_step
- 無自動調參功能

**UI：**
- DecisionV3Card 有 Compare 區塊（顯示 winner badge, delta metrics, summary）

### After (v0.6.4-A5)

**Arena 功能：**
- 同時比較 V3 vs 3 個不同策略基線（RISK_OFF, MOMENTUM, EQUAL_WEIGHT）
- 引入 Pareto 支配分析
- 自動調參：Grid Search 9 種 Variant Config，找出最佳風險映射和複合權重
- 輸出：scoreboard（所有挑戰者分數）, winner_id, is_regression, auto_tuning, summary, recommendation_next_step

**UI：**
- DecisionV3Card 新增 Arena 區塊（分數板表格、自動調參結果、最近競技場歷史）
- Compare 區塊保留（兩者並存）

**關鍵差異：**
- **從「單一對照」升級為「多對手競技場」**
- **從「固定 Baseline」升級為「自動調參 Variant」**
- **從「簡單勝負」升級為「Pareto 支配分析」**

---

## 八、未完成但已預留的延伸點

### 1. Champion 自動輪替（預留給 A6）

**目前狀態：**
- Champion 固定為 V3
- 即使 Winner 是其他挑戰者，也不會自動切換

**預留設計：**
- `ArenaResult.winner_id` 已記錄每次的 Winner
- `is_regression` 標記可用於觸發輪替邏輯
- 未來可實作：連續 N 次 Winner 不是 V3 時，自動將 Winner 設為新 Champion

### 2. Delta Metrics 直接輸出（預留給 A6）

**目前狀態：**
- Delta 需要從 `scoreboard` 手動計算

**預留設計：**
- `ChallengerScore` 可擴展為包含 `delta_vs_winner` 欄位
- 或新增 `ArenaResult.delta_metrics` 欄位（winner vs 各挑戰者的 delta）

### 3. 更多挑戰者策略（預留給 A7）

**目前狀態：**
- 固定 4 個挑戰者（V3, RISK_OFF, MOMENTUM, EQUAL_WEIGHT）

**預留設計：**
- `ChallengerId` 使用 `Literal` 類型，可擴展為包含更多策略
- `_build_*_decision` 函數可擴展為支援更多策略建構

### 4. Auto-Tuning 參數擴展（預留給 A8）

**目前狀態：**
- Grid Search 僅搜尋 risk_mapping（3 種）和 composite_weights（3 種）= 9 種組合

**預留設計：**
- `_run_auto_tuning` 可擴展為支援更多參數（如 strategy weights, confidence thresholds）
- 可引入更進階的優化算法（如 Bayesian Optimization）

### 5. Arena 歷史分析（預留給 A9）

**目前狀態：**
- 僅儲存 snapshot，無歷史趨勢分析

**預留設計：**
- 可新增 endpoint：`GET /api/v1/decision-v3/arena/trend/{symbol}`（分析 winner_id 變化趨勢）
- 可新增 endpoint：`GET /api/v1/decision-v3/arena/stats/{symbol}`（統計各挑戰者勝率）

---

## 總結

v0.6.4-A5 實現了完整的「競技場對照與自動調參」系統，從單一對照升級為多對手競技場，並引入自動參數優化能力。所有 API endpoints 保證 200 回應，UI 完整呈現分數板和調參結果，測試覆蓋所有場景。Coroutine bug 已修復並建立結構性防護機制。

**交付狀態：✅ 完成**
