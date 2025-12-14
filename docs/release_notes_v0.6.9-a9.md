# J-GOD v0.6.9-A9 版本說明

**發布日期：** 2025-12-14  
**版本類型：** Auto-Pilot Activation & Guard Rails（Conditional Self-Evolution + Async Learning）  
**目標：** 安全地讓智慧變成行動

---

## 一、版本定位

v0.6.9-A9 是「Auto-Pilot 啟動」版本，在 A8 的基礎上，建立 Guard Rails 機制，讓 Learning 輸出的智慧能夠「安全地自動套用」。核心原則：**可回滾、可審計、可關閉**。

---

## 二、核心功能完成清單

### 2.1 Learning BaseLayer（Guard Rails 核心）

**功能說明：**
- 抽象基底類別：`BaseLayer`
- `compute_quality_score(output_dict)`：計算品質分數（0.0 ~ 1.0）
- `auto_apply_threshold()`：取得自動套用門檻（每層不同）
- `should_auto_apply(score)`：判斷是否應自動套用
- `finalize_status(score)`：決定最終狀態（PENDING / AUTO_APPLY / REJECTED）

**門檻設定：**
- Thought Layer：0.15（基於 score_delta / pnl_delta / mdd_change）
- Method Layer：0.12（基於 top_feature_score_mean）
- Strategy Layer：0.10（基於 composite_score_delta）

**實作位置：**
- `jgod/learning/base_layer.py`：`BaseLayer` 類別

### 2.2 Learning Outputs 狀態機強化

**功能說明：**
- 新增 `PatchStatus` enum：`PENDING_APPROVAL`, `AUTO_APPLY`, `REJECTED`
- 所有 layer 輸出包含：
  - `quality_score: float`
  - `status: PatchStatus`
  - `snapshot_id: str`（一致性保證）

**實作位置：**
- `jgod/learning/models.py`：`PatchStatus` enum，更新 `TuningPatch`, `FeatureSubset`, `StrategyAllocation`

### 2.3 三層 Learning：計分 + 自動狀態

**功能說明：**
- 每個 layer 繼承 `BaseLayer`
- 輸出生成時：
  - 計算 `quality_score`
  - 根據 threshold 決定 `status`
  - 必須帶入 `snapshot_id`
- 不得直接 `apply_patch`：只產生建議 + status

**實作位置：**
- `jgod/learning/tuning_advisor.py`：繼承 BaseLayer，計算 quality_score
- `jgod/learning/feature_selector.py`：同上
- `jgod/learning/strategy_allocator.py`：同上

### 2.4 Snapshot Consistency（學習觸發時凍結資料）

**功能說明：**
- `create_snapshot_id(symbol, start_date, end_date, doctrine_version)`：產生 deterministic snapshot ID
- Snapshot ID 格式：`SNAP-{symbol}-{start}-{end}-{version}-{hash}`
- `create_snapshot_payload()`：產生完整 snapshot payload
- 儲存至 `data/research/snapshots.jsonl`

**實作位置：**
- `jgod/research/snapshot.py`：Snapshot 生成邏輯
- `jgod/research/storage.py`：`save_snapshot()`, `load_snapshot()`

### 2.5 WalkForwardRunner：Auto-Pilot + Async + Shadow Run

**功能說明：**
- Feature flags：
  - `autopilot_enabled: bool = False`
  - `autopilot_apply_only_when_status_auto: bool = True`
  - `async_learning_enabled: bool = True`
- Daily cycle 不阻塞：
  - Method/Strategy 使用 `ThreadPoolExecutor` 異步執行
  - Thought（5日）可同步或異步
- Auto-apply 流程：
  - 當學習輸出是 `AUTO_APPLY` 時，Runner 呼叫 `doctrine.apply_patch()`
  - 產生新版本（append-only）
  - 記錄來源（patch_id, snapshot_id, layer）
- Shadow Run（90天）：
  - `run_shadow()` 方法
  - 同時跑 AUTOPILOT_ON 和 BASELINE_STATIC
  - 輸出 `ShadowReport`（final_nav_delta, pnl_delta, mdd_delta, number_of_patches_auto_applied）

**實作位置：**
- `jgod/research/walkforward_runner.py`：修改 `__init__()`, `_trigger_*_layer()`, 新增 `run_shadow()`

### 2.6 Doctrine：支援 Runner 自動 apply + 回滾保持

**功能說明：**
- `apply_patch()` 支援 `patch_id`, `snapshot_id`, `layer` 參數
- 版本儲存 append-only：沿用 `data/config/doctrine.jsonl`
- `rollback()` 維持 A8 邏輯

**實作位置：**
- `jgod/config/doctrine.py`：修改 `apply_patch()` 簽名

### 2.7 API：通知查詢 / Shadow 報告查詢

**功能說明：**
- `GET /api/v1/walkforward/notifications/latest`：取得最新通知
- `GET /api/v1/walkforward/notifications/list?n=50`：列出通知
- `POST /api/v1/walkforward/shadow/run/{symbol}`：執行 Shadow Run
- 所有端點保證 200（空狀態不 404）

**實作位置：**
- `jgod/api/routers/walkforward.py`：新增端點
- `jgod/api/schemas/walkforward_notifications.py`：Pydantic schemas

---

## 三、Guard Rails 設計

### 3.1 三層的 quality_score 算法

**Thought Layer：**
- 輸入：`score_delta`, `pnl_delta`, `mdd_change`
- 計算：`0.4 * score_component + 0.4 * pnl_component + 0.2 * mdd_component`
- 門檻：0.15

**Method Layer：**
- 輸入：`feature_scores`（相關性分數）
- 計算：Top 3 features 平均分數，正規化到 [0, 1]
- 門檻：0.12

**Strategy Layer：**
- 輸入：`strategy_scores`（composite_score）
- 計算：`(best_score - current_score) / 0.2`，正規化到 [0, 1]
- 門檻：0.10

### 3.2 Auto-apply 狀態機

```
quality_score >= threshold → AUTO_APPLY
threshold * 0.5 <= quality_score < threshold → PENDING_APPROVAL
quality_score < threshold * 0.5 → REJECTED
```

---

## 四、新增檔案

### 4.1 後端核心模組

- `jgod/learning/base_layer.py`：Guard Rails 基底類別
- `jgod/research/snapshot.py`：Snapshot 生成邏輯
- `jgod/api/schemas/walkforward_notifications.py`：通知 schemas

### 4.2 測試

- `tests/test_autopilot_guardrails_contract.py`：A9 合約測試

### 4.3 文件

- `docs/release_notes_v0.6.9-a9.md`：本文件

---

## 五、修改檔案

- `jgod/learning/models.py`：新增 quality_score, status enum, snapshot_id
- `jgod/learning/tuning_advisor.py`：繼承 BaseLayer，計算 quality_score
- `jgod/learning/feature_selector.py`：同上
- `jgod/learning/strategy_allocator.py`：同上
- `jgod/config/doctrine.py`：支援 auto_apply 參數
- `jgod/research/storage.py`：新增 snapshot + notification log
- `jgod/research/walkforward_runner.py`：Auto-Pilot + Async + Shadow Run
- `jgod/api/routers/walkforward.py`：新增通知查詢端點
- `scripts/ci_quick_check.sh`：新增 Check 22/23

---

## 六、API 端點

### 6.1 通知查詢

- `GET /api/v1/walkforward/notifications/latest`：取得最新通知
- `GET /api/v1/walkforward/notifications/list?n=50`：列出通知

### 6.2 Shadow Run

- `POST /api/v1/walkforward/shadow/run/{symbol}?start_date=...&end_date=...&autopilot=true`：執行 Shadow Run

---

## 七、CI 更新

**新增檢查：**
- Check 22：`pytest tests/test_autopilot_guardrails_contract.py -q`
- Check 23：Shadow run smoke test（unit stub）

---

## 八、已知限制

1. **Ledger 狀態持久化**：
   - Shadow Run 目前每次創建新 Ledger
   - 未來需從前一日狀態載入

2. **Async Learning 錯誤處理**：
   - 目前使用 fire-and-forget
   - 未來可加入錯誤回報機制

3. **Shadow Run 對照組**：
   - 目前 baseline 是固定策略（無學習）
   - 未來可擴展到其他 baseline 模式

4. **Quality Score 調參**：
   - 目前門檻是寫死的常數
   - 未來可配置化或動態調整

---

## 九、驗證命令

### 9.1 後端驗證

```bash
# 語法檢查
python3 -m compileall jgod -q

# CI 快速檢查（23 個檢查點）
bash scripts/ci_quick_check.sh

# 個別測試
pytest tests/test_autopilot_guardrails_contract.py -q -v
pytest tests/test_walkforward_runner_contract.py -q -v
pytest tests/test_learning_layers_contract.py -q -v
```

### 9.2 API 驗證

```bash
# 取得最新通知
curl "http://127.0.0.1:8000/api/v1/walkforward/notifications/latest"

# 列出通知
curl "http://127.0.0.1:8000/api/v1/walkforward/notifications/list?n=50"

# 執行 Shadow Run
curl -X POST "http://127.0.0.1:8000/api/v1/walkforward/shadow/run/2330?start_date=2024-01-01&end_date=2024-04-01&autopilot=true"
```

---

## 十、與前一版（v0.6.8-A8）的能力差異

| 項目 | v0.6.8-A8 | v0.6.9-A9 |
|------|-----------|-----------|
| Learning 輸出狀態 | 僅 PENDING_APPROVAL | PENDING / AUTO_APPLY / REJECTED |
| Quality Score | 無 | 有（每層獨立算法）|
| Auto-Apply | 無 | 有（條件式自動套用）|
| Async Learning | 無 | 有（Method/Strategy 不阻塞）|
| Snapshot | 無 | 有（學習觸發時凍結資料）|
| Shadow Run | 無 | 有（90 天對照測試）|
| Notification | 無 | 有（學習結束通知）|

---

## 十一、後續延伸點（預留）

1. **Quality Score 動態調整**：
   - 基於歷史表現調整門檻
   - 不同市場環境使用不同門檻

2. **Shadow Run 擴展**：
   - 多種 baseline 模式
   - 組合最佳化

3. **Async Learning 錯誤處理**：
   - 錯誤回報機制
   - 重試邏輯

4. **Portfolio Manager（A10）**：
   - 多標的組合管理
   - 風險分散

---

## 十二、總結

v0.6.9-A9 成功建立 Auto-Pilot Activation & Guard Rails 系統，實現條件式自動套用、異步學習、Shadow Run 驗證。所有學習建議均需通過品質門檻才能自動套用，確保可控性。所有 CI 檢查通過（23/23），測試 deterministic 可重現。

**下一步建議：**
- 開始 A10（Portfolio Manager）
- 優化 Quality Score 算法
- 擴展 Shadow Run 對照組

