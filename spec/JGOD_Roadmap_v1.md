# J-GOD 路線圖 v1

**文件版本：** 1.0  
**最後更新：** 2025-01-06  
**目標讀者：** 專案經理、工程師、決策者

---

## 文件說明

本文檔提供 J-GOD 系統的開發路線圖，包括版本軸線、短期/中期/長期目標，以及 v1.0 必須/應該/可以有的功能列表。

---

## 1. Roadmap 概觀與版本軸線

### 1.1 版本軸線

```
v0.2.0 (目前) → v0.3.x → v0.4.x → v0.5.x → v1.0.0
```

### 1.2 目前階段：v0.4.0 (2025-12-13)

**核心功能：**
- ✅ War Room V2 統一控制中心已實作
- ✅ Decision Layer V1 和 V2 並存（V2 使用 S-Rank 加權）
- ✅ Doctrine V2 版本控制系統已實作
- ✅ War Room V2 Dashboard 前端已實作
- ✅ 預測時間軸端點（timeline）已實作
- ✅ 預測穩定性指標（prediction-stability）已實作
- ✅ 前端 API 客戶端 100% 統一（所有 hooks 使用 client.ts）
- ✅ 後端編譯通過（agent-loop safe）
- ✅ Patch lifecycle E2E 完整支援（create → run-sim → approve → deploy → revert）
- ✅ War Room V2 Patch 快速處置 UI（Run Sim / Approve / Reject / Deploy / Revert）
- ⚠️ 部分股票資料不完整（需補齊）

**v0.3.0 新增功能：**
- 預測時間軸 API：`GET /api/v1/predictions/timeline/{symbol}`
- 最新預測 API：`GET /api/v1/predictions/latest/{symbol}`
- 預測穩定性 API：`GET /api/v1/observer/prediction-stability/{symbol}`
- War Room V2 預測穩定性卡片
- CI 快速檢查腳本（`scripts/ci_quick_check.sh`）

**v0.4.0 新增功能：**
- Patch lifecycle API 完整支援（Body 參數統一）
- Patch E2E 合約測試（`tests/test_doctrine_patch_lifecycle_e2e.py`）
- War Room V2 Patch 快速處置按鈕（狀態感知）
- 治理瓶頸計算更新（pending_review + pending_simulation）
- 前端 hooks 100% 遷移至統一 API 客戶端

**v0.5.0-B1 新增功能：**
- S-Rank Engine V2 推薦系統（rule-based，可擴充）
- 策略推薦 API：`GET /api/v1/s-rank-v2/recommendation/{symbol}`
- JSONL 儲存快照（`data/s_rank_v2/recommendations.jsonl`）
- War Room V2 S-Rank Recommendation Card

**v0.5.1-B2 新增功能：**
- Strategy Performance Feed（deterministic evaluator，純 Python）
- 績效驅動推薦模式（mode=performance，預設）
- 績效指標：sharpe_proxy, max_drawdown_proxy, turnover_proxy, decay_slope
- 績效 API：`GET /api/v1/strategy-perf/latest/{symbol}`, `POST /api/v1/strategy-perf/recompute/{symbol}`
- War Room V2 S-Rank Recommendation Card 升級（顯示績效指標 + Recompute Perf 按鈕）

**v0.6.0-A1 新增功能：**
- Decision Engine V3（Rule-based × S-Rank V2 × Performance Feed）
- 決策 API：`GET /api/v1/decision-v3/decide/{symbol}?mode=performance`
- 風險管理：自動計算 position_scale 與 risk_state（RISK_ON / CAUTION / RISK_OFF）
- 決策信心度：基於穩定性與策略權重計算 confidence（0.0 ~ 1.0）
- 決策說明：自動生成繁中決策摘要
- War Room V2 DecisionV3Card（顯示主要策略、風險狀態、信心度、決策理由）

**v0.6.1-A2 新增功能：**
- Decision V3 Snapshot Storage（JSONL append-only）
- 決策快照 API：`POST /api/v1/decision-v3/recompute/{symbol}`, `GET /api/v1/decision-v3/latest/{symbol}`, `GET /api/v1/decision-v3/list/{symbol}`
- War Room V2 DecisionV3Card 升級（顯示快照歷史 + Recompute 按鈕）

**v0.6.2-A3 新增功能：**
- Decision V3 Evaluation Loop（Self-Compare / Self-Evolve）
- 評估指標：hit_rate_proxy, avg_return_proxy, max_drawdown_proxy, turnover_proxy, decision_consistency
- Verdict：IMPROVED / NEUTRAL / REGRESSED / NO_DATA
- 評估 API：`POST /api/v1/decision-v3/eval/recompute/{symbol}`, `GET /api/v1/decision-v3/eval/latest/{symbol}`, `GET /api/v1/decision-v3/eval/list/{symbol}`
- War Room V2 DecisionV3Card 升級（Evaluation 區塊：verdict badge + metrics grid + recommendation）

**v0.6.3-A4 新增功能：**
- Decision V3 Compare vs Baseline（對照評估）
- Baseline 定義：固定 risk_state="CAUTION", position_scale=0.50, primary_strategy="momentum", confidence=0.50
- Winner 判定：V3 / BASELINE / TIE / NO_DATA（使用 composite score）
- Delta metrics：每個指標的差值（v3 - baseline）
- 對照 API：`POST /api/v1/decision-v3/compare/recompute/{symbol}`, `GET /api/v1/decision-v3/compare/latest/{symbol}`, `GET /api/v1/decision-v3/compare/list/{symbol}`
- War Room V2 DecisionV3Card 升級（Compare 區塊：winner badge + delta metrics grid + summary + next step）

**主要限制：**
- 僅支援模擬模式（DRY_RUN / PAPER）
- 資料完整性待補齊
- 部分 Path 引擎未完成
- Patch 操作者 ID 目前硬編碼（未來需整合認證）

---

## 2. 後端 Roadmap

### 2.1 短期（1-3 個月）：v0.2.x → v0.3.x

#### 2.1.1 Decision V2 完整整合
- **目標**：將 S-Rank Engine 完全整合到 Decision V2
- **任務**：
  - 完善 Final Score V2 的計算邏輯
  - 整合 S-Rank 加權機制
  - 淘汰 Decision V1（或保留作為 fallback）
- **預期成果**：Decision Layer 統一使用 V2

#### 2.1.2 Doctrine V2 完善
- **目標**：完善 Doctrine 系統的審核與部署流程
- **任務**：
  - 完善 Patch 審核流程
  - 實作 Self-Repair Engine 的自動提案機制
  - 整合 Doctrine Alert 到 Observer
- **預期成果**：Doctrine 系統可自動修復與審核

#### 2.1.3 資料完整性
- **目標**：補齊所有股票的完整資料
- **任務**：
  - 補齊所有股票的 predictions（目前 1301, 1303, 2308, 2412 缺少）
  - 擴充 universe 到 50 檔（tw_top50_2024.yaml）
  - 優化資料回填腳本（支援批次處理、錯誤重試）
- **預期成果**：所有 universe 股票有完整的歷史資料

#### 2.1.4 War Room Backend V6 整合
- **目標**：完成 FastAPI + WebSocket 後端
- **任務**：
  - 完成 WebSocket 實作
  - 整合到正式 War Room UI
  - 實作即時更新機制
- **預期成果**：War Room 支援即時更新

---

### 2.2 中期（3-6 個月）：v0.3.x → v0.4.x

#### 2.2.1 Path 引擎統一
- **目標**：統一 Path A/B/C/D/E 的介面與實作
- **任務**：
  - 建立統一的 Strategy Interface
  - 統一 Path A/B/C/D/E 的介面
  - 實作 Path 選擇器（根據市場條件自動選擇最佳 Path）
  - 完善各 Path 的策略邏輯
- **預期成果**：所有 Path 使用統一介面，可動態切換

#### 2.2.2 回測系統增強
- **目標**：增強回測功能與績效分析
- **任務**：
  - 實作 Walk-Forward 分析
  - 加入更多績效指標（Calmar Ratio, Sortino Ratio, Information Ratio 等）
  - 實作回測報告視覺化（圖表、表格）
  - 優化回測性能（並行處理）
- **預期成果**：回測系統功能完整，支援進階分析

#### 2.2.3 Observer 系統完善
- **目標**：完善系統監控與告警機制
- **任務**：
  - 實作即時監控儀表板
  - 加入異常自動告警（Telegram/Email）
  - 整合到 War Room V2
  - 實作系統健康度評分
- **預期成果**：系統可自動監控與告警

#### 2.2.4 知識庫擴充
- **目標**：擴充知識庫與自動化知識提取
- **任務**：
  - 自動從交易記錄中提取知識
  - 實作知識品質評分機制
  - 建立知識審核工作流
  - 整合到 Doctrine 系統
- **預期成果**：知識庫可自動擴充與更新

---

### 2.3 長期（6-12 個月）：v0.4.x → v1.0.0

#### 2.3.1 實盤交易準備
- **目標**：準備實盤交易功能（不實際啟用）
- **任務**：
  - 實作實盤券商 API 整合（可能透過 VirtualBroker 抽象層）
  - 加入實盤風險控制機制（更嚴格的限制）
  - 實作交易日誌和審計系統
  - 實作實盤/模擬模式切換
- **預期成果**：系統具備實盤交易能力（但保持模擬模式）

#### 2.3.2 機器學習整合
- **目標**：整合 ML 模型到預測引擎
- **任務**：
  - 實作 ML 模型訓練管道
  - 整合 ML 預測到 Prediction Engine
  - 實作模型版本管理
  - 實作模型 A/B 測試
- **預期成果**：系統支援 ML 預測與規則預測混合

#### 2.3.3 多市場支援
- **目標**：擴充到多個市場
- **任務**：
  - 擴充到美股市場（yfinance 整合）
  - 實作跨市場套利策略
  - 加入外匯、期貨市場（可選）
  - 實作市場切換機制
- **預期成果**：系統支援多市場交易

---

## 3. 前端 Roadmap

### 3.1 短期（1-3 個月）：v0.2.x → v0.3.x

#### 3.1.1 War Room V2 完善
- **目標**：完成所有 War Room V2 組件與功能
- **任務**：
  - 完成所有 War Room V2 組件
  - 實作即時更新（WebSocket）
  - 加入互動式圖表
  - 優化 UI/UX
- **預期成果**：War Room V2 功能完整

#### 3.1.2 Dashboard 增強
- **目標**：增強 Dashboard 功能與視覺化
- **任務**：
  - 加入 K-line 圖表（可能使用 TradingView 或自訂）
  - 實作訂單下單介面（模擬模式）
  - 加入更多視覺化面板
  - 優化響應式設計
- **預期成果**：Dashboard 功能完整，視覺化豐富

#### 3.1.3 Doctrine 管理介面
- **目標**：完善 DMC（Doctrine Management Console）
- **任務**：
  - 完善 DMC 所有頁面
  - 實作 Patch 審核工作流 UI
  - 加入版本比較視覺化
  - 實作 Doctrine 搜尋與過濾
- **預期成果**：DMC 功能完整，易於使用

---

### 3.2 中期（3-6 個月）：v0.3.x → v0.4.x

#### 3.2.1 即時監控儀表板
- **目標**：實作 Observer 即時監控 UI
- **任務**：
  - 實作 Observer 即時監控 UI
  - 加入系統健康度儀表板
  - 實作錯誤追蹤和重播 UI
  - 實作告警通知 UI
- **預期成果**：系統監控 UI 完整

#### 3.2.2 回測視覺化
- **目標**：實作回測結果視覺化
- **任務**：
  - 實作回測結果視覺化（圖表、表格）
  - 加入績效指標圖表
  - 實作策略比較工具
  - 實作回測報告下載
- **預期成果**：回測結果可視覺化分析

#### 3.2.3 移動端適配
- **目標**：優化移動端體驗
- **任務**：
  - 響應式設計優化
  - 可能實作 PWA（Progressive Web App）
  - 優化觸控操作
- **預期成果**：系統可在移動端使用

---

### 3.3 長期（6-12 個月）：v0.4.x → v1.0.0

#### 3.3.1 多使用者支援
- **目標**：實作多使用者與權限管理
- **任務**：
  - 實作使用者認證和授權
  - 加入角色權限管理
  - 實作多租戶架構
  - 實作用戶設定與偏好
- **預期成果**：系統支援多使用者

#### 3.3.2 協作功能
- **目標**：實作團隊協作功能
- **任務**：
  - 實作團隊協作功能
  - 加入評論和註解系統
  - 實作知識分享機制
  - 實作協作工作流
- **預期成果**：系統支援團隊協作

---

## 4. v1.0 必須/應該/可以有功能列表

### 4.1 必須有（Must Have）

#### 4.1.1 完整的資料回填
- ✅ 所有 universe 股票的完整資料
- ✅ 至少 1 年的歷史資料
- ✅ 資料完整性驗證機制

#### 4.1.2 穩定的 API
- ✅ 所有 API 端點都有完整的錯誤處理
- ✅ API 文件（Swagger/OpenAPI）
- ✅ API 版本管理（v1, v2）
- ✅ API 測試覆蓋

#### 4.1.3 基本的前端功能
- ✅ Dashboard 完整功能
- ✅ War Room V2 基本功能
- ✅ Doctrine 管理介面（DMC）
- ✅ 響應式設計

---

### 4.2 應該有（Should Have）

#### 4.2.1 測試覆蓋
- ⚠️ 關鍵路徑的單元測試（目標：> 70%）
- ⚠️ API 整合測試
- ⚠️ 前端組件測試

#### 4.2.2 監控和日誌
- ⚠️ 統一的日誌系統
- ⚠️ 錯誤追蹤系統
- ⚠️ 性能監控

#### 4.2.3 文件
- ✅ API 文件（Swagger）
- ✅ 架構文件（本文檔集）
- ⚠️ 使用者手冊

---

### 4.3 可以有（Nice to Have）

#### 4.3.1 進階視覺化
- 互動式圖表（3D 視覺化）
- 自訂儀表板
- 進階圖表類型

#### 4.3.2 自動化
- CI/CD 管道
- 自動化測試
- 自動化部署

---

## 5. 風險與前置條件

### 5.1 需要先補的資料

#### 5.1.1 股票資料完整性
- **問題**：部分股票（1301, 1303, 2308, 2412）缺少 predictions
- **影響**：影響分析準確性
- **解決方案**：執行完整的資料回填腳本

#### 5.1.2 Universe 擴充
- **問題**：目前只有 8 檔股票，目標是 50 檔
- **影響**：分析範圍受限
- **解決方案**：擴充 universe 到 tw_top50_2024.yaml

---

### 5.2 需要先清的技術債

#### 5.2.1 版本統一
- **問題**：Decision V1/V2、Doctrine V1/V2 並存
- **影響**：維護成本高、行為不一致
- **解決方案**：建立版本遷移計劃，逐步淘汰舊版本

#### 5.2.2 模組依賴優化
- **問題**：某些模組依賴關係複雜
- **影響**：測試困難、循環依賴風險
- **解決方案**：引入依賴注入框架，明確模組邊界

#### 5.2.3 資料庫模型統一
- **問題**：`PredictionSnapshot` 有向後兼容欄位
- **影響**：資料不一致、查詢邏輯混亂
- **解決方案**：執行資料遷移，統一欄位命名

---

### 5.3 需要先完善的基礎設施

#### 5.3.1 錯誤處理統一
- **問題**：各模組錯誤處理方式不一致
- **影響**：錯誤追蹤困難
- **解決方案**：建立統一的錯誤處理中間件

#### 5.3.2 配置管理統一
- **問題**：配置檔案分散在多處
- **影響**：配置不一致、難以管理
- **解決方案**：統一配置管理系統

#### 5.3.3 測試基礎設施
- **問題**：測試覆蓋率可能不足
- **影響**：重構時容易引入回歸錯誤
- **解決方案**：建立測試基礎設施，增加測試覆蓋

---

## 6. 里程碑時間表

### 6.1 v0.3.0（3 個月後）

**目標：** Decision V2 完整整合 + 資料完整性

**關鍵成果：**
- Decision Layer 統一使用 V2
- 所有 universe 股票有完整資料
- War Room Backend V6 整合完成

---

### 6.2 v0.4.0（6 個月後）

**目標：** Path 引擎統一 + 回測系統增強

**關鍵成果：**
- 所有 Path 使用統一介面
- 回測系統功能完整
- Observer 系統完善

---

### 6.3 v1.0.0（12 個月後）

**目標：** 實盤交易準備 + 多市場支援

**關鍵成果：**
- 系統具備實盤交易能力（但保持模擬模式）
- 支援多市場交易
- ML 整合完成

---

## 7. 相關文件

- [系統藍圖](./JGOD_System_Blueprint_v1.md) - 系統總覽
- [後端模組地圖](./JGOD_Backend_Module_Map_v1.md) - 後端模組說明
- [架構風險與治理](./JGOD_Architecture_Risks_and_Governance_v1.md) - 技術債務與改進建議

---

**文件結束**

