# J-GOD Release Notes

## War Room v6 - Phase 1 (2025-11-26)

### 🚀 主要更新

#### 1. Gemini Scout 加速與優化
- 模型升級至 `gemini-2.5-flash`，避免 404 錯誤
- 強制使用 `response_mime_type="text/plain"`，關閉 AFC/tools
- `max_output_tokens` 提升至 2048，確保有足夠 token 產生內容
- Timeout 從 8 秒提升至 15 秒，讓 API 有足夠時間回應
- 實作 fallback 機制，當 fast model 不可用時自動切換

#### 2. 首響時間與總耗時顯示
- 所有角色卡片顯示「首響：X.Xs｜總耗時：X.Xs」
- 使用 `time.perf_counter()` 進行高精度計時
- 後端追蹤並透過 WebSocket 傳遞 timing 資訊
- 前端優先使用後端提供的精確時間

#### 3. 全角色 Timeout Fallback
- 統一 timeout 機制：Scout 15 秒，其他角色 15 秒
- 使用 `asyncio.wait_for` 包裝 provider 呼叫
- Timeout 時返回備援內容，不會讓整個戰情室卡死
- 前端顯示明確的 TIMEOUT 標記

#### 4. 結構化 Mission Summary
- 重寫 summary 生成邏輯，輸出四大結構化段落：
  - Market Overview（市場概況）
  - Technical & Indicators（技術與指標）
  - Capital & Risk（資金與風險）
  - Trading Stance（操作立場）
- 使用 Markdown 格式渲染，內容更清晰有條理

### 📝 技術改進
- 建立 `_build_config()` 方法，兼容不同 SDK 版本
- 統一前後端角色 key 映射，避免不一致
- 改進錯誤處理，記錄詳細 log 但不讓系統崩潰
- 強制最低 `max_tokens = 2048`，確保所有角色有足夠 token

### 🐛 Bug 修復
- 修復 Gemini 404 錯誤，實作自動 fallback
- 修復空內容問題，確保 Scout 能正常顯示文字
- 修復 TypeError: unexpected keyword argument 'tools'
- 修復前後端角色 key 不一致問題

### 📊 實際效果
- Scout 首響時間：3-5 秒
- Scout 總耗時：5-12 秒
- 其他角色正常運作，延遲範圍 2-12 秒
- Timeout 保護確保系統不會卡死

---

## 2025-11-26
- auto-commit: Add new features


- auto-commit: Enhance war room functionality

- auto-commit: Add new features

- auto-commit: Update codebase

- auto-commit: Add new features

## 2025-11-25
- auto-commit: Add auto Git pipeline

- auto-commit: Add auto Git pipeline
- auto-commit: Improve war room core
- auto-commit: Update codebase
- auto-commit: Enhance war room functionality
- auto-commit: Improve war room core
- auto-commit: Enhance war room functionality
- auto-commit: Update codebase
- auto-commit: Improve war room core
- auto-commit: Improve war room core
- auto-commit: Update war room AI
- auto-commit: Enhance war room functionality
- auto-commit: Enhance war room functionality
- auto-commit: Enhance war room functionality
- auto-commit: Enhance war room functionality
- auto-commit: Enhance war room functionality
- auto-commit: Add new features
- auto-commit: Update codebase
- auto-commit: Improve war room core
- auto-commit: Improve war room core
- auto-commit: Enhance war room functionality
- auto-commit: Improve war room core
- auto-commit: Enhance war room functionality
- auto-commit: Add new features
- auto-commit: Update configuration
- auto-commit: Update codebase
- auto-commit: Add new features
- auto-commit: Add new features
- auto-commit: Add new features
- auto-commit: Add new features
- auto-commit: Add new features
- auto-commit: Add new features
- auto-commit: Add new features
- auto-commit: Update codebase
- auto-commit: Update war room AI
- auto-commit: Add new features