# J-GOD v0.6.6-A7 版本說明

**發布日期：** 2025-12-14  
**版本類型：** Milestone M1 (Realism Foundation)  
**目標：** 修正 Reward Signal（Grounding：OHLCV + Fill 摩擦），淘汰 proxy P&L

---

## 一、版本定位

v0.6.6-A7 是「真實性基礎化」版本，建立 Market Data Time Series Service (MDTS)、Fill Engine 和 Backtest Core，讓 Decision V3 的評估與競技場系統從「價格代理（price proxy）」升級為「基於真實 OHLCV 與撮合摩擦的評估」，為 A8 Walk-Forward 奠定唯一真實研究基礎。

---

## 二、核心功能完成清單

### 2.1 Market Data Time Series Service (MDTS)

**功能說明：**
- 提供 OHLCV 時序資料（Open, High, Low, Close, Volume）
- 優先使用現有 SQLite 資料庫（`tw_stock_daily` 表）
- 若資料庫無資料，fallback 到 deterministic mock（測試用）
- 支援單日查詢和日期範圍查詢

**實作位置：**
- `jgod/data/market_data_service.py`：`MarketDataService` 類別

**關鍵方法：**
- `fetch_ohlcv(symbol, date_str)`：取得單日 OHLCV
- `fetch_ohlcv_range(symbol, start_date, end_date)`：取得日期範圍 OHLCV

### 2.2 Fill Engine（撮合引擎）

**功能說明：**
- 模擬訂單執行，考慮市場摩擦：
  - Slippage（滑點）：BUY 0.1%，SELL 0.05%
  - Fees（手續費）：0.1425%
  - Tax（賣出稅）：0.3%（僅 SELL）
- 產生 `OrderFill` 結果（qty_executed, fill_price, fee, tax, slippage）

**實作位置：**
- `jgod/execution/fill_engine.py`：`FillEngine.execute()`

**邏輯：**
- BUY：fill_price = close * (1 + slippage_rate)，clamp 到 high
- SELL：fill_price = close * (1 - slippage_rate)，clamp 到 low

### 2.3 Backtest Core（回測核心）

**功能說明：**
- 提供 deterministic 回測引擎（可重現）
- 逐日 loop：Decision → Order → Fill → Ledger Update
- 產生 `BacktestReport`（final_nav, metrics, daily_log）

**實作位置：**
- `jgod/research/backtest_engine.py`：`BacktestEngine.run()`

**流程：**
1. 初始化 VirtualLedger
2. 取得 OHLCV 範圍
3. 逐日處理：
   - Mark to market
   - 計算 Decision
   - 生成 Order
   - 執行 Fill
   - 更新 Ledger
   - 記錄 Daily Log
4. 計算 Metrics（total_return, avg_daily_return, max_drawdown, sharpe_ratio, hit_rate, turnover）

### 2.4 Decision V3 Evaluation 升級

**功能說明：**
- 新增 `evaluate_decision_v3_with_backtest()` 方法
- 使用 BacktestCore 取代 proxy P&L
- 保留原有 `evaluate_decision_v3()` 作為 fallback

**實作位置：**
- `jgod/decision_v3/evaluation.py`：新增方法

**注意：**
- 目前 Arena 仍使用原有方法（proxy），A8 將全面切換到 BacktestCore

---

## 三、新增檔案

### 3.1 後端核心模組

- `jgod/data/market_data_service.py`：MDTS 服務
- `jgod/execution/fill_engine.py`：撮合引擎
- `jgod/research/__init__.py`：Research 模組初始化
- `jgod/research/backtest_engine.py`：回測引擎

### 3.2 測試

- `tests/test_mdts_contract.py`：MDTS 合約測試
- `tests/test_fill_engine_contract.py`：Fill Engine 合約測試
- `tests/test_backtest_core_contract.py`：Backtest Core 合約測試

### 3.3 文件

- `spec/A7_A8_WalkForward_MasterPlan.md`：A7/A8 Master Plan
- `docs/release_notes_v0.6.6-a7.md`：本文件

---

## 四、修改檔案

- `jgod/execution/virtual_ledger.py`：新增 `apply_fill()` 方法
- `jgod/decision_v3/evaluation.py`：新增 `evaluate_decision_v3_with_backtest()` 方法
- `scripts/ci_quick_check.sh`：新增 Check 16/17/18

---

## 五、CI 更新

**新增檢查：**
- Check 16：`pytest tests/test_mdts_contract.py -q`
- Check 17：`pytest tests/test_fill_engine_contract.py -q`
- Check 18：`pytest tests/test_backtest_core_contract.py -q`

---

## 六、已知限制

1. **MDTS 資料來源**：
   - 優先使用 SQLite DB，若無資料則 fallback 到 mock
   - Mock 資料為 deterministic，但非真實市場價格
   - 未來需整合真實價格資料源（A8）

2. **BacktestEngine 與 Decision Engine 整合**：
   - 目前 BacktestEngine 內部直接呼叫 `DecisionEngineV3.decide()`
   - 尚未使用 Feature DB（A7.5-M2 將實作）

3. **Arena 尚未切換**：
   - `arena.py` 仍使用原有 `evaluate_decision_v3()`（proxy）
   - A8 將全面切換到 BacktestCore

4. **Slippage 參數固定**：
   - 目前 slippage 為固定值（BUY 0.1%, SELL 0.05%）
   - 未來可根據 volume 動態調整

---

## 七、驗證命令

### 7.1 後端驗證

```bash
# 語法檢查
python3 -m compileall jgod -q

# CI 快速檢查（18 個檢查點）
bash scripts/ci_quick_check.sh

# 個別測試
pytest tests/test_mdts_contract.py -q -v
pytest tests/test_fill_engine_contract.py -q -v
pytest tests/test_backtest_core_contract.py -q -v
```

### 7.2 程式碼驗證

```python
# 測試 MDTS
from jgod.data.market_data_service import MarketDataService
mdts = MarketDataService(use_mock=True)
snapshot = mdts.fetch_ohlcv("2330", "2024-01-15")
print(snapshot)

# 測試 Fill Engine
from jgod.execution.fill_engine import FillEngine
from jgod.execution.order_engine import OrderRequest
from jgod.data.market_data_service import OHLCVSnapshot

order = OrderRequest(symbol="2330", side="BUY", qty=100, reason="Test", target_position_scale=0.5, current_position_scale=0.0)
ohlcv = OHLCVSnapshot(symbol="2330", date="2024-01-15", open=100.0, high=105.0, low=99.0, close=104.0, volume=1000000.0)
fill = FillEngine.execute(order, ohlcv)
print(fill)

# 測試 BacktestEngine
from jgod.research.backtest_engine import BacktestEngine, BacktestConfig
engine = BacktestEngine(use_mock_mdts=True)
config = BacktestConfig(initial_cash=1_000_000.0)
report = engine.run("2330", "2024-01-01", "2024-01-31", config)
print(f"Final NAV: {report.final_nav}, Total Return: {report.metrics.total_return}")
```

---

## 八、與前一版（v0.6.5-A6）的能力差異

| 項目 | v0.6.5-A6 | v0.6.6-A7 |
|------|-----------|-----------|
| 價格來源 | 價格代理（從 final_score 推導） | 真實 OHLCV（DB 或 mock） |
| 撮合摩擦 | 無 | 有（slippage + fee + tax） |
| 回測引擎 | 無 | 有（BacktestEngine） |
| 評估基礎 | Proxy P&L | BacktestCore P&L（可選） |
| 真實性 | 低（可能作弊） | 高（真實市場摩擦） |

---

## 九、後續延伸點（預留）

1. **Feature DB 整合（A7.5-M2）**：
   - BacktestEngine 使用 Feature DB 取得因子資料
   - 避免每次重算 365 天因子

2. **Arena 全面切換（A8）**：
   - `arena.py` 使用 BacktestCore 取代 proxy
   - 所有評估基於真實 P&L

3. **Walk-Forward Runner（A8-M3）**：
   - 使用 BacktestEngine 作為每日 cycle 的基礎
   - 整合 Learning Layers（T/M/S）

---

## 十、總結

v0.6.6-A7 成功建立真實性基礎設施，讓 Decision V3 的評估系統從「理論指標」升級為「基於真實 OHLCV 與撮合摩擦的評估」，為 A8 Walk-Forward 奠定唯一真實研究基礎。所有 CI 檢查通過（18/18），測試 deterministic 可重現。

**下一步建議：**
- 開始 A7.5-M2（Feature DB/Cache）
- 準備 A8-M3（Walk-Forward Runner + Learning Layers）

