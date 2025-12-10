# Self-Repair Engine Test Suite

本測試套件針對 J-GOD Knowledge Brain v2 – Self-Repair Engine v1.0 進行測試。

## 測試範圍 (Test Scope)

### 單元測試 (Unit Tests)

1. **test_scanner.py** - `SelfRepairScanner`
   - 空列表處理
   - 單一 section 掃描
   - 重複檢測（靜態分析）
   - LLM 啟用/停用模式
   - 衝突檢測
   - 模糊性檢測
   - Issue 結構驗證

2. **test_proposer.py** - `RepairProposer`
   - 空 issues 列表處理
   - 無 LLM 模式
   - 有 LLM 模式
   - Proposal 結構驗證
   - 不同 issue type 的 proposal 生成（CONFLICT, DUPLICATE, AMBIGUOUS, GAP）
   - Issue ID 映射驗證

3. **test_evaluator.py** - `ProposalEvaluator`
   - 空 proposals 列表處理
   - 無 LLM 模式（預設 confidence）
   - 有 LLM 模式（完整評分）
   - 評分範圍驗證（0.0-1.0）
   - 低/高 confidence 處理
   - 原始 proposal 資料保留

4. **test_patcher.py** - `SafePatcher`
   - 初始化測試
   - 自訂路徑
   - 檔案不存在處理
   - 備份建立
   - 有/無備份模式
   - 現有條目保留

5. **test_engine.py** - `SelfRepairEngineV1`
   - 引擎初始化
   - 空 sections 處理
   - 完整分析流程（無 LLM）
   - 完整分析流程（有 LLM）
   - Report 結構驗證
   - Metadata 驗證
   - Proposal-Issue 映射驗證

### API 測試 (API Tests)

6. **test_api_self_repair.py** - API Endpoints
   - `POST /api/v1/knowledge/self-repair/run`
   - `GET /api/v1/knowledge/self-repair/reports`
   - `POST /api/v1/knowledge/self-repair/apply`
   - 錯誤處理

## 測試資料 (Test Data)

測試使用以下 mock 資料：

- `sample_doctrine_sections`: 正常 Doctrine sections
- `sample_conflicting_sections`: 存在衝突的 sections
- `sample_duplicate_sections`: 重複的 sections
- `sample_ambiguous_section`: 模糊定義的 section
- `sample_consistency_issues`: 範例一致性問題
- `sample_fix_proposals`: 範例修復建議
- `mock_llm_provider`: Mock LLM 提供者（返回固定回應）

## 執行測試 (Running Tests)

### 執行所有測試

```bash
# 執行整個測試套件
pytest tests/knowledge_self_repair/

# 執行特定測試檔案
pytest tests/knowledge_self_repair/test_scanner.py

# 執行特定測試類別
pytest tests/knowledge_self_repair/test_scanner.py::TestSelfRepairScanner

# 執行特定測試方法
pytest tests/knowledge_self_repair/test_scanner.py::TestSelfRepairScanner::test_scan_duplicates_static
```

### 執行時顯示詳細輸出

```bash
# 顯示 print 輸出
pytest tests/knowledge_self_repair/ -s

# 顯示詳細測試資訊
pytest tests/knowledge_self_repair/ -v

# 顯示覆蓋率報告
pytest tests/knowledge_self_repair/ --cov=jgod.knowledge.self_repair --cov-report=html
```

### 只執行無 LLM 的測試

```bash
# 跳過需要 LLM 的測試
pytest tests/knowledge_self_repair/ -m "not llm_required"
```

## 測試環境需求 (Requirements)

- Python 3.8+
- pytest
- 可選：pytest-cov（覆蓋率報告）

安裝測試依賴：

```bash
pip install pytest pytest-cov
```

## 測試策略 (Test Strategy)

1. **隔離測試**: 每個模組獨立測試，使用 mock LLM provider
2. **邊界測試**: 測試空列表、單一元素、缺失資料等邊界情況
3. **結構驗證**: 驗證資料結構的完整性和正確性
4. **無 LLM 模式**: 確保在無 LLM 時系統仍能運作（降級模式）
5. **安全性測試**: 驗證備份機制、不自動 commit 等安全特性

## 注意事項 (Notes)

- API 測試 (`test_api_self_repair.py`) 目前為骨架，需配置 FastAPI TestClient
- LLM 相關測試使用 mock provider，不實際呼叫 LLM API
- 某些測試可能需要實際的 Doctrine sections 資料
- 測試不會修改實際的知識庫檔案（使用臨時檔案）

## 未來擴充 (Future Enhancements)

- [ ] 整合測試（end-to-end pipeline）
- [ ] 效能測試（大量 sections 的掃描時間）
- [ ] LLM 回應解析的邊界案例測試
- [ ] 錯誤恢復測試
- [ ] 並行執行測試

