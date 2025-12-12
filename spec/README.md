# J-GOD 規格文件索引

**最後更新：** 2025-01-06

---

## 核心規格文件集（v1）

本目錄包含 J-GOD 系統的完整規格文件集，建議按以下順序閱讀：

### 1. [系統藍圖](./JGOD_System_Blueprint_v1.md) ⭐ 必讀

**目標讀者：** 所有人（新進工程師、架構師、AI 助手）

**內容：**
- 系統願景與哲學
- 系統大地圖：六大世界
- 高層級資料流
- 關鍵設計原則
- 關鍵限制
- 版本標記說明

**建議：** 所有新進人員應先閱讀此文件。

---

### 2. [後端模組地圖](./JGOD_Backend_Module_Map_v1.md)

**目標讀者：** 後端工程師、架構師

**內容：**
- 後端總覽
- 核心引擎模組（market, prediction, decision, strategy, risk, execution）
- 知識與治理模組（knowledge, doctrine_v2, doctrine_alert, self_repair）
- 實驗與模擬模組（path_a~e, backtest, rule_sim, decision_ab, policy）
- 觀察與監控模組（observer, diagnostics, error_engine）
- 戰情室與編排模組（council_chamber, war_room backend, orchestrator）
- 資料儲存模組（storage models）
- 模組完整度總覽

---

### 3. [前端架構](./JGOD_Frontend_Architecture_v1.md)

**目標讀者：** 前端工程師、UI/UX 設計師

**內容：**
- 技術棧與專案結構
- 頁面結構（Dashboard, WarRoom, WarRoomV2Dashboard, DMC 等）
- 核心共用組件
- War Room / War Room V2 專用組件
- 狀態管理策略
- API 客戶端與型別
- War Room V2 設計理解
- 未來擴充建議

---

### 4. [API 映射](./JGOD_API_Map_v1.md)

**目標讀者：** 後端工程師、前端工程師、API 使用者

**內容：**
- API 設計原則
- Predictions / Indicators / Universe 區
- Decision / Decision AB Test 區
- Doctrine / Doctrine Patch / Doctrine Alert 區
- Rule Simulation / S-Rank / Observer / Signal Conflict 區
- Error Review / Replay / Self-Repair 區
- Policy / Strategy / Backtest / Orders 區
- 後續計畫

---

### 5. [路線圖](./JGOD_Roadmap_v1.md)

**目標讀者：** 專案經理、工程師、決策者

**內容：**
- Roadmap 概觀與版本軸線
- 後端 Roadmap：短期/中期/長期
- 前端 Roadmap：短期/中期/長期
- v1.0 必須/應該/可以有功能列表
- 風險與前置條件
- 里程碑時間表

---

### 6. [架構風險與治理](./JGOD_Architecture_Risks_and_Governance_v1.md)

**目標讀者：** 架構師、技術主管、資深工程師

**內容：**
- 架構層風險（多版本並存、依賴複雜、資料庫 schema 問題）
- 程式品質風險（錯誤處理、測試覆蓋、config 分散）
- 資料完整性風險（回填、FinMind 節流）
- 前端風險（state 管理、API 錯誤處理、重用性）
- 安全性風險（認證、敏感資訊管理）
- 性能風險（DB 查詢、LLM 成本）
- 架構改進建議（DI、統一 config、事件驅動、API 版本管理）
- 缺失抽象層（DAL, Strategy Interface, Broker Interface）
- 可觀測性與監控建議（logging, metrics, tracing）
- 風險矩陣總結
- 改進計劃建議

---

## 其他規格文件

本目錄還包含其他模組的詳細規格文件：

- `SRank_Engine_V2_Spec.md` - S-Rank Engine V2 推薦系統規格
- `JGOD_System_Architecture_v1.md` - 系統架構詳細說明
- `JGOD_Backfill_and_Simulation_Data_Spec_v1.md` - 資料回填與模擬規格
- `JGOD_Trading_Command_Center_UI_Spec_v1.md` - 交易指揮中心 UI 規格
- `JGOD_PathAEngine_Spec.md` ~ `JGOD_PathEEngine_Spec.md` - 各 Path 引擎規格
- `JGOD_ExecutionEngine_Spec.md` - 執行引擎規格
- `JGOD_DiagnosisEngine_Spec.md` - 診斷引擎規格
- 其他模組規格文件...

---

## 文件維護

- **文件版本：** 所有核心規格文件目前為 v1.0
- **更新頻率：** 當系統架構有重大變更時更新
- **維護者：** 架構師與技術主管

---

**文件索引結束**

