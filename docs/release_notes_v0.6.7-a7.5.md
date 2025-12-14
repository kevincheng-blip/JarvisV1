# J-GOD v0.6.7-A7.5 版本說明

**發布日期：** 2025-12-14  
**版本類型：** Milestone M2 (Feature DB/Cache & Data Pipeline)  
**目標：** Acceleration（資料加速）＋ Traceability（版本追溯）

---

## 一、版本定位

v0.6.7-A7.5 是「資料加速化」版本，建立 Feature DB/Cache 系統，讓 Walk-Forward 40 檔 × 250 天 + 每 5 日 auto-tuning 不再每次重算 50+10 因子，同時提供版本追溯能力，為 A8 Walk-Forward Runner 奠定高效資料基礎。

---

## 二、核心功能完成清單

### 2.1 Feature DB Schema

**功能說明：**
- 定義 `FeatureSchema`（symbol, date, version, ohlcv, features, meta）
- Key：`(symbol, date, version)` 作為唯一識別
- 目前 features dict 包含最小集合（SMA/RSI/RET/VOL），未來擴展到 50+10 因子

**實作位置：**
- `jgod/data/feature_models.py`：`FeatureSchema` dataclass

### 2.2 Feature Computer（因子計算器）

**功能說明：**
- 提供 `compute_features(ohlcv_series, version="v1.0")` 函數
- 最小因子集合（deterministic，純 Python）：
  - SMA_5, SMA_20（Simple Moving Average）
  - RSI_14（Relative Strength Index）
  - VOL_MEAN_20（Volume rolling mean）
  - RET_1D（1-day return）
- 所有計算 deterministic（相同輸入 → 相同輸出）

**實作位置：**
- `jgod/data/feature_computer.py`：`compute_features()` 函數

### 2.3 Feature Storage（JSONL 持久化）

**功能說明：**
- JSONL append-only 儲存（`data/features/features.jsonl`）
- 函數：`save_feature()`, `load_feature()`, `has_feature()`, `list_features()`
- 查詢方式：線性掃描（last one wins）
- 不將整檔載入 memory（逐行 scan）

**實作位置：**
- `jgod/data/feature_storage.py`：儲存層函數

### 2.4 Feature Service（統一入口）

**功能說明：**
- `FeatureService` 類別：統一取得特徵的入口
- `get_feature(symbol, date, version, lookback)`：
  - Cache hit → return
  - Cache miss → MDTS 取得 OHLCV → compute → save → return
- `recompute_range(symbol, start_date, end_date, version, force)`：
  - 逐日處理，已存在 skip（除非 force=True）
  - 回傳統計（computed_count, skipped_count, errors）

**實作位置：**
- `jgod/data/feature_service.py`：`FeatureService` 類別

### 2.5 BacktestEngine 解耦

**功能說明：**
- BacktestEngine 不再內部計算因子
- 每日 loop 使用 `FeatureService.get_feature()` 取得 features
- Features 記錄到 `daily_log`（ohlcv + features_summary）
- DecisionEngineV3 目前尚未直接使用 features（A8 將整合）

**實作位置：**
- `jgod/research/backtest_engine.py`：修改 daily loop

---

## 三、三大設計決策

### 3.1 儲存格式：JSONL append-only

**理由：**
- 便於增量寫入（append-only）
- CI 驗證容易（文字格式）
- 版本控制友好（git diff）
- 不鎖定資料庫（未來可遷移）

### 3.2 避免重算 Key：`(symbol, date, version)`

**理由：**
- `symbol` + `date`：唯一識別標的與日期
- `version`：因子計算邏輯版本（變更時需重算）
- 版本管理：同一日期不同 version 可並存（支援 A/B 測試）

### 3.3 統一入口：FeatureService

**理由：**
- 避免多處重複計算
- Cache hit/miss 邏輯集中管理
- 未來擴展容易（例如：分散式 cache、預計算 pipeline）

---

## 四、新增檔案

### 4.1 後端核心模組

- `jgod/data/feature_models.py`：FeatureSchema 定義
- `jgod/data/feature_computer.py`：因子計算邏輯
- `jgod/data/feature_storage.py`：JSONL 持久化
- `jgod/data/feature_service.py`：統一服務入口

### 4.2 測試

- `tests/test_feature_db_contract.py`：Feature DB 合約測試

### 4.3 文件

- `docs/release_notes_v0.6.7-a7.5.md`：本文件

---

## 五、修改檔案

- `jgod/research/backtest_engine.py`：解耦因子計算，使用 FeatureService
- `scripts/ci_quick_check.sh`：新增 Check 19

---

## 六、CI 更新

**新增檢查：**
- Check 19：`pytest tests/test_feature_db_contract.py -q`

---

## 七、已知限制

1. **Features 最小集合**：
   - 目前僅實作 SMA/RSI/RET/VOL（5 個因子）
   - 50+10 因子將逐步擴張（A8 或後續版本）

2. **DecisionEngineV3 尚未使用 features**：
   - 目前 `decide()` 方法不接受 features 參數
   - Features 已記錄到 `daily_log`，A8 將真正使用

3. **Storage 查詢效率**：
   - 目前使用線性掃描（last one wins）
   - 未來可優化為索引（例如：按 symbol 分檔）

4. **版本管理工具**：
   - 目前 `recompute_range()` 支援 partial rebuild
   - 未來可新增版本比較工具（v1.0 vs v1.1 差異分析）

---

## 八、驗證命令

### 8.1 後端驗證

```bash
# 語法檢查
python3 -m compileall jgod -q

# CI 快速檢查（19 個檢查點）
bash scripts/ci_quick_check.sh

# 個別測試
pytest tests/test_feature_db_contract.py -q -v
```

### 8.2 程式碼驗證

```python
# 測試 FeatureService
from jgod.data.feature_service import FeatureService

service = FeatureService(use_mock_mdts=True)
feature = service.get_feature("2330", "2024-01-20", version="v1.0", lookback=20)
print(f"Features: {feature.features}")

# 測試 cache hit
feature2 = service.get_feature("2330", "2024-01-20", version="v1.0", lookback=20)
assert feature.features == feature2.features  # Should be same (cached)

# 測試版本變更
feature_v1_1 = service.get_feature("2330", "2024-01-20", version="v1.1", lookback=20)
# Should recompute (different version)
```

---

## 九、與前一版（v0.6.6-A7）的能力差異

| 項目 | v0.6.6-A7 | v0.6.7-A7.5 |
|------|-----------|-------------|
| 因子計算 | BacktestEngine 內部計算 | FeatureService 統一計算 |
| 因子快取 | 無 | 有（JSONL append-only） |
| 版本管理 | 無 | 有（version 欄位） |
| 避免重算 | 無 | 有（cache hit/miss） |
| 資料追溯 | 無 | 有（版本化儲存） |

---

## 十、後續延伸點（預留）

1. **50+10 因子擴張**：
   - 逐步將 50+10 因子加入 `feature_computer.py`
   - 或升級為 typed fields（取代 dict）

2. **DecisionEngineV3 整合（A8）**：
   - `decide()` 方法接受 features 參數
   - 真正使用 Feature DB 的因子進行決策

3. **Storage 優化**：
   - 按 symbol 分檔（減少掃描範圍）
   - 索引建立（加速查詢）

4. **預計算 Pipeline**：
   - 每日自動計算新日期 features
   - 支援批次預計算（多標的、多日期）

---

## 十一、總結

v0.6.7-A7.5 成功建立 Feature DB/Cache 系統，讓 Walk-Forward 系統不再每次重算因子，同時提供版本追溯能力。所有 CI 檢查通過（19/19），測試 deterministic 可重現。

**下一步建議：**
- 開始 A8-M3（Walk-Forward Runner + Learning Layers）
- 擴展 50+10 因子（逐步實作）

