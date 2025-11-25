# J-GOD Multi-AI War Room v5.0 · 系統設計說明書

## 1. 目的與範圍

本文件說明 J-GOD Multi-AI War Room v5.0 的系統架構與設計原則，作為後續開發、重構與維護的共同依據。

### War Room 的定位：

- 作為 J-GOD 股神作戰系統的 **核心決策中樞**
- 對接多家 LLM Provider（OpenAI / Anthropic / Google Gemini / Perplexity）
- 以「多角色戰情室」的方式，為使用者提供：
  - 個股短線判斷
  - 盤勢分析
  - 風險與部位建議
  - 策略統整與執行建議

### v5.0 將 War Room 分為兩條主軸：

1. **Streamlit War Room v4.2（Pseudo-Live）**
   - 面向：本機開發、研究部內部使用
   - 特性：快速啟動、類即時更新、方便測試引擎與 Provider

2. **Web War Room v5.0（FastAPI + WebSocket + Next.js）**
   - 面向：正式戰情室前台（未來可接入交易系統）
   - 特性：真正即時的多角色聊天室式 UI、多使用者、多端接入

上述兩者共用同一顆 Core War Room Engine，以避免邏輯分裂與行為不一致。

## 2. 整體架構概觀

J-GOD War Room v5.0 由三層組成：

### Core Engine 層（共用邏輯）

- Provider Manager（多 AI Provider 管理）
- War Room Engine（多角色決策流程）
- 既有：Prediction Engine / Feature Builder / Risk Engine 等

### Transport 層

- Streamlit App（本機 UI，Pseudo-Live 版本）
- FastAPI Backend（REST + WebSocket API）

### UI 層

- Streamlit War Room 畫面（開發 / 研究用途）
- Next.js + Tailwind Web Console（正式多 AI 戰情室前台）

**目標是：所有「戰情邏輯」集中於 Core Engine，UI 與 Transport 僅作為呈現與輸入介面。**

## 3. 核心引擎層（Core Engine Layer）

### 3.1 角色與 Provider Mapping

War Room 採用「多角色委員會」模式，每個角色固定對應一個預設 Provider。

角色設定建議集中管理，例如 `jgod/war_room/config/roles.py` 或 YAML 檔：

**角色列表（範例）：**

- Intel Officer（情報官） → Provider: Perplexity
- Scout（斥候） → Provider: Gemini
- Risk Officer（風控長） → Provider: Claude
- Quant Lead（量化長） → Provider: Claude
- Strategist（策略統整） → Provider: GPT
- Execution Officer（執行官） → Provider: GPT

**模式（Mode）定義：**

- Lite：僅啟用 GPT
- Pro：啟用 GPT + Claude
- God：啟用 GPT + Claude + Gemini + Perplexity
- Custom：使用者自訂要啟用的 Provider

角色與 Provider 的對應、各模式啟用 Provider 清單，皆應集中於單一設定模組，供 Streamlit 與 FastAPI 共用。

### 3.2 Provider Manager

Provider Manager 負責將各家 API 的細節封裝成統一介面，職責包含：

- 管理 Provider 初始化（API Key、Model Name、Timeout、max_tokens 等）
- 對外提供統一的 async 呼叫介面，例如：

```python
async def ask_role(
    role_name: str,
    provider_key: str,
    prompt: str,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> str:
    ...
```

**支援 Provider：**

- GPT（OpenAI Chat Completions）
- Claude（Anthropic Messages API）
- Gemini（Google Generative AI）
- Perplexity Sonar（搜尋型 LLM）

**Provider Manager 應具備：**

- 統一錯誤處理（API Key 缺失、網路錯誤、Rate Limit）
- 統一 logging（包含 Provider 名稱、耗時、token 使用量等）
- 可擴充性（未來新增 Provider 時不影響 War Room Engine 對外介面）

### 3.3 War Room Engine（多角色決策流程）

War Room Engine 是系統的決策核心，負責：

1. **接收使用者輸入的分析需求：**
   - 股票代碼列表（tickers）
   - 日期範圍（date_range）
   - 問題（question）
   - 模式（mode：Lite / Pro / God / Custom）
   - 自訂啟用 Provider 清單（enabled_providers，僅 Custom 模式使用）

2. **準備分析 Context：**
   - 近期股價 / K 線資料（可透過 Prediction / Market 模組）
   - 預測 Engine 的輸出（例如明日上漲機率最高前 N 檔）
   - 風控 / 部位資訊（由 Risk Engine 提供）

3. **根據角色設定與模式，決定每個角色應使用之 Provider，並啟動多角色協同流程。**

#### 3.3.1 批次模式（Batch Mode）

適用於非串流 UI，或僅需一次性總結的場景。

回傳結構化資料，例如：

```python
async def run_war_room_batch(params: WarRoomParams) -> Dict[str, RoleResult]:
    # key: role_name
    # value: provider, full_text, timing, etc.
```

#### 3.3.2 串流模式（Streaming / Event Mode）

適用於 WebSocket 與 Streamlit Pseudo-Live。

回傳 async iterator，逐步產出事件：

```python
async def run_war_room(
    self,
    params: WarRoomParams,
) -> AsyncIterator[WarRoomEvent]:
    # yield SessionStart
    # yield RoleChunk / RoleDone / Summary / Error
```

**WarRoomEvent 的類型範例：**

- session_start
- role_chunk
- role_done
- summary
- error

每個事件應包含：session_id、role、provider、mode、時間戳記等欄位，方便前端 UI 正確更新狀態。

## 4. Transport 層 A：Streamlit War Room v4.2（Pseudo-Live）

### 4.1 角色定位

Streamlit War Room 的定位為：

- 本機執行、單使用者、快速啟動
- 用於：
  - 測試 Provider API 是否正常
  - 驗證 War Room Engine 行為
  - 小規模實戰盤前 / 盤後研究

### 4.2 狀態管理（session_state 結構）

在 `st.session_state` 中，建議維持統一結構：

**war_room_roles**：儲存每個角色的狀態與內容

```python
{
    "Intel Officer": {
        "role_key": "intel_officer",
        "provider": "perplexity",
        "status": "pending" | "running" | "done" | "error",
        "content": str,
        "error_message": Optional[str],
        "started_at": Optional[datetime],
        "finished_at": Optional[datetime],
    },
    ...
}
```

**war_room_running**：布林值，表示目前是否有戰情室執行中

### 4.3 Pseudo-Live 更新機制

由於 Streamlit 本身是同步重新執行整個 script，因此：

- 真正的「逐字更新」無法直接達成
- 可透過以下策略達成「類即時更新」：

**當使用者按下「開始戰情室」按鈕：**

1. 初始化 `war_room_roles` 狀態（全部設為 pending）
2. 設定 `war_room_running = True`
3. 以非阻塞方式啟動 War Room Engine（async 背景執行）
4. callback 負責寫入 `session_state["war_room_roles"][role]["content"]`

**在 Streamlit 主程式中：**

1. 若 `war_room_running` 為 True，使用 `st_autorefresh()`（或類似機制）每 500–800ms 觸發頁面重繪
2. 每次重新執行時，根據最新的 `war_room_roles` 內容，更新 UI 上各角色卡片

**當 Engine 完成所有角色：**

1. 將 `war_room_running = False`
2. 停止自動刷新
3. 顯示該輪戰情室總耗時

### 4.4 UI 設計原則

Streamlit War Room 的 UI 應遵循：

- 各角色以卡片形式平行排列，每一張卡片包含：
  - 角色名稱（例如：「情報官（Intel Officer）」）
  - Provider Badge（GPT / Claude / Gemini / Perplexity）
  - 狀態指示（待機 / 執行中 / 完成 / 錯誤）
  - 累積文字內容（戰情發言）

- 頂部區域提供：
  - 模式切換（Lite / Pro / God / Custom）
  - 啟用 Provider 清單摘要
  - 啟動 / 重設按鈕

**目標體驗：**

- 在 God 模式下，使用者應在約 3–6 秒內看到第一個角色輸出
- 所有 Provider 並行執行，不可串行阻塞造成 20–30 秒後才一次全部出現

## 5. Transport 層 B：FastAPI + WebSocket War Room Backend v5.0

### 5.1 目錄結構建議

於專案中新增後端模組，例如：

```
jgod/war_room_backend/
  ├── __init__.py
  ├── main.py                # FastAPI app entry
  ├── config.py              # 環境變數、設定
  ├── models.py              # Pydantic 模型（請求、事件）
  ├── websocket_manager.py   # WebSocket 連線管理
  ├── routers/
  │     └── war_room.py      # 戰情室相關路由
  ├── engine/
  │     ├── war_room_engine.py           # 對 Core Engine 的包裝
  │     └── provider_manager_adapter.py  # provider manager 的 adapter
  └── logging_utils.py       # 統一 logging 設定
```

### 5.2 API 設計

後端應至少提供：

**健康檢查端點**

```
GET /health → { "status": "ok", "version": "5.0.0" }
```

**建立 War Room Session**

```
POST /api/war-room/session
```

輸入：
- 股票代碼、日期範圍、問題、模式、Provider 選擇等

輸出：
- session_id（例如 UUID）
- session 基本資訊

**War Room WebSocket**

```
GET /ws/war-room/{session_id}
```

建立即時串流連線，傳送 War Room 事件流（見下）

### 5.3 WebSocket 事件格式

事件型別（type）包含：

- session_start
- role_chunk
- role_done
- summary
- error

**role_chunk 範例：**

```json
{
  "type": "role_chunk",
  "session_id": "uuid-1234",
  "role": "scout",
  "role_label": "斥候（Scout）",
  "provider": "gemini",
  "mode": "god",
  "chunk": "這是新的一段分析文字…",
  "sequence": 3,
  "is_final": false,
  "timestamp": "2025-11-25T09:24:00Z"
}
```

**summary 事件**則提供戰情室最終統整結果（通常由 Strategist 角色提供）。

所有事件應以 Pydantic models 統一管理，確保前後端 schema 一致。

## 6. UI 層：Next.js + Tailwind War Room Console v5.0

### 6.1 前端框架

前端建議位於：

```
frontend/war-room-web/
```

**採用技術：**

- Next.js（React + TypeScript）
- Tailwind CSS
- shadcn/ui（元件庫：Card / Button / Tabs / Badge 等）

### 6.2 畫面佈局

前端 UI 應以「交易室控制台」為設計概念，分為：

**Top Bar**

- 顯示系統名稱：J-GOD Multi-AI War Room
- 模式選擇器：Lite / Pro / God / Custom
- 當前 Session 狀態指示（Idle / Running / Completed / Error）

**左側控制面板**

- 股票代碼輸入（支援多檔）
- 日期範圍選擇
- 問題輸入（支援中文）
- Provider 勾選（自訂模式用）
- Run / Stop 按鈕

**右側多角色戰情網格**

2x3 或 3x2 卡片網格，包含：

- 情報官（Intel Officer · Perplexity）
- 斥候（Scout · Gemini）
- 風控長（Risk Officer · Claude）
- 量化長（Quant Lead · Claude）
- 策略統整（Strategist · GPT）
- 執行官（Execution Officer · GPT）

每張卡片顯示：

- 角色名稱（中英）
- Provider Badge
- 狀態（Pending / Running / Done / Error）
- 即時文字內容（隨事件 append）

**底部總結區**

顯示 Strategist 的最終總結：

- 當日盤勢結論
- 明日偏多 / 偏空判斷
- 關鍵個股與風險提示

### 6.3 WebSocket 客戶端行為

前端流程：

1. **使用者點擊 Run：**
   - 呼叫 `POST /api/war-room/session` → 取得 session_id
   - 建立 WebSocket 連線：`/ws/war-room/{session_id}`

2. **接收事件：**
   - session_start：初始化畫面與狀態
   - role_chunk：將 chunk append 至對應角色卡片內容
   - role_done：更新角色狀態為完成
   - summary：填入底部總結區
   - error：顯示錯誤提示

前端應以 React state（例如 `WarRoomState`）維護：

- sessionId
- mode
- roles（每一角色的內容與狀態）
- summary
- error

## 7. 設定管理與共用邏輯

### 7.1 共用設定

Provider 與角色相關設定應集中管理，避免 Streamlit / FastAPI / 前端各自定義。建議：

- 建立 `jgod/war_room/config` 模組
- 角色 – Provider 對應表
- Mode – Provider 啟用清單
- 預設 Prompt 範本、語氣風格可一併集中

### 7.2 環境變數與密鑰

所有 Provider 所需的 API Key、FinMind Token 等，不應散落於程式中。建議使用共用 env loader（例如 `jgod.config.env_loader`）統一處理。

## 8. Logging、錯誤處理與文件

### 8.1 Logging

**後端（FastAPI / Engine）建議採用結構化 logging：**

- Logger name：war_room_backend、war_room_engine、provider_manager 等
- 重要紀錄：
  - Session 啟動 / 結束
  - 啟用 Provider 清單
  - 每角色耗時
  - API 錯誤 / Rate Limit / Exception

**Streamlit 部分：**

- 避免大量重複 log（特別是在自動刷新情況）
- 把真正 Debug 用 log 與使用者提示分開處理

### 8.2 文件

本文件可作為 `docs/JGOD_WAR_ROOM_v5.md` 的基礎版本，後續依實作結果補充：

- 實際啟動指令：
  - `python -m streamlit run jgod/war_room/war_room_app.py`
  - `uvicorn jgod.war_room_backend.main:app --reload`
  - `npm run dev`（前端）
- 各模式（Lite / Pro / God / Custom）差異說明
- 實際輸出範例（可另建一份 `docs/examples/` 存放）

## 9. 總結

J-GOD Multi-AI War Room v5.0 目標是：

- 以 **單一 Core Engine** 串起所有戰情邏輯
- 對內提供 Streamlit Pseudo-Live 版本，方便快速驗證與研究
- 對外提供 FastAPI + WebSocket + Next.js 的真正即時戰情前台
- 多 Provider 並行執行、角色分工清楚、輸出風格一致
- 架構清晰、模組邊界明確，便於未來加入：
  - 盤勢總覽 Dashboard
  - 策略生成器
  - 策略回測系統（Backtest Engine）
  - 自動交易 Execution Engine

本說明書的目的，是讓之後任何接手 J-GOD 專案的開發者，在未閱讀全部程式碼的情況下，也能理解整個 War Room 的設計脈絡與擴充方向。

