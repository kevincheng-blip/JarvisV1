# J-GOD 穩定化 Sprint v1 計畫

**目標**: 將系統健康度從 79 分提升到 90 分以上  
**時間**: 2025-12-04  
**策略**: 不增加新功能，只做穩定化與文件補齊

---

## 📋 Sprint 任務清單

### 1️⃣ Path A 固化（高優先級）

#### 1.1 建立 Path A Spec 文件
- **檔案**: `spec/JGOD_PathAEngine_Spec.md`
- **內容**:
  - Path A 的目標與定位
  - 主要模組說明（Loader / Feature Engine / Alpha Engine / Risk Model / Optimizer / Execution / Backtest Runner / Reporter）
  - 每個模組的 input / output / 關鍵方法
  - Path A 與 Path B/C/D 的關係

#### 1.2 補齊 Path A 測試
- **新增檔案**: `tests/path_a/test_path_a_integration_smoke.py`
  - 最小可運作的 smoke test（使用 mock data loader）
  - 測試完整 backtest 流程
  
- **新增檔案**: `tests/path_a/test_path_a_extreme_mode_smoke.py`
  - Extreme mode smoke test（使用 extreme mock data loader）
  - 測試 extreme mode 完整流程

- **整理現有測試**: 
  - 確認 `test_path_a_backtest_skeleton.py` 是否足夠
  - 確認命名與結構清晰

---

### 2️⃣ 舊版 / 重複檔案整理

#### 2.1 檢查並處理舊版檔案
- **`jgod/model/path_a_engine.py`**
  - 檢查是否被使用
  - 若未使用：加註 `# LEGACY: do not use for new development`
  
- **`jgod/rl/rl_engine.py`**
  - 檢查是否被使用（Path D 已有完整實作）
  - 若未使用：加註 `# LEGACY: do not use for new development`

#### 2.2 處理原則
- 避免更動現役模組
- 只標記或移動未使用的檔案
- 保留檔案以避免破壞性變更

---

### 3️⃣ 建立最小版 E2E 測試

#### 3.1 建立 E2E 測試目錄
- **目錄**: `tests/e2e/`
- **檔案**: `test_path_abcd_pipeline.py`

#### 3.2 測試內容
- 使用 mock 資料
- 依序呼叫：
  1. Path A backtest（至少一個 window）
  2. Path B walk-forward（最小配置）
  3. Path C scenario（跑一個最基礎 scenario）
  4. Path D eval（輕量級 eval，使用預訓練或簡單 policy）

#### 3.3 驗證
- 測試能成功執行完畢
- 關鍵輸出檔案存在
- 確認整個 ABCD pipeline 可以正常運作

---

## 📝 預期修改/新增檔案清單

### 新增檔案
1. `spec/JGOD_PathAEngine_Spec.md` - Path A 技術規格
2. `tests/path_a/test_path_a_integration_smoke.py` - Path A 整合 smoke test
3. `tests/path_a/test_path_a_extreme_mode_smoke.py` - Path A Extreme mode smoke test
4. `tests/e2e/__init__.py` - E2E 測試模組初始化
5. `tests/e2e/test_path_abcd_pipeline.py` - 完整 pipeline E2E 測試

### 修改檔案
1. `jgod/model/path_a_engine.py` - 加註 LEGACY（若未使用）
2. `jgod/rl/rl_engine.py` - 加註 LEGACY（若未使用）
3. `docs/JGOD_GLOBAL_SYSTEM_AUDIT_v1.md` - 更新進度紀錄

---

## ✅ 驗收標準

1. ✅ Path A Spec 文件完整且格式一致
2. ✅ Path A 測試可通過（smoke test + extreme mode）
3. ✅ 舊版檔案已標記或處理
4. ✅ E2E 測試可執行並通過
5. ✅ Audit 報告已更新進度

---

## 🎯 預期成果

- **系統健康度**: 79 → 90+
- **測試覆蓋度**: 75 → 85+
- **文件完整性**: 80 → 95+
- **程式碼品質**: 80 → 85+

---

**開始執行時間**: 2025-12-04

