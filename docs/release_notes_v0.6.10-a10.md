# J-GOD v0.6.10-A10 版本說明

**發布日期：** 2025-12-14  
**版本類型：** Portfolio Coordination & Multi-Symbol Scaling  
**目標：** 規模化：多標的組合級運行能力

---

## 一、版本定位

v0.6.10-A10 是「規模化」版本，在 A9 單一標的安全自主進化的基礎上，建立 Portfolio Manager 系統，實現多標的組合級 Walk-Forward 運行。核心能力：**Portfolio Layer 協調、Allocation 分配、Multi-Symbol Learning、Data Interface 解耦**。

---

## 二、核心功能完成清單

### 2.1 Data 解耦：DataService Interface

**功能說明：**
- 定義抽象協議：`DataServiceInterface`
- 方法：`get_features()`, `get_ohlcv()`, `get_trading_dates()`
- 實作：`DefaultDataService`（使用 FeatureService + MDTS）
- 讓 Runner 不再直接 new FeatureService/MDTS

**實作位置：**
- `jgod/data/data_service_interface.py`：抽象接口
- `jgod/data/data_service.py`：DefaultDataService 實作

### 2.2 Portfolio Manager：多 runner 協調 + 分配

**功能說明：**
- `PortfolioManager` 類別：協調多個 WalkForwardRunner
- `allocate_capital()`：資本分配（equal_weight / vol_parity）
- `run_portfolio_walkforward()`：組合級 Walk-Forward
- 每個 symbol 建立獨立 Runner + Ledger
- 時間一致性檢查：所有 runner 使用同一決策日期 T

**Allocation 模式：**
- Equal Weight：每標的 cash = total / N
- Vol Parity：weight ∝ 1/vol，normalized（簡化版，使用最近 N 日 close 計算日報酬 std）

**實作位置：**
- `jgod/strategy/portfolio_manager.py`：PortfolioManager 類別
- `jgod/strategy/models.py`：PortfolioConfig, AllocationResult, PortfolioDailyLog

### 2.3 WalkForwardRunner：支援 external DataService + time sync

**功能說明：**
- `__init__()` 接受 `data_service` 參數
- Daily cycle 使用 `data_service.get_features()` 和 `data_service.get_ohlcv()`
- Time sync check：若 runner date != manager date → raise error
- 支援 ledger 狀態注入（portfolio 模式）

**實作位置：**
- `jgod/research/walkforward_runner.py`：修改 `__init__()`, `run_daily_cycle()`

### 2.4 Storage：Portfolio logs（append-only）

**功能說明：**
- `save_portfolio_log()`：儲存組合日誌（`data/research/portfolio_logs.jsonl`）
- `latest_portfolio_report()`：取得最新組合報告
- `list_portfolio_logs(n)`：列出最近 N 筆日誌

**實作位置：**
- `jgod/research/storage.py`：新增 portfolio log 函數

### 2.5 Multi-symbol Learning：FeatureSelector 泛化

**功能說明：**
- `select_global_features()`：跨標的因子篩選
- 聚合方式：`global_score(feature) = mean(score across symbols)`
- 輸出 `FeatureSubset`（scope="global", target_symbols=...）
- 仍保持 A9 的 guard rails（quality_score + status）

**實作位置：**
- `jgod/learning/feature_selector.py`：新增 `select_global_features()`
- `jgod/learning/models.py`：FeatureSubset 新增 `scope`, `target_symbols`

### 2.6 API：Portfolio endpoints

**功能說明：**
- `POST /api/v1/walkforward/portfolio/run`：執行組合 Walk-Forward
- `GET /api/v1/walkforward/portfolio/latest`：取得最新組合報告
- `GET /api/v1/walkforward/portfolio/list?n=20`：列出組合日誌
- 所有端點保證 200（空狀態不 404）

**實作位置：**
- `jgod/api/routers/walkforward.py`：新增 portfolio 端點
- `jgod/api/schemas/portfolio.py`：Pydantic schemas

---

## 三、Allocation 設計

### 3.1 Equal Weight

**公式：**
```
cash_per_symbol = total_cash / n_symbols
weight_per_symbol = 1.0 / n_symbols
```

**參數：**
- `initial_cash_total`：總初始現金
- `symbols`：標的清單

### 3.2 Vol Parity（簡化版）

**公式：**
```
vol[symbol] = std(daily_returns, lookback=N)
inv_vol_weight[symbol] = 1.0 / vol[symbol]
weight[symbol] = inv_vol_weight[symbol] / sum(inv_vol_weights)
cash[symbol] = total_cash * weight[symbol]
```

**參數：**
- `vol_lookback`：波動度計算回看天數（預設 20）
- `initial_cash_total`：總初始現金
- `symbols`：標的清單

---

## 四、新增檔案

### 4.1 後端核心模組

- `jgod/strategy/__init__.py`：Strategy 模組初始化
- `jgod/strategy/models.py`：PortfolioConfig, AllocationResult, PortfolioDailyLog
- `jgod/strategy/portfolio_manager.py`：PortfolioManager 核心
- `jgod/data/data_service_interface.py`：Data 抽象接口
- `jgod/data/data_service.py`：DefaultDataService 實作
- `jgod/api/schemas/portfolio.py`：Portfolio API schemas

### 4.2 測試

- `tests/test_portfolio_manager_contract.py`：Portfolio Manager 合約測試

### 4.3 文件

- `docs/release_notes_v0.6.10-a10.md`：本文件

---

## 五、修改檔案

- `jgod/research/storage.py`：新增 portfolio log 函數
- `jgod/research/walkforward_runner.py`：支援 external data_service + time sync
- `jgod/learning/models.py`：FeatureSubset 支援 global scope
- `jgod/learning/feature_selector.py`：新增 `select_global_features()`
- `jgod/api/routers/walkforward.py`：新增 portfolio 端點
- `scripts/ci_quick_check.sh`：新增 Check 24

---

## 六、API 端點

### 6.1 Portfolio Walk-Forward

- `POST /api/v1/walkforward/portfolio/run`：執行組合 Walk-Forward
- `GET /api/v1/walkforward/portfolio/latest`：取得最新組合報告
- `GET /api/v1/walkforward/portfolio/list?n=20`：列出組合日誌

---

## 七、CI 更新

**新增檢查：**
- Check 24：`pytest tests/test_portfolio_manager_contract.py -q`

---

## 八、已知限制

1. **Ledger 狀態持久化**：
   - 目前 Portfolio 模式每次創建新 Ledger
   - 未來需從前一日狀態載入

2. **Vol Parity 簡化**：
   - 目前使用最近 N 日 close 計算波動度
   - 未來可擴展到更複雜的風險模型

3. **Parallel Execution**：
   - 目前 `portfolio_parallel_enabled=False`（保守）
   - 未來可啟用並行執行

4. **Global Learning**：
   - 目前僅 Method Layer 支援 global scope
   - Thought/Strategy 仍維持 symbol-level

---

## 九、驗證命令

### 9.1 後端驗證

```bash
# 語法檢查
python3 -m compileall jgod -q

# CI 快速檢查（24 個檢查點）
bash scripts/ci_quick_check.sh

# 個別測試
pytest tests/test_portfolio_manager_contract.py -q -v
```

### 9.2 API 驗證

```bash
# 執行組合 Walk-Forward
curl -X POST "http://127.0.0.1:8000/api/v1/walkforward/portfolio/run" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["2330", "2317"],
    "start_date": "2024-04-01",
    "end_date": "2024-04-10",
    "initial_cash_total": 1000000.0,
    "allocation_mode": "equal_weight"
  }'

# 取得最新組合報告
curl "http://127.0.0.1:8000/api/v1/walkforward/portfolio/latest"

# 列出組合日誌
curl "http://127.0.0.1:8000/api/v1/walkforward/portfolio/list?n=20"
```

---

## 十、與前一版（v0.6.9-A9）的能力差異

| 項目 | v0.6.9-A9 | v0.6.10-A10 |
|------|-----------|-------------|
| 標的數量 | 單一標的 | 多標的組合 |
| Allocation | 無 | 有（equal_weight / vol_parity）|
| Portfolio Logs | 無 | 有（組合級 NAV/P&L）|
| Data Interface | 無 | 有（DataServiceInterface）|
| Time Sync | 無 | 有（確保多 runner 使用同一 T）|
| Global Learning | 無 | 有（Method Layer global scope）|

---

## 十一、後續延伸點（預留）

1. **Portfolio Risk Management**：
   - 組合級風險預算
   - 相關性調整

2. **Parallel Execution**：
   - 啟用並行執行（`portfolio_parallel_enabled=True`）
   - 並行安全保證

3. **Global Learning 擴展**：
   - Thought/Strategy Layer 支援 global scope
   - 跨標的策略優化

4. **Real-time Data Integration**：
   - 實作 RealTimeDataService（繼承 DataServiceInterface）
   - 即時資料接入

---

## 十二、總結

v0.6.10-A10 成功建立 Portfolio Manager 系統，實現多標的組合級 Walk-Forward 運行。所有標的使用獨立 Runner + Ledger，確保狀態隔離。Time sync check 確保資料一致性。所有 CI 檢查通過（24/24），測試 deterministic 可重現。

**下一步建議：**
- 開始 A11（Real-time Data Integration）
- 優化 Vol Parity 算法
- 啟用 Parallel Execution

