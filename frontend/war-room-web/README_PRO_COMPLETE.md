# J-GOD War Room Frontend v6.0 PRO - 完整規格實作

## 🎯 系統目標

世界級交易戰情室（Trading War Room）前端介面，支援：
- FastAPI v6 WebSocket 即時串流事件
- 多 AI role 卡片並行更新
- Bloomberg × Military UIUX 效果
- 型號 v6（Engine v6 + Backend v6 + Frontend v6）

## 📁 完整檔案結構

```
frontend/war-room-web/
├── app/
│   ├── layout.tsx                    # Root Layout（含主題初始化）
│   ├── page.tsx                      # 主頁面（使用 WarRoomLayoutPro）
│   └── demo/
│       └── tsmc/
│           └── page.tsx              # Demo 頁面（自動執行）
├── components/
│   ├── pro/                          # PRO 組件
│   │   ├── CommandPanelPro.tsx      # 專業指揮面板
│   │   ├── RoleCardPro.tsx          # Bloomberg 風格角色卡片
│   │   ├── SummaryCardPro.tsx       # Mission Summary 卡片
│   │   ├── TimelinePro.tsx         # 專業時間軸
│   │   └── __init__.ts
│   ├── common/                       # 通用組件
│   │   ├── Badge.tsx
│   │   ├── ProviderTag.tsx
│   │   ├── ProviderIndicator.tsx    # Provider 指示燈
│   │   ├── LoadingDots.tsx
│   │   ├── ThemeToggle.tsx          # 主題切換
│   │   └── ThemeScript.tsx          # 主題初始化
│   ├── controls/                     # 控制組件（已升級）
│   │   ├── ModeSelector.tsx
│   │   ├── ProviderSelector.tsx
│   │   ├── StockInput.tsx
│   │   ├── PromptInput.tsx
│   │   └── ControlPanel.tsx
│   ├── war-room/                     # 戰情室組件
│   │   ├── RoleCard.tsx
│   │   ├── RoleGrid.tsx             # 使用 RoleCardPro
│   │   ├── StatusBar.tsx
│   │   ├── EventTimeline.tsx
│   │   └── MissionSummary.tsx
│   └── layout/
│       ├── WarRoomLayout.tsx
│       └── WarRoomLayoutPro.tsx     # PRO 版 Layout
├── lib/
│   ├── types/
│   │   └── warRoom.ts               # Type 定義
│   ├── ws/
│   │   ├── warRoomClient.ts        # 基礎版
│   │   └── warRoomClientPro.ts     # PRO 版（心跳包、自動重連）
│   └── theme.ts                     # 主題管理
├── styles/
│   └── globals.css                  # 深度客製化樣式
├── tailwind.config.ts               # PRO 色系 + 動畫
├── package.json                     # Next.js 15 + React 19
├── tsconfig.json
├── next.config.js
├── postcss.config.js
├── .env.local                        # 環境變數
└── README_PRO_COMPLETE.md           # 本文檔
```

## 🚀 啟動方式

### 1. 安裝依賴

```bash
cd /Users/kevincheng/JarvisV1/frontend/war-room-web
npm install
```

### 2. 設定環境變數

`.env.local` 已建立，包含：
```env
NEXT_PUBLIC_WAR_ROOM_BACKEND_URL=http://localhost:8081
NEXT_PUBLIC_WAR_ROOM_ENV=development
NEXT_PUBLIC_WAR_ROOM_TITLE="J-GOD AI 戰情室 v6"
NEXT_PUBLIC_WAR_ROOM_THEME="dark"
```

### 3. 啟動開發伺服器

```bash
npm run dev
```

前端將在 `http://localhost:3000` 啟動。

### 4. 啟動後端（另一個終端）

```bash
cd /Users/kevincheng/JarvisV1
uvicorn jgod.war_room_backend_v6.main:app --host 0.0.0.0 --port 8081 --reload
```

## 🎨 視覺設計

### 色系（Bloomberg × Military）

- **Ultra Dark**: `#0C0F11` - 背景色
- **Titanium**: `#1A1F24` - 卡片背景
- **AI Blue**: `#0099FF` - 主要強調色
- **Military Green**: `#00FFBF` - 成功/完成色
- **Command Red**: `#FF4D4D` - 錯誤/警告色
- **Metal Gold**: `#D2B48C` - 高級/總結色

### 動畫效果

- **Glow**: 發光邊框效果
- **Pulse Border**: 脈衝邊框動畫
- **Typing**: 打字機效果
- **Shimmer**: 閃爍動畫
- **Framer Motion**: 過渡動畫

## 🔌 WebSocket 客戶端 PRO

### 功能

- ✅ 自動重連（最多 3 次，每次間隔 3 秒）
- ✅ 心跳包（每 20 秒）
- ✅ 狀態管理（disconnected / connecting / connected / reconnecting）
- ✅ 狀態變更回調

### 使用方式

```typescript
import { WarRoomWebSocketClientPro, createSession } from "@/lib/ws/warRoomClientPro";

const client = new WarRoomWebSocketClientPro();

client.onEvent((event) => {
  // 處理事件
});

client.onStatusChange((status) => {
  // 處理狀態變更
});

await client.connect(sessionId, requestData);
```

## 📊 組件說明

### CommandPanelPro

專業指揮面板，包含：
- 金屬開關式模式選擇器
- 多色 Provider 指示燈
- 標籤式股票輸入
- 大型指令輸入區
- 主紅鍵啟動按鈕

### RoleCardPro

Bloomberg Terminal 風格角色卡片：
- Glass Panel 效果
- 漸層標題
- 打字機效果（running 時）
- Markdown 支援（done 時）
- Pulse 邊框動畫（running 時）

### SummaryCardPro

Mission Summary 卡片：
- AI 共識統計
- 市場方向（Long/Short/Neutral）
- 風險等級（1-5）
- 風控建議摘要
- 量化分析摘要
- 策略統整

### TimelinePro

專業事件時間軸：
- Icon 標記
- 時間戳記
- 事件分組（不同顏色）
- 自動滾動

## 🎬 Demo 頁面

訪問 `/demo/tsmc` 可自動執行台積電（2330）分析，適合展示給投資人、董事、朋友。

## 📝 技術棧

- **Next.js 15** (App Router)
- **React 19**
- **TypeScript**
- **Tailwind CSS** (深度客製化)
- **Framer Motion** (動畫)
- **React Markdown** (Markdown 渲染)
- **clsx** (條件樣式)

## ✅ 完成項目

- [x] Next.js 15 / React 19 升級
- [x] 深度客製化 Tailwind 配置
- [x] WebSocket 客戶端 PRO（心跳包、自動重連）
- [x] CommandPanelPro 組件
- [x] RoleCardPro 組件
- [x] SummaryCardPro 組件
- [x] TimelinePro 組件
- [x] WarRoomLayoutPro
- [x] 主頁面升級
- [x] Demo 頁面
- [x] 主題系統（Dark / Ultra Dark）
- [x] 響應式設計（Mobile / Tablet / Desktop）

## 🎯 下一步

- v7 AI Multi-Agent 並行模型
- 策略引擎整合
- 更多動畫效果
- 效能優化

