# A7/A8 Walk-Forward Master Plan

**文件版本：** 1.0  
**建立日期：** 2025-12-14  
**目標讀者：** Engineering Lead, Backend Engineers, Research Team  
**當前版本：** v0.6.5-A6 (Execution Grounding)

---

## I. 總體戰略與 A7 優先性

### 1.1 系統升級目標

系統從 v0.6.5-A6「具備執行基礎」升級為「具備真實 P&L 驅動的持續進化能力」。

**核心問題：**
- v0.6.5-A6 的 Virtual Ledger 使用價格代理（price proxy），從 `final_score` 推導價格
- Reward Signal 失真：AI 可能學會在模擬器中「作弊」（利用 proxy 的簡化假設）
- 缺乏真實撮合摩擦（slippage、流動性限制）導致評估過於樂觀

**A7 必須先做：**
1. **修正 Reward Signal（Grounding）**：使用真實 OHLCV 資料 + Fill Engine（撮合摩擦）
2. **Backtest Core**：提供可重現的回測引擎，作為 A8 Walk-Forward 的唯一真實研究基礎
3. **淘汰 Proxy P&L**：`evaluation.py` 和 `arena.py` 必須使用 BacktestCore 的輸出

**並行設計原則：**
- **正確性（A7-M1）優先於效率**：先確保 P&L 計算正確，再優化計算效率
- **Feature DB（A7.5/M2）設計必須提前完成**：避免 M1 實作時埋下「每次重算 365 天」的技術債

---

## II. AI 大腦四層分工與模組邊界

### 2.1 四層架構定義

| 層級 | 英文代號 | 責任 | Input | Output | Storage | 落地階段 |
|------|---------|------|-------|--------|---------|----------|
| **Data** | D | 市場資料時序（OHLCV）+ 特徵計算（50+10因子） | 原始市場資料 | OHLCV + FeatureVector | `data/features.jsonl` | A7.5-M2 |
| **Method** | M | 特徵優化/篩選（10/20日週期） | FeatureVector + Performance | FeatureSubset | `data/feature_subsets.jsonl` | A8-M3 |
| **Thought** | T | 調參/風控 mapping/權重修復 → 產出 DoctrinePatch 建議（5日週期） | DecisionV3 + Arena + Eval | DoctrinePatch（建議） | `data/doctrine_patches.jsonl` | A8-M3 |
| **Strategy** | S | Regime/策略切換（季/60日週期） | Regime Signal + Performance | StrategyAllocation | `data/strategy_allocations.jsonl` | A8-M3 |

### 2.2 模組邊界說明

**Data Layer (D)：**
- **Who**: `jgod/data/market_data_service.py` (MDTS) + `jgod/data/feature_service.py` (Feature DB)
- **責任**: 提供 OHLCV 時序、計算 50+10 因子、增量更新 Feature DB
- **更新頻率**: 每日（增量）
- **版本管理**: `(symbol, date, version)` 作為唯一 key

**Method Layer (M)：**
- **Who**: `jgod/research/feature_selector.py`
- **責任**: 分析因子表現，產出 FeatureSubset 建議（每 10/20 日）
- **Input**: FeatureVector + BacktestReport（歸因分析）
- **Output**: FeatureSubset（建議移除/保留的因子列表）

**Thought Layer (T)：**
- **Who**: `jgod/research/tuning_advisor.py`（整合現有 Arena + Auto-Tuning）
- **責任**: 分析 Decision V3 表現，產出 DoctrinePatch 建議（每 5 日）
- **Input**: DecisionV3 + Arena + Eval + Compare 結果
- **Output**: DoctrinePatch JSON（需人工 approve）

**Strategy Layer (S)：**
- **Who**: `jgod/research/strategy_allocator.py`
- **責任**: 分析 Regime 變化，產出 StrategyAllocation 建議（每季/60 日）
- **Input**: Regime Signal + 多策略表現
- **Output**: StrategyAllocation（建議切換的策略配置）

---

## III. 2024 Walk-Forward Runner（A8）流程設計

### 3.1 Daily Prediction Cycle（每日）

**流程：**
```
1. Data cache check（缺就增量計算）
   - MDTS.fetch_ohlcv(symbol, date)
   - FeatureService.get_or_compute(symbol, date, version)
   
2. S/T/M input 注入
   - StrategyAllocation（當前策略配置）
   - FeatureSubset（當前因子子集）
   - DoctrinePatch（當前決策參數）
   
3. Decision → Order → Fill → Ledger Update
   - DecisionEngineV3.decide(symbol, date, ...)
   - OrderGenerationEngine.generate_orders(...)
   - FillEngine.execute(order, ohlcv_snapshot)
   - VirtualLedger.apply_fill(fill)
   
4. Log：DailyLedgerSnapshot（append-only）
   - 寫入 data/walkforward/daily_snapshots.jsonl
   - 包含：symbol, date, nav, position, realized_pnl, decision, order, fill
```

**實作位置：**
- `jgod/research/walkforward_runner.py`：`run_daily_cycle(symbol, date)`

### 3.2 多週期 Learning & Review Cycle

**每 5 日：Thought Layer（Arena + Auto-Tuning）**
- 觸發：`run_thought_review(symbol, window=5)`
- 流程：
  1. 取得最近 5 日的 DailyLedgerSnapshot
  2. 執行 Decision V3 Arena（使用 BacktestCore）
  3. 分析 Auto-Tuning 結果
  4. 產出 DoctrinePatch 建議（JSON）
  5. 寫入 `data/walkforward/thought_reviews.jsonl`
- **重要**：所有建議必須人工 approve（使用既有 `doctrine_patch` pipeline）

**每 10/20 日：Method Layer（歸因/因子檢視）**
- 觸發：`run_method_review(symbol, window=10)` 或 `window=20`
- 流程：
  1. 取得最近 N 日的 BacktestReport
  2. 執行因子歸因分析（correlation + contribution）
  3. 產出 FeatureSubset 建議（建議移除/保留的因子）
  4. 寫入 `data/walkforward/method_reviews.jsonl`
- **重要**：FeatureSubset 建議需人工 approve（未來可自動化）

**每季/60 日：Strategy Layer（Regime）**
- 觸發：`run_strategy_review(symbol, window=60)`
- 流程：
  1. 分析 Regime 變化（volatility, trend, correlation）
  2. 比較多策略表現（momentum, mean_reversion, breakout, risk_off）
  3. 產出 StrategyAllocation 建議
  4. 寫入 `data/walkforward/strategy_reviews.jsonl`
- **重要**：StrategyAllocation 建議需人工 approve（未來可自動化）

### 3.3 版本控制與追溯性

**所有產出都必須：**
- 落 JSONL（append-only）
- 具備版本欄位：`config_version`（對應 Feature DB version）
- 具備唯一 key：`(symbol, date, window, config_version)`
- 支援回滾：保留歷史版本，能切回穩定版本

**Storage Schema：**
```python
# data/walkforward/daily_snapshots.jsonl
{
  "snapshot_id": "uuid",
  "symbol": "2330",
  "date": "2024-01-15",
  "config_version": "v1.0",
  "nav": 1000000.0,
  "position": {"qty": 100, "avg_cost": 100.0},
  "realized_pnl": 0.0,
  "unrealized_pnl": 1000.0,
  "decision": {...},
  "order": {...},
  "fill": {...}
}

# data/walkforward/thought_reviews.jsonl
{
  "review_id": "uuid",
  "symbol": "2330",
  "date": "2024-01-15",
  "window": 5,
  "config_version": "v1.0",
  "arena_result": {...},
  "doctrine_patch_suggestion": {...},  # JSON
  "status": "PENDING_APPROVAL"  # PENDING_APPROVAL / APPROVED / REJECTED
}
```

---

## IV. Feature DB/Cache（A7.5/M2）設計

### 4.1 Schema 定義

**FeatureSchema：**
```python
{
  "symbol": "2330",
  "date": "2024-01-15",
  "version": "v1.0",  # 版本號（因子計算邏輯版本）
  "ohlcv_snapshot": {
    "open": 100.0,
    "high": 105.0,
    "low": 99.0,
    "close": 104.0,
    "volume": 1000000
  },
  "features": {
    "trend_ma5": 102.0,
    "trend_ma20": 100.0,
    "momentum_rsi": 65.0,
    # ... 50+10 因子欄位
  },
  "computed_at": "2024-01-15T10:00:00Z"
}
```

### 4.2 存儲設計

**路徑：** `data/features.jsonl`（append-only）

**唯一 key：** `(symbol, date, version)`

**增量更新邏輯：**
```python
def get_or_compute_features(symbol, date, version):
    # 1. 先查存在就 skip
    existing = load_feature(symbol, date, version)
    if existing:
        return existing
    
    # 2. 只算新增日期
    ohlcv = mdts.fetch_ohlcv(symbol, date)
    features = compute_features(ohlcv, version)
    save_feature(symbol, date, version, features)
    return features
```

**版本管理：**
- `version` 變更需重算（但要有工具支援 partial rebuild）
- 工具：`jgod/data/feature_service.py` 提供 `rebuild_features(symbol, start_date, end_date, new_version)`
- **明確寫出「絕不每次重算 365 天」**：只重算 `version` 變更的日期範圍

### 4.3 實作位置

- `jgod/data/feature_service.py`：Feature DB 服務層
- `jgod/data/feature_storage.py`：JSONL 持久化
- `jgod/data/feature_computer.py`：因子計算邏輯（50+10 因子）

---

## V. Backtest Core（A7/M1）設計

### 5.1 BacktestEngine 設計

**核心功能：**
- `BacktestEngine.run(symbol, start_date, end_date, config)`
- 切片（MDTS + FeatureDB）取得 OHLCV 和 FeatureVector
- 逐日 loop：Decision → Order → Fill → Ledger Update
- 產生 BacktestReport（final_nav / metrics / daily_log）

**實作位置：**
- `jgod/research/backtest_engine.py`：`BacktestEngine` 類別

**流程：**
```python
def run(self, symbol, start_date, end_date, config):
    ledger = VirtualLedger(initial_cash=config.initial_cash)
    daily_logs = []
    
    for date in date_range(start_date, end_date):
        # 1. 取得 OHLCV 和 FeatureVector
        ohlcv = mdts.fetch_ohlcv(symbol, date)
        features = feature_service.get_or_compute(symbol, date, config.feature_version)
        
        # 2. 計算 Decision
        decision = decision_engine.decide(symbol, date, features, config)
        
        # 3. 生成 Order
        order = order_engine.generate_orders(decision, ledger, ohlcv.close)
        
        # 4. 執行 Fill（撮合）
        fill = fill_engine.execute(order, ohlcv)
        
        # 5. 更新 Ledger
        ledger.apply_fill(fill)
        ledger.mark_to_market(symbol, ohlcv.close)
        
        # 6. 記錄 Daily Log
        daily_logs.append({
            "date": date,
            "nav": ledger.nav,
            "position": ledger.positions.get(symbol),
            "realized_pnl": ledger.realized_pnl,
            "decision": decision,
            "order": order,
            "fill": fill
        })
    
    # 7. 產生 BacktestReport
    return BacktestReport(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        final_nav=ledger.nav,
        metrics=compute_metrics(daily_logs),
        daily_log=daily_logs
    )
```

### 5.2 BacktestReport 結構

```python
{
  "symbol": "2330",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "final_nav": 1050000.0,
  "initial_cash": 1000000.0,
  "total_return": 0.05,
  "metrics": {
    "avg_daily_return": 0.001,
    "max_drawdown": 0.02,
    "sharpe_ratio": 1.5,
    "hit_rate": 0.55,
    "turnover": 0.3
  },
  "daily_log": [
    {
      "date": "2024-01-01",
      "nav": 1000000.0,
      "position": {"qty": 0, "avg_cost": 0.0},
      "realized_pnl": 0.0,
      "decision": {...},
      "order": {...},
      "fill": {...}
    },
    # ...
  ]
}
```

### 5.3 與現有 Evaluation/Arena 整合

**修改 `jgod/decision_v3/evaluation.py`：**
- 新增 `evaluate_decision_v3_with_backtest()` 方法
- 使用 `BacktestEngine.run()` 取代現有的 proxy P&L 邏輯
- 保留 `use_ledger=True` 參數，但內部改用 BacktestCore

**修改 `jgod/decision_v3/arena.py`：**
- `compute_arena()` 內部呼叫 `evaluate_decision_v3_with_backtest()` 取代 proxy

**重要：**
- 保持 deterministic（測試可重現）
- 不引入 numpy（純 Python）

---

## VI. Doctrine 自我修復與 Patch 機制（A8/M3）

### 6.1 Thought Layer 產出 DoctrinePatch 建議

**流程：**
1. `tuning_advisor.analyze(symbol, window=5)` 分析最近 5 日表現
2. 執行 Arena + Auto-Tuning，找出最佳配置
3. 比較當前 Doctrine 配置與最佳配置
4. 產出 DoctrinePatch 建議（JSON）

**DoctrinePatch 建議格式：**
```json
{
  "patch_id": "uuid",
  "symbol": "2330",
  "created_at": "2024-01-15T10:00:00Z",
  "window": 5,
  "config_version": "v1.0",
  "changes": [
    {
      "type": "risk_mapping",
      "path": "decision_v3.risk_mapping.STABLE",
      "old_value": 0.70,
      "new_value": 0.80,
      "reason": "Arena 顯示 STABLE 狀態下提高 position_scale 可提升 sharpe"
    },
    {
      "type": "composite_weights",
      "path": "decision_v3.composite_weights.avg_return_proxy",
      "old_value": 1.0,
      "new_value": 1.1,
      "reason": "Auto-tuning 發現提高 avg_return 權重可提升 composite score"
    }
  ],
  "status": "PENDING_APPROVAL"
}
```

### 6.2 人工 Approve 機制

**使用既有 `doctrine_patch` pipeline：**
- 建議寫入 `data/walkforward/thought_reviews.jsonl`
- 人工審核後，透過 `POST /api/v1/doctrine/patches/{patchId}/approve` 批准
- 批准後自動 apply 到系統配置

**或新增 config endpoint：**
- `POST /api/v1/config/apply-patch`：直接 apply DoctrinePatch（需人工觸發）

### 6.3 版本控制與回滾

**版本管理：**
- 所有 DoctrinePatch 建議保留歷史版本
- 支援回滾：`POST /api/v1/config/revert-patch/{patchId}`
- 回滾後系統切回穩定版本

**重要：**
- 任何 auto-tuning/auto-patch 必須可 revert
- 保留完整變更歷史（JSONL append-only）

---

## VII. Milestone 拆解與白名單（A7 & A8）

### 7.1 M1 (v0.6.6-A7): Realism Foundation

**目標：** 修正 Reward Signal（Grounding：OHLCV + Fill 摩擦），淘汰 proxy P&L

**新增檔案：**
- `jgod/data/market_data_service.py`：提供 OHLCV 時序（先用現有 DB/PredictionSnapshot 或 deterministic mock）
- `jgod/execution/fill_engine.py`：撮合（slippage + fee）產生 OrderFill
- `jgod/research/backtest_engine.py`：start/end 區間逐日 loop：Decision → Order → Fill → Ledger
- `jgod/research/__init__.py`：初始化 research 模組

**修改檔案：**
- `jgod/decision_v3/evaluation.py`：新增 `evaluate_decision_v3_with_backtest()`，使用 BacktestCore 取代 proxy
- `jgod/decision_v3/arena.py`：使用 `evaluate_decision_v3_with_backtest()` 取代 proxy
- `jgod/execution/virtual_ledger.py`：新增 `apply_fill(fill)` 方法（如果尚未有）

**新增測試：**
- `tests/test_mdts_contract.py`：MDTS 合約測試
- `tests/test_fill_engine_contract.py`：Fill Engine 合約測試
- `tests/test_backtest_core_contract.py`：Backtest Core 合約測試

**CI 更新：**
- `scripts/ci_quick_check.sh`：
  - Check 16：`pytest tests/test_mdts_contract.py -q`
  - Check 17：`pytest tests/test_fill_engine_contract.py -q`
  - Check 18：`pytest tests/test_backtest_core_contract.py -q`

**文件：**
- `docs/release_notes_v0.6.6-a7.md`：版本說明

**Manual 驗證指令：**
```bash
# 1. 測試 MDTS
curl http://127.0.0.1:8000/api/v1/data/ohlcv/2330?start_date=2024-01-01&end_date=2024-01-31

# 2. 測試 Fill Engine（透過 Backtest API）
curl -X POST "http://127.0.0.1:8000/api/v1/research/backtest/run?symbol=2330&start_date=2024-01-01&end_date=2024-01-31"

# 3. 驗證 Evaluation 使用 BacktestCore
curl -X POST "http://127.0.0.1:8000/api/v1/decision-v3/eval/recompute/2330?mode=performance&limit=60&k=5&window=20"
```

**風險點：**
- MDTS 資料來源：若現有 DB 無 OHLCV，需使用 deterministic mock（可能與真實資料有差異）
- Fill Engine slippage 參數：需合理設定（目前固定值，未來可配置化）

**回滾策略：**
- 保留 `evaluate_decision_v3()` 的 `use_ledger=False` 路徑（proxy 模式）作為 fallback
- 新增 feature flag：`USE_BACKTEST_CORE=true`（預設 true，可切回 false）

---

### 7.2 M2 (v0.6.7-A7.5): Feature DB/Cache & Data Pipeline

**目標：** 建立 Feature DB/Cache，避免每次重算 365 天因子

**新增檔案：**
- `jgod/data/feature_service.py`：Feature DB 服務層（get_or_compute, rebuild_features）
- `jgod/data/feature_storage.py`：JSONL 持久化（`data/features.jsonl`）
- `jgod/data/feature_computer.py`：因子計算邏輯（50+10 因子，純 Python）

**修改檔案：**
- `jgod/research/backtest_engine.py`：使用 `feature_service.get_or_compute()` 取代直接計算
- `jgod/api/routers/data.py`（或新建）：提供 Feature DB API

**新增測試：**
- `tests/test_feature_db_contract.py`：Feature DB 合約測試（增量更新、版本管理）

**CI 更新：**
- `scripts/ci_quick_check.sh`：
  - Check 19：`pytest tests/test_feature_db_contract.py -q`

**文件：**
- `docs/release_notes_v0.6.7-a7.5.md`：版本說明

**Manual 驗證指令：**
```bash
# 1. 測試 Feature DB 增量更新
curl -X POST "http://127.0.0.1:8000/api/v1/data/features/compute/2330?date=2024-01-15&version=v1.0"

# 2. 測試 Feature DB 查詢
curl "http://127.0.0.1:8000/api/v1/data/features/2330?date=2024-01-15&version=v1.0"

# 3. 測試版本重建（partial）
curl -X POST "http://127.0.0.1:8000/api/v1/data/features/rebuild/2330?start_date=2024-01-01&end_date=2024-01-31&new_version=v1.1"
```

**風險點：**
- 因子計算邏輯複雜度：50+10 因子可能計算耗時（需優化）
- 版本管理：`version` 變更時 partial rebuild 的正確性

**回滾策略：**
- 保留直接計算路徑（不使用 Feature DB）作為 fallback
- Feature DB 查詢失敗時自動 fallback 到直接計算

---

### 7.3 M3 (v0.6.8-A8): WalkForward Runner & Learning Layers

**目標：** 實作 Walk-Forward Runner 與多週期 Learning Layers

**新增檔案：**
- `jgod/research/walkforward_runner.py`：`run_daily_cycle()`, `run_thought_review()`, `run_method_review()`, `run_strategy_review()`
- `jgod/research/tuning_advisor.py`：Thought Layer（整合 Arena + Auto-Tuning）
- `jgod/research/feature_selector.py`：Method Layer（因子歸因/篩選）
- `jgod/research/strategy_allocator.py`：Strategy Layer（Regime 分析/策略切換）
- `jgod/research/storage.py`：Walk-Forward JSONL 持久化（`data/walkforward/*.jsonl`）

**修改檔案：**
- `jgod/api/routers/research.py`（或新建）：提供 Walk-Forward API

**新增測試：**
- `tests/test_walkforward_runner_contract.py`：Walk-Forward Runner 合約測試
- `tests/test_learning_layers_contract.py`：Learning Layers 合約測試（T/M/S）

**CI 更新：**
- `scripts/ci_quick_check.sh`：
  - Check 20：`pytest tests/test_walkforward_runner_contract.py -q`
  - Check 21：`pytest tests/test_learning_layers_contract.py -q`

**文件：**
- `docs/release_notes_v0.6.8-a8.md`：版本說明

**Manual 驗證指令：**
```bash
# 1. 測試 Daily Cycle
curl -X POST "http://127.0.0.1:8000/api/v1/research/walkforward/daily/2330?date=2024-01-15"

# 2. 測試 Thought Review（5 日）
curl -X POST "http://127.0.0.1:8000/api/v1/research/walkforward/thought-review/2330?window=5"

# 3. 測試 Method Review（10 日）
curl -X POST "http://127.0.0.1:8000/api/v1/research/walkforward/method-review/2330?window=10"

# 4. 測試 Strategy Review（60 日）
curl -X POST "http://127.0.0.1:8000/api/v1/research/walkforward/strategy-review/2330?window=60"
```

**風險點：**
- Learning Layers 產出建議的品質：需人工審核，避免錯誤建議
- Walk-Forward 執行時間：每日 cycle 可能耗時（需優化）

**回滾策略：**
- 所有建議保留 `status=PENDING_APPROVAL`，需人工 approve 才生效
- 支援回滾到歷史版本（保留完整變更歷史）

---

## 附錄：技術決策記錄

### A. 為什麼 A7-M1 必須先做？

1. **Reward Signal 失真問題**：v0.6.5-A6 的價格代理可能導致 AI 學會「作弊」
2. **Backtest Core 是唯一真實研究基礎**：A8 Walk-Forward 必須基於真實 P&L
3. **技術債最小化**：先修正正確性，再優化效率

### B. 為什麼 Feature DB（A7.5/M2）設計必須提前完成？

1. **避免「每次重算 365 天」的技術債**：M1 實作時必須考慮 Feature DB 的接口設計
2. **增量更新是必須**：Walk-Forward 每日 cycle 不能每次都重算所有因子
3. **版本管理複雜度**：`version` 變更時的 partial rebuild 需要提前設計

### C. 為什麼保持 deterministic？

1. **測試可重現**：所有測試必須 deterministic，避免 flaky tests
2. **回測可追溯**：BacktestReport 必須可重現，供歸因/檢討
3. **不引入 numpy**：保持純 Python，避免外部依賴

---

**文件狀態：** ✅ 完成  
**下一步：** 開始實作 M1 (v0.6.6-A7): Realism Foundation

