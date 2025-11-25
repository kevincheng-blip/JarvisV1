# J-GOD War Room Frontend v6.0 PRO - 啟動指南

## ✅ 完成狀態

**所有組件、頁面、邏輯已完整實作完成！**

## 📁 完整檔案清單

### 核心檔案
- ✅ `package.json` - Next.js 15 + React 19 + 所有依賴
- ✅ `tsconfig.json` - TypeScript 配置
- ✅ `tailwind.config.ts` - PRO 色系 + 動畫配置
- ✅ `next.config.js` - Next.js 配置
- ✅ `postcss.config.js` - PostCSS 配置
- ✅ `.env.local` - 環境變數（已建立）
- ✅ `styles/globals.css` - 深度客製化樣式（Glow、Pulse、Glass）

### 類型定義與工具
- ✅ `lib/types/warRoom.ts` - 完整 Type 定義
- ✅ `lib/theme.ts` - 主題管理系統
- ✅ `lib/ws/warRoomClientPro.ts` - WebSocket PRO 客戶端（心跳包、自動重連）

### PRO 組件
- ✅ `components/pro/CommandPanelPro.tsx` - 專業指揮面板
- ✅ `components/pro/RoleCardPro.tsx` - Bloomberg 風格角色卡片
- ✅ `components/pro/SummaryCardPro.tsx` - Mission Summary 卡片
- ✅ `components/pro/TimelinePro.tsx` - 專業事件時間軸
- ✅ `components/pro/__init__.ts` - 模組匯出

### 通用組件
- ✅ `components/common/Badge.tsx` - 徽章組件
- ✅ `components/common/ProviderTag.tsx` - Provider 標籤
- ✅ `components/common/ProviderIndicator.tsx` - Provider 指示燈
- ✅ `components/common/LoadingDots.tsx` - 載入動畫
- ✅ `components/common/ThemeToggle.tsx` - 主題切換
- ✅ `components/common/ThemeScript.tsx` - 主題初始化

### 控制組件（已升級）
- ✅ `components/controls/ModeSelector.tsx` - 金屬開關模式選擇器
- ✅ `components/controls/ProviderSelector.tsx` - 多色指示燈 Provider 選擇
- ✅ `components/controls/StockInput.tsx` - 標籤式股票輸入
- ✅ `components/controls/PromptInput.tsx` - 大型指令輸入區
- ✅ `components/controls/ControlPanel.tsx` - 控制面板（已升級）

### 戰情室組件
- ✅ `components/war-room/RoleCard.tsx` - 基礎角色卡片
- ✅ `components/war-room/RoleGrid.tsx` - 角色網格（使用 RoleCardPro）
- ✅ `components/war-room/StatusBar.tsx` - 狀態列（已升級）
- ✅ `components/war-room/EventTimeline.tsx` - 基礎時間軸
- ✅ `components/war-room/MissionSummary.tsx` - Mission Summary（舊版）

### Layout
- ✅ `components/layout/WarRoomLayout.tsx` - 基礎 Layout
- ✅ `components/layout/WarRoomLayoutPro.tsx` - PRO 版 Layout

### 頁面
- ✅ `app/layout.tsx` - Root Layout（含主題初始化）
- ✅ `app/page.tsx` - 主頁面（使用 WarRoomLayoutPro + WebSocket PRO）
- ✅ `app/demo/tsmc/page.tsx` - Demo 頁面（自動執行）

## 🚀 啟動方式

### 步驟 1: 安裝依賴

```bash
cd /Users/kevincheng/JarvisV1/frontend/war-room-web
npm install
```

### 步驟 2: 確認環境變數

`.env.local` 已建立，包含：
```env
NEXT_PUBLIC_WAR_ROOM_BACKEND_URL=http://localhost:8081
NEXT_PUBLIC_WAR_ROOM_ENV=development
NEXT_PUBLIC_WAR_ROOM_TITLE="J-GOD AI 戰情室 v6"
NEXT_PUBLIC_WAR_ROOM_THEME="dark"
```

### 步驟 3: 啟動後端（終端 1）

```bash
cd /Users/kevincheng/JarvisV1
uvicorn jgod.war_room_backend_v6.main:app --host 0.0.0.0 --port 8081 --reload
```

### 步驟 4: 啟動前端（終端 2）

```bash
cd /Users/kevincheng/JarvisV1/frontend/war-room-web
npm run dev
```

### 步驟 5: 訪問

- **主頁**: http://localhost:3000
- **Demo**: http://localhost:3000/demo/tsmc
- **後端**: http://localhost:8081

## 🎨 視覺效果

### Bloomberg × Military 風格

1. **Ultra Dark 背景** (#0C0F11)
2. **Glass Panel 效果** - 毛玻璃 + 邊框
3. **Glow 發光效果** - 藍/綠/紅/金
4. **Pulse 脈衝動畫** - 運行時邊框脈衝
5. **漸層文字** - 標題使用漸層色彩
6. **金屬開關** - 模式選擇器
7. **多色指示燈** - Provider 狀態顯示

### 動畫效果

- ✅ **Framer Motion** - 過渡動畫
- ✅ **Typing** - 打字機效果（streaming 時）
- ✅ **Pulse Border** - 脈衝邊框（running 時）
- ✅ **Shimmer** - 閃爍動畫（按鈕）
- ✅ **Fade In** - 淡入效果（完成時）

## 🔌 WebSocket 功能

### PRO 版客戶端特性

- ✅ **自動重連** - 最多 3 次，每次間隔 3 秒
- ✅ **心跳包** - 每 20 秒發送 ping
- ✅ **狀態管理** - disconnected / connecting / connected / reconnecting
- ✅ **狀態回調** - 即時更新 UI 狀態

### 事件處理

- ✅ `session_start` - Session 開始
- ✅ `role_start` - 角色開始（並行）
- ✅ `role_chunk` - Streaming chunk（即時更新）
- ✅ `role_done` - 角色完成
- ✅ `summary` - 最終總結
- ✅ `error` - 錯誤處理

## 📊 組件功能

### CommandPanelPro

- ✅ 金屬開關式模式選擇器（God / Custom）
- ✅ 多色 Provider 指示燈（藍/黃/青/綠）
- ✅ 標籤式股票輸入（可移除）
- ✅ 大型指令輸入區（字元計數）
- ✅ 主紅鍵啟動按鈕（Hover pulse）

### RoleCardPro

- ✅ Glass Panel 效果
- ✅ 漸層標題
- ✅ 打字機效果（running 時）
- ✅ Markdown 渲染（done 時）
- ✅ Pulse 邊框動畫（running 時）
- ✅ 執行時間顯示

### SummaryCardPro

- ✅ AI 共識統計
- ✅ 市場方向（Long/Short/Neutral）
- ✅ 風險等級（1-5）
- ✅ 風控建議摘要
- ✅ 量化分析摘要
- ✅ 策略統整

### TimelinePro

- ✅ Icon 標記（🚀 🎯 🔹 ✔️ 📘 ❌）
- ✅ 時間戳記
- ✅ 事件分組（不同顏色邊框）
- ✅ 自動滾動到底

## 🎯 功能驗證清單

- [x] Next.js 15 / React 19 升級完成
- [x] 深度客製化 Tailwind 配置完成
- [x] WebSocket PRO 客戶端完成（心跳包、自動重連）
- [x] 所有 PRO 組件完成
- [x] 主題系統完成（Dark / Ultra Dark）
- [x] 響應式設計完成（Mobile / Tablet / Desktop）
- [x] Demo 頁面完成
- [x] 所有動畫效果完成
- [x] 事件處理邏輯完成
- [x] 狀態管理完成

## 📝 技術規格

- **Next.js**: 15.0.0
- **React**: 19.0.0
- **TypeScript**: 5.3.3
- **Tailwind CSS**: 3.4.1（深度客製化）
- **Framer Motion**: 11.0.0（動畫）
- **React Markdown**: 9.0.0（Markdown 渲染）
- **clsx**: 2.1.0（條件樣式）

## 🎬 使用流程

1. 啟動後端和前端
2. 訪問 http://localhost:3000
3. 選擇模式（God / Custom）
4. 選擇 Provider（God 模式自動全選）
5. 輸入股票代碼（例如：2330, 2412）
6. 輸入使用者指令
7. 點擊「⚔️ 啟動 J-GOD 作戰分析」
8. 觀察各角色卡片即時更新
9. 查看 Mission Summary（所有角色完成後）
10. 查看事件時間軸

## 🔗 WebSocket URL

WebSocket URL 透過環境變數自動設定：
- 開發環境：`ws://localhost:8081/ws/v6/war-room/{session_id}`
- 生產環境：`wss://api.j-god.ai/ws/v6/war-room/{session_id}`

自動轉換邏輯：
- `http://` → `ws://`
- `https://` → `wss://`

## ✨ 完成！

所有功能已完整實作，可直接啟動使用！

