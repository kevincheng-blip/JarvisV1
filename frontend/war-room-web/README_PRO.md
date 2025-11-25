# J-GOD War Room Frontend v6.0 PRO

## 🎨 PRO UIUX 升級完成

### 新增功能

1. **專業左側指揮面板**
   - 深色鋼鐵風格 + Glow 邊框效果
   - 金屬開關式模式選擇器
   - 多色 Provider 指示燈（藍/黃/青/綠）
   - 股票輸入帶自動完成標籤
   - 大型 ChatGPT 風格指令輸入區

2. **Bloomberg Terminal 風格角色卡片**
   - 統一專業風格設計
   - 動畫效果（pulse、typing、fade-in）
   - 執行時間顯示
   - 狀態標籤（pending / running / done）
   - 漸層標題效果

3. **專業戰情時間軸**
   - 現代化事件點設計
   - 自動滾動到底
   - 事件分組顯示
   - Icon 標記

4. **Mission Summary 卡片**
   - AI 共識統計
   - 多空方向建議
   - 風控建議摘要
   - 量化分析摘要
   - 策略統整

5. **WebSocket 自動重連系統**
   - 斷線自動重連（最多 5 次）
   - UI 顯示「重新連線中...」
   - 重連成功後繼續接收事件

6. **Dark / Ultra Dark 雙主題**
   - 右上角主題切換按鈕
   - 自動保存主題偏好
   - 即時切換

7. **Demo 頁面**
   - `/demo/tsmc` - 自動執行台積電分析
   - 完整展示工作流程

## 🚀 啟動方式

### 後端（FastAPI v6）

```bash
cd /Users/kevincheng/JarvisV1
uvicorn jgod.war_room_backend_v6.main:app --host 0.0.0.0 --port 8081 --reload
```

### 前端（Next.js v6 PRO）

```bash
cd /Users/kevincheng/JarvisV1/frontend/war-room-web
npm install
npm run dev
```

- 前端：http://localhost:3000
- Demo：http://localhost:3000/demo/tsmc
- 後端：http://localhost:8081

## 🎯 主要改進

### UI/UX 升級

- ✅ 深色鋼鐵風格設計
- ✅ Glow 邊框效果
- ✅ 漸層文字效果
- ✅ 動畫過渡效果
- ✅ 專業級視覺反饋

### 功能增強

- ✅ WebSocket 自動重連
- ✅ 主題切換系統
- ✅ Mission Summary 卡片
- ✅ 改進的事件時間軸
- ✅ 專業級角色卡片

### 開發體驗

- ✅ TypeScript 完整類型
- ✅ 模組化組件設計
- ✅ 響應式布局
- ✅ 自訂滾動條樣式

## 📝 環境變數

`.env.local`:
```env
NEXT_PUBLIC_WAR_ROOM_BACKEND_URL=http://localhost:8081
NEXT_PUBLIC_WAR_ROOM_ENV=development
NEXT_PUBLIC_WAR_ROOM_TITLE="J-GOD AI 戰情室 v6"
NEXT_PUBLIC_WAR_ROOM_THEME="dark"
```

## 🎨 主題系統

- **Dark**: 標準深色主題（預設）
- **Ultra Dark**: 極致深色主題

切換方式：點擊右上角主題切換按鈕

## 🔄 WebSocket 重連

- 自動重連延遲：3 秒
- 最大重連次數：5 次
- UI 顯示重連狀態

## 📊 Mission Summary

當所有角色完成後，會自動顯示 Mission Summary 卡片，包含：

- AI 共識統計
- 短線方向（多/空/中性）
- 風控建議
- 量化分析
- 策略統整

