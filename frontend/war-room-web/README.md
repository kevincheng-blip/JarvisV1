# J-GOD War Room Frontend v6.0

Next.js + TypeScript + Tailwind CSS 前端，串接 FastAPI WebSocket v6 後端。

## 安裝與啟動

### 1. 安裝依賴

```bash
cd frontend/war-room-web
npm install
```

### 2. 設定環境變數

複製 `.env.local.example` 為 `.env.local`：

```bash
cp .env.local.example .env.local
```

編輯 `.env.local`，設定後端 URL（預設為 `http://localhost:8081`）：

```env
NEXT_PUBLIC_WAR_ROOM_BACKEND_URL=http://localhost:8081
```

### 3. 啟動開發伺服器

```bash
npm run dev
```

前端將在 `http://localhost:3000` 啟動。

## 專案結構

```
frontend/war-room-web/
├── app/
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # 主頁面（War Room）
├── components/
│   ├── common/             # 通用組件
│   │   ├── Badge.tsx
│   │   ├── LoadingDots.tsx
│   │   └── ProviderTag.tsx
│   ├── controls/           # 控制面板組件
│   │   ├── ControlPanel.tsx
│   │   ├── ModeSelector.tsx
│   │   ├── ProviderSelector.tsx
│   │   ├── PromptInput.tsx
│   │   └── StockInput.tsx
│   ├── layout/
│   │   └── WarRoomLayout.tsx
│   └── war-room/           # 戰情室組件
│       ├── EventTimeline.tsx
│       ├── RoleCard.tsx
│       ├── RoleGrid.tsx
│       └── StatusBar.tsx
├── lib/
│   ├── types/
│   │   └── warRoom.ts      # Type 定義
│   └── ws/
│       └── warRoomClient.ts # WebSocket 客戶端
└── styles/
    └── globals.css         # 全域樣式
```

## 功能特點

- ✅ 深色系 UI（Trading War Room 風格）
- ✅ 即時 WebSocket 串流
- ✅ 多角色並行顯示
- ✅ 事件時間軸
- ✅ God / Custom 模式切換
- ✅ 多 Provider 選擇（GPT, Claude, Gemini, Perplexity）
- ✅ 多股票輸入
- ✅ 即時狀態更新

## WebSocket URL 設定

WebSocket URL 透過環境變數 `NEXT_PUBLIC_WAR_ROOM_BACKEND_URL` 設定，預設為：

```
http://localhost:8081
```

WebSocket 連線會自動轉換為 `ws://localhost:8081` 或 `wss://`（如果使用 HTTPS）。

## 使用流程

1. 選擇模式（God / Custom）
2. 選擇 Provider（God 模式自動全選）
3. 輸入股票代碼（例如：2330, 2412）
4. 輸入使用者指令
5. 點擊「啟動 J-GOD 戰情室」
6. 觀察各角色卡片即時更新
7. 查看事件時間軸

## 技術棧

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **React Hooks** (useState, useEffect, useRef, useCallback)

## 開發指令

```bash
# 開發模式
npm run dev

# 建置
npm run build

# 生產模式
npm start

# Lint
npm run lint
```
