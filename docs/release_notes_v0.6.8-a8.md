# J-GOD v0.6.8-A8 版本說明

**發布日期：** 2025-12-14  
**版本類型：** Walk-Forward Runner & Learning Layers（AI 自我演化閉環）  
**目標：** 建立可持續演化、可被人類審核的研究級閉環系統

---

## 一、版本定位

v0.6.8-A8 是「AI 自我演化閉環」版本，將 Decision V3 + M1 真實 P&L + M2 Feature DB 串成一個可持續演化、可被人類審核的研究級閉環系統。解決三個歷史問題：
1. **學習是黑盒** → 現在全部版本化、可回放
2. **修正不可控** → 現在只產生 Patch 建議，不自動生效
3. **滾動實驗不嚴謹** → 現在嚴格 Walk-Forward（只用過去資料）

---

## 二、核心功能完成清單

### 2.1 Walk-Forward Runner（核心調度者）

**功能說明：**
- 嚴格使用 T-1 資料（無未來資料洩漏）
- 支援指定：`start_date`, `end_date`, `symbol_list`, `doctrine_version`
- 每日流程（嚴格順序）：
  1. 讀取 FeatureService → 當日 features
  2. 呼叫 DecisionEngineV3.decide(features=..., doctrine=...)
  3. OrderEngine → FillEngine → VirtualLedger
  4. 寫入 daily_log（JSONL）
  5. 檢查是否觸發學習週期（5/10/20/季）
- 所有結果寫入：`data/research/walkforward_logs.jsonl`

**實作位置：**
- `jgod/research/walkforward_runner.py`：`WalkForwardRunner` 類別

### 2.2 DecisionEngineV3 參數化

**功能說明：**
- `decide()` 方法現在接受：
  - `features: dict`（來自 FeatureService）
  - `doctrine_config: DoctrineConfig`（版本化配置）
  - `feature_subset: list[str]`（Method Layer 篩選的子集）
- 若未傳 `features` → raise 明確錯誤（A8 不再允許隱性 proxy）
- 使用 `doctrine_config.risk_mapping` 計算風險計劃

**實作位置：**
- `jgod/decision_v3/engine.py`：修改 `decide()` 和 `_calculate_risk_plan()`

### 2.3 Thought Layer（5 日調參）

**功能說明：**
- 輸入：最近 5 日 Walk-Forward P&L + Arena 結果
- 輸出：`TuningPatch` 建議（只產生建議，不套用）
  - `patch_id`, `target`, `changes`, `reason`, `evidence`
- 存放：`data/learning/thought_log.jsonl`

**實作位置：**
- `jgod/learning/tuning_advisor.py`：`analyze_and_suggest_patch()`

### 2.4 Method Layer（10/20 日）

**功能說明：**
- 使用 BacktestEngine + Feature DB 比較多組 FeatureSubset
- 選出 P&L 最佳子集
- 輸出：`FeatureSubset` 建議（只產生建議，不套用）
  - `recommended_features`, `reason`, `evidence`
- 存放：`data/learning/method_log.jsonl`

**實作位置：**
- `jgod/learning/feature_selector.py`：`analyze_and_suggest_subset()`

### 2.5 Strategy Layer（季）

**功能說明：**
- 判斷是否切換 PrimaryStrategy
- 輸出：`StrategyAllocation` 建議（只產生建議，不套用）
  - `recommended_primary_strategy`, `recommended_secondary_strategies`, `reason`, `evidence`
- 存放：`data/learning/strategy_log.jsonl`

**實作位置：**
- `jgod/learning/strategy_allocator.py`：`analyze_and_suggest_allocation()`

### 2.6 Doctrine Patch（可回滾）

**功能說明：**
- Doctrine 必須有 `version`
- `apply_patch` 需透過 API（手動審核）
- 所有舊版本保留
- 可 `rollback` 到舊版本

**實作位置：**
- `jgod/config/doctrine.py`：`DoctrineConfig`, `apply_patch()`, `rollback_to_version()`

---

## 三、四層結構（正式落地）

| 層級 | 模組 | 職責 | 輸出 |
|------|------|------|------|
| Data | Feature DB（已完成） | 提供高速、版本化特徵 | FeatureSchema |
| Method | feature_selector | 10/20 日因子歸因與篩選 | FeatureSubset |
| Thought | tuning_advisor | 5 日調參，產生 Patch 建議 | DoctrinePatch |
| Strategy | strategy_allocator | 季/宏觀策略切換 | StrategyAllocation |

**WalkForwardRunner 是總調度者，不做學習，只負責觸發。**

---

## 四、新增檔案

### 4.1 後端核心模組

- `jgod/learning/__init__.py`：Learning 模組初始化
- `jgod/learning/models.py`：FeatureSubset, TuningPatch, StrategyAllocation
- `jgod/learning/feature_selector.py`：Method Layer
- `jgod/learning/tuning_advisor.py`：Thought Layer
- `jgod/learning/strategy_allocator.py`：Strategy Layer
- `jgod/config/__init__.py`：Config 模組初始化
- `jgod/config/doctrine.py`：Doctrine 版本管理
- `jgod/research/storage.py`：Walk-Forward 日誌儲存
- `jgod/research/walkforward_runner.py`：Walk-Forward Runner

### 4.2 API

- `jgod/api/routers/walkforward.py`：Walk-Forward API
- `jgod/api/routers/config.py`：Config API

### 4.3 測試

- `tests/test_walkforward_runner_contract.py`：Walk-Forward Runner 合約測試
- `tests/test_learning_layers_contract.py`：Learning Layers 合約測試

### 4.4 文件

- `docs/release_notes_v0.6.8-a8.md`：本文件

---

## 五、修改檔案

- `jgod/decision_v3/engine.py`：參數化 `decide()` 方法
- `jgod/api/main.py`：註冊 walkforward 和 config routers
- `jgod/api/routers/__init__.py`：匯出新 routers
- `scripts/ci_quick_check.sh`：新增 Check 20/21

---

## 六、API 端點

### 6.1 Walk-Forward API

- `POST /api/v1/walkforward/run-daily/{symbol}`：執行單日循環
- `POST /api/v1/walkforward/run-range/{symbol}`：執行日期範圍

### 6.2 Config API

- `GET /api/v1/config/doctrine/{version}`：取得 Doctrine 配置
- `GET /api/v1/config/doctrine/versions`：列出所有版本
- `POST /api/v1/config/doctrine/apply-patch`：套用 Patch（需手動審核）
- `POST /api/v1/config/doctrine/rollback/{version}`：回滾到舊版本

---

## 七、CI 更新

**新增檢查：**
- Check 20：`pytest tests/test_walkforward_runner_contract.py -q`
- Check 21：`pytest tests/test_learning_layers_contract.py -q`

---

## 八、已知限制

1. **Ledger 狀態持久化**：
   - 目前每日循環創建新 Ledger（簡化版）
   - 未來需從前一日狀態載入

2. **Learning Layers 觸發條件**：
   - 目前使用簡單的日期計數（每 5/10/20/60 日）
   - 未來可改為更智能的觸發條件

3. **Feature Subset 選擇**：
   - 目前使用簡單的相關性分析
   - 未來可改為更複雜的歸因分析

4. **Strategy Allocation**：
   - 目前僅分析 Primary Strategy
   - 未來可擴展到 Secondary Strategies 組合

---

## 九、驗證命令

### 9.1 後端驗證

```bash
# 語法檢查
python3 -m compileall jgod -q

# CI 快速檢查（21 個檢查點）
bash scripts/ci_quick_check.sh

# 個別測試
pytest tests/test_walkforward_runner_contract.py -q -v
pytest tests/test_learning_layers_contract.py -q -v
```

### 9.2 API 驗證

```bash
# 執行單日循環
curl -X POST "http://127.0.0.1:8000/api/v1/walkforward/run-daily/2330?date=2024-04-01"

# 執行日期範圍
curl -X POST "http://127.0.0.1:8000/api/v1/walkforward/run-range/2330?start_date=2024-04-01&end_date=2024-04-10"

# 取得 Doctrine 配置
curl "http://127.0.0.1:8000/api/v1/config/doctrine/v1.0"
```

---

## 十、與前一版（v0.6.7-A7.5）的能力差異

| 項目 | v0.6.7-A7.5 | v0.6.8-A8 |
|------|-------------|-----------|
| Decision Engine | 不接受 features 參數 | 接受 features + doctrine_config |
| 學習機制 | 無 | 有（Thought/Method/Strategy 三層）|
| 版本管理 | 無 | 有（Doctrine 版本化）|
| Walk-Forward | 無 | 有（嚴格 T-1 資料）|
| 自動套用 | N/A | 禁止（只產生建議）|

---

## 十一、後續延伸點（預留）

1. **Ledger 狀態持久化**：
   - 從前一日狀態載入 Ledger
   - 支援多標的 Ledger

2. **智能觸發條件**：
   - 基於 P&L 波動的觸發
   - 基於策略表現的觸發

3. **更複雜的歸因分析**：
   - SHAP 值分析
   - 因子重要性排序

4. **多標的 Walk-Forward**：
   - 支援 symbol_list 批次執行
   - 組合最佳化

---

## 十二、總結

v0.6.8-A8 成功建立 Walk-Forward Runner & Learning Layers 系統，實現 AI 自我演化閉環。所有學習建議均需手動審核，確保可控性。所有 CI 檢查通過（21/21），測試 deterministic 可重現。

**下一步建議：**
- 開始 A9（真實交易沙盒 / Paper Trading）
- 優化 Ledger 狀態持久化
- 擴展多標的 Walk-Forward

