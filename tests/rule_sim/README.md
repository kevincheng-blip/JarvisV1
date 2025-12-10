# Rule Simulation Engine Test Suite

本測試套件針對 J-GOD Rule Simulation Engine v1.0 進行測試。

## 測試範圍 (Test Scope)

### 單元測試 (Unit Tests)

1. **test_models.py** - 資料模型
   - RuleSetRef 建立與欄位驗證
   - RuleSimExperimentConfig 建立
   - RuleSimArmMetrics / RuleSimDeltaMetrics 建立
   - RuleSimReport 建立與欄位存取

2. **test_storage.py** - JSONL 儲存
   - save_report 與 load_recent 基本流程
   - load_recent 分頁與排序（新到舊）
   - load_by_id 查找存在/不存在的報告
   - 無效 JSON 行處理（錯誤容忍）

3. **test_sandbox_applier.py** - 沙盒套用器
   - create_sandbox 目錄建立
   - 不修改 production 檔案（hash/mtime 驗證）
   - Doctrine section 覆寫邏輯

4. **test_engine.py** - 核心引擎
   - 成功執行完整實驗
   - Recommendation 邏輯：APPROVE / CAUTION / REJECT
   - 錯誤處理（data_access 例外）
   - storage.save_report 呼叫驗證

### 整合測試 (Integration Tests)

5. **test_api_rule_sim.py** - API 層
   - POST /api/v1/rule-sim/run：觸發實驗
   - GET /api/v1/rule-sim/experiments/recent：取得最近實驗
   - GET /api/v1/rule-sim/experiments/{id}：取得詳細報告（存在/不存在）

6. **test_cli_rule_sim.py** - CLI 腳本
   - 基本執行（smoke test）
   - 缺少必填參數錯誤處理
   - 無效日期格式處理
   - 完整參數執行

## 測試資料 (Test Data)

測試使用以下 mock 資料：

- `sample_universe`: 測試股票池 ["2330", "2317", "3008", "3034"]
- `sample_ruleset_ref`: 測試用 Doctrine section 參考
- `sample_experiment_config`: 完整實驗配置
- `mock_data_access`: 模擬 PathA 回測結果（可調整 baseline/variant 指標）
- `mock_sandbox_applier`: 模擬沙盒建立器
- `mock_doctrine_service`: 模擬 Doctrine Service V2

## 執行測試 (Running Tests)

### 執行所有測試

```bash
# 執行整個測試套件
pytest tests/rule_sim/

# 顯示詳細輸出
pytest tests/rule_sim/ -v -s

# 顯示覆蓋率
pytest tests/rule_sim/ --cov=jgod.rule_sim --cov-report=html
```

### 執行特定測試

```bash
# 執行特定測試檔案
pytest tests/rule_sim/test_engine.py

# 執行特定測試類別
pytest tests/rule_sim/test_engine.py::TestRuleSimEngineV1

# 執行特定測試方法
pytest tests/rule_sim/test_engine.py::TestRuleSimEngineV1::test_successful_experiment
```

### 執行時顯示詳細輸出

```bash
# 顯示 print 輸出
pytest tests/rule_sim/ -s

# 顯示最詳細資訊
pytest tests/rule_sim/ -vv

# 顯示失敗時的局部變數
pytest tests/rule_sim/ -l
```

## 測試環境需求 (Requirements)

- Python 3.8+
- pytest
- fastapi[test] (for TestClient)
- 可選：pytest-cov（覆蓋率報告）

安裝測試依賴：

```bash
pip install pytest pytest-cov fastapi[test]
```

## 測試策略 (Test Strategy)

1. **隔離測試**: 使用 mock 物件，不實際執行 PathA 回測
2. **沙盒隔離**: 所有測試使用 `tmp_path`，不修改 production 檔案
3. **推薦邏輯覆蓋**: 測試 APPROVE / CAUTION / REJECT 三種情境
4. **錯誤處理**: 驗證例外情況下的報告生成與狀態設定
5. **API 測試**: 使用 FastAPI TestClient，不啟動實際伺服器

## 注意事項 (Notes)

- 所有測試使用臨時目錄（`tmp_path`），不會修改 production 設定檔
- Mock 物件模擬 PathAEngineV1，避免實際執行耗時的回測
- CLI 測試使用 `sys.argv` monkeypatch，不實際執行 subprocess
- API 測試使用 FastAPI TestClient，不啟動 HTTP 伺服器

## 測試覆蓋率目標

- ✅ 所有核心模組（models, storage, sandbox_applier, engine）有測試
- ✅ API 端點有基本 smoke test
- ✅ CLI 腳本有參數驗證測試
- ✅ Recommendation 邏輯覆蓋三種情境
- ✅ 錯誤處理有基本測試

## 未來擴充 (Future Enhancements)

- [ ] 更完整的 sandbox 覆寫邏輯測試
- [ ] 更多 edge case 測試（空 universe、極端日期範圍等）
- [ ] Performance 測試（大量報告的載入速度）
- [ ] 整合測試（與實際 PathAEngine 的輕量級整合）

