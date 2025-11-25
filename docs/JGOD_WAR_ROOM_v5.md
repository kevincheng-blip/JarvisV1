# J-GOD War Room v5.0 完整文件

## 概述

J-GOD War Room v5.0 是一個雙軌式戰情室系統，提供兩種使用方式：

1. **Streamlit v4.2**：Pseudo-Live 版本，適合本機快速啟動
2. **FastAPI + WebSocket v5.0**：真正即時串流版本，適合生產環境
3. **Next.js 前端**：專業等級的 Web Console

## 架構說明

### 系統架構

```
JarvisV1/
├── jgod/war_room/              # Streamlit v4.2
│   ├── war_room_app.py        # 主應用
│   ├── providers/              # Provider 模組
│   ├── core/                   # 核心引擎
│   └── utils/                  # 工具模組
│       ├── role_state_manager.py
│       └── pseudo_live.py
│
├── jgod/war_room_backend/      # FastAPI v5.0
│   ├── main.py                 # FastAPI 主程式
│   ├── models.py               # WebSocket 訊息模型
│   ├── websocket_manager.py   # WebSocket 管理器
│   ├── routers/                # API 路由
│   └── engine/                 # 戰情室引擎
│
└── frontend/war-room-web/      # Next.js 前端
    ├── pages/                  # 頁面
    ├── components/              # 組件
    └── lib/                     # 工具函數
```

## PHASE 1: Streamlit v4.2（Pseudo-Live）

### 如何運行

```bash
cd /Users/kevincheng/JarvisV1
streamlit run jgod/war_room/war_room_app.py
```

### 功能特點

- **角色狀態管理**：使用 `role_state_manager.py` 統一管理角色狀態
- **Pseudo-Live 更新**：使用 `pseudo_live.py` 實現類即時更新
- **5 秒內第一句話**：優化 max_tokens 和並行執行
- **專業 UI**：角色卡片、狀態指示器、執行時間

### 模式說明

- **Lite**：快速回應（GPT-4o-mini）
- **Pro**：平衡模式（GPT + Claude）
- **God**：深度分析（全 Provider：GPT / Claude / Gemini / Perplexity）
- **Custom**：自訂模式（手動選擇 Provider）

## PHASE 2: FastAPI + WebSocket v5.0

### 如何運行

```bash
cd /Users/kevincheng/JarvisV1
python -m jgod.war_room_backend.main
```

或使用 uvicorn：

```bash
uvicorn jgod.war_room_backend.main:app --host 0.0.0.0 --port 8000
```

### API 端點

#### REST API

- `GET /health`：健康檢查
- `POST /api/war-room/session`：建立新會話

#### WebSocket

- `GET /ws/war-room/{session_id}`：WebSocket 連線

### WebSocket 訊息格式

#### Session Start

```json
{
  "type": "session_start",
  "session_id": "uuid",
  "mode": "God",
  "enabled_providers": ["gpt", "claude", "gemini", "perplexity"],
  "stock_id": "2330",
  "question": "請分析台積電的投資建議",
  "timestamp": "2025-11-25T09:30:00Z"
}
```

#### Role Chunk

```json
{
  "type": "role_chunk",
  "session_id": "uuid",
  "role": "scout",
  "role_label": "斥候（Scout）",
  "provider": "gemini",
  "chunk": "...新文字...",
  "sequence": 4,
  "is_final": false,
  "timestamp": "2025-11-25T09:30:00Z"
}
```

#### Role Done

```json
{
  "type": "role_done",
  "session_id": "uuid",
  "role": "scout",
  "role_label": "斥候（Scout）",
  "provider": "gemini",
  "success": true,
  "content": "完整內容",
  "execution_time": 3.5,
  "error_message": null,
  "timestamp": "2025-11-25T09:30:00Z"
}
```

#### Summary

```json
{
  "type": "summary",
  "session_id": "uuid",
  "content": "所有角色分析完成",
  "execution_time": 15.2,
  "timestamp": "2025-11-25T09:30:00Z"
}
```

#### Error

```json
{
  "type": "error",
  "session_id": "uuid",
  "error_type": "EXECUTION_ERROR",
  "message": "錯誤訊息",
  "details": {},
  "timestamp": "2025-11-25T09:30:00Z"
}
```

## PHASE 3: Next.js 前端

### 如何運行

```bash
cd frontend/war-room-web
npm install
npm run dev
```

### 功能特點

- **專業 UI**：使用 TailwindCSS + shadcn/ui
- **即時更新**：WebSocket 連線，即時顯示角色輸出
- **模式選擇**：Lite / Pro / God / Custom
- **角色卡片**：六大角色卡片，即時文字串流
- **策略總結**：底部顯示 GPT 最終策略總結

### 前端結構

```
frontend/war-room-web/
├── pages/
│   ├── index.tsx              # 主頁面
│   └── api/                   # API 路由（如果需要）
├── components/
│   ├── RoleCard.tsx           # 角色卡片
│   ├── ControlPanel.tsx      # 控制面板
│   └── SummaryPanel.tsx      # 總結面板
├── lib/
│   ├── websocket.ts           # WebSocket 客戶端
│   └── types.ts               # TypeScript 類型
└── styles/
    └── globals.css            # 全域樣式
```

## PHASE 4: 共用設定

### 環境變數

所有模組共用以下環境變數：

- `OPENAI_API_KEY`：GPT Provider
- `ANTHROPIC_API_KEY`：Claude Provider
- `GEMINI_API_KEY` 或 `GOOGLE_API_KEY`：Gemini Provider
- `PERPLEXITY_API_KEY`：Perplexity Provider
- `WAR_ROOM_API_HOST`：FastAPI 主機（預設：0.0.0.0）
- `WAR_ROOM_API_PORT`：FastAPI 埠號（預設：8000）

### Provider 設定

Provider 設定統一在 `jgod/war_room/core/models.py` 中定義：

- `ROLE_PROVIDER_MAP`：角色到 Provider 的映射
- `MODE_PROVIDER_MAP`：模式到 Provider 列表的映射

## PHASE 5: Logging

### 結構化日誌

所有模組使用 Python `logging` 模組，格式：

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 日誌級別

- `INFO`：一般資訊（角色開始/結束、Provider 啟動）
- `WARNING`：警告（Provider 未初始化、API Key 缺失）
- `ERROR`：錯誤（API 呼叫失敗、執行異常）

### 日誌位置

- Streamlit：終端輸出
- FastAPI：終端輸出 + 可選檔案日誌
- 錯誤日誌：`logs/error/`

## 驗證與測試

### Streamlit v4.2 驗證

1. 啟動 Streamlit
2. 選擇 God 模式
3. 輸入問題並啟動
4. 確認 5 秒內看到第一句話
5. 確認所有 Provider 並行執行

### FastAPI v5.0 驗證

1. 啟動 FastAPI 後端
2. 使用 WebSocket 客戶端連線
3. 發送啟動參數
4. 確認收到即時 chunk 事件
5. 確認所有角色完成事件

### Next.js 前端驗證

1. 啟動前端
2. 連線到 FastAPI 後端
3. 選擇模式並啟動
4. 確認即時顯示角色輸出
5. 確認總結面板顯示

## 故障排除

### Streamlit 無法即時更新

- 檢查 `war_room_running` 狀態
- 確認 `should_autorefresh()` 返回 True
- 檢查角色狀態是否正確更新

### FastAPI WebSocket 連線失敗

- 檢查 CORS 設定
- 確認 WebSocket 端點路徑正確
- 檢查 session_id 是否有效

### Next.js 前端無法連線

- 檢查 `NEXT_PUBLIC_API_URL` 環境變數
- 確認 FastAPI 後端正在運行
- 檢查瀏覽器 Console 錯誤訊息

## 未來改進

- [ ] 加入 Redis 支援多實例部署
- [ ] 加入認證與授權
- [ ] 加入歷史記錄查詢
- [ ] 加入更多 Provider（如 Llama、Mistral）
- [ ] 優化 streaming 效能

## 聯絡與支援

如有問題，請查看：
- 專案 GitHub Issues
- 日誌檔案：`logs/error/`
- 文件：`docs/`

