# War Room Backend v6.0 使用說明

## 啟動後端

### 方法 1: 使用 uvicorn 指令（推薦）

```bash
cd /Users/kevincheng/JarvisV1
uvicorn jgod.war_room_backend_v6.main:app --host 0.0.0.0 --port 8081 --reload
```

### 方法 2: 直接執行 main.py

```bash
cd /Users/kevincheng/JarvisV1
python3 -m jgod.war_room_backend_v6.main
```

### 方法 3: 使用 Python 模組

```bash
cd /Users/kevincheng/JarvisV1
python3 -m uvicorn jgod.war_room_backend_v6.main:app --port 8081
```

## API 端點

### 1. 健康檢查

```bash
GET http://localhost:8081/health
```

回應：
```json
{
  "status": "healthy",
  "version": "6.0.0",
  "active_sessions": 0,
  "providers": ["gpt", "claude", "gemini", "perplexity"]
}
```

### 2. 建立 Session

```bash
POST http://localhost:8081/api/v6/war-room/session
Content-Type: application/json

{
  "stock_ids": ["2330", "2412"],
  "mode": "god",
  "enabled_providers": ["gpt", "claude", "gemini", "perplexity"],
  "user_prompt": "請分析台積電和聯發科的投資建議",
  "max_tokens": 512,
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

回應：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "websocket_url": "/ws/v6/war-room/550e8400-e29b-41d4-a716-446655440000"
}
```

### 3. WebSocket 連線

```
WS ws://localhost:8081/ws/v6/war-room/{session_id}
```

## Next.js 前端連線範例

### TypeScript 範例

```typescript
// types/war-room.ts
export interface WarRoomRequest {
  stock_ids: string[];
  mode: "god" | "custom";
  enabled_providers: string[];
  user_prompt: string;
  max_tokens?: number;
  start_date?: string;
  end_date?: string;
  market_context?: string;
}

export interface WarRoomEvent {
  type: "session_start" | "role_start" | "role_chunk" | "role_done" | "summary" | "error";
  session_id: string;
  role?: string;
  role_label?: string;
  provider?: string;
  chunk?: string;
  content?: string;
  error?: string;
  meta?: Record<string, any>;
}

// hooks/useWarRoom.ts
import { useState, useEffect, useRef } from 'react';
import { WarRoomRequest, WarRoomEvent } from '@/types/war-room';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8081';

export function useWarRoom() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [events, setEvents] = useState<WarRoomEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // 建立 Session
  const createSession = async (request: WarRoomRequest): Promise<string> => {
    const response = await fetch(`${BACKEND_URL}/api/v6/war-room/session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to create session');
    }

    const data = await response.json();
    setSessionId(data.session_id);
    return data.session_id;
  };

  // 連線 WebSocket
  const connectWebSocket = (sessionId: string, request: WarRoomRequest) => {
    const ws = new WebSocket(`ws://localhost:8081/ws/v6/war-room/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      
      // 發送請求
      ws.send(JSON.stringify(request));
    };

    ws.onmessage = (event) => {
      const warRoomEvent: WarRoomEvent = JSON.parse(event.data);
      console.log('Event received:', warRoomEvent.type);
      
      setEvents((prev) => [...prev, warRoomEvent]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };
  };

  // 啟動戰情室
  const startWarRoom = async (request: WarRoomRequest) => {
    try {
      const newSessionId = await createSession(request);
      connectWebSocket(newSessionId, request);
    } catch (error) {
      console.error('Failed to start war room:', error);
      throw error;
    }
  };

  // 關閉連線
  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setSessionId(null);
    setEvents([]);
  };

  // 清理
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  return {
    sessionId,
    events,
    isConnected,
    startWarRoom,
    disconnect,
  };
}

// components/WarRoomPanel.tsx
'use client';

import { useWarRoom } from '@/hooks/useWarRoom';
import { useState } from 'react';

export function WarRoomPanel() {
  const { events, isConnected, startWarRoom, disconnect } = useWarRoom();
  const [userPrompt, setUserPrompt] = useState('');

  const handleStart = async () => {
    await startWarRoom({
      stock_ids: ['2330'],
      mode: 'god',
      enabled_providers: ['gpt', 'claude', 'gemini', 'perplexity'],
      user_prompt: userPrompt,
    });
  };

  // 依角色分組事件
  const roleEvents = events.reduce((acc, event) => {
    if (event.role) {
      if (!acc[event.role]) {
        acc[event.role] = [];
      }
      acc[event.role].push(event);
    }
    return acc;
  }, {} as Record<string, typeof events>);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">J-GOD War Room</h1>
      
      <div className="mb-4">
        <input
          type="text"
          value={userPrompt}
          onChange={(e) => setUserPrompt(e.target.value)}
          placeholder="輸入問題..."
          className="border p-2 w-full"
        />
        <button
          onClick={handleStart}
          disabled={isConnected}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
        >
          {isConnected ? '執行中...' : '啟動戰情室'}
        </button>
        {isConnected && (
          <button
            onClick={disconnect}
            className="mt-2 ml-2 px-4 py-2 bg-red-500 text-white rounded"
          >
            停止
          </button>
        )}
      </div>

      {/* 顯示各角色事件 */}
      <div className="grid grid-cols-2 gap-4">
        {Object.entries(roleEvents).map(([role, roleEventList]) => {
          const chunks = roleEventList
            .filter((e) => e.type === 'role_chunk')
            .map((e) => e.chunk)
            .join('');
          
          return (
            <div key={role} className="border p-4">
              <h3 className="font-bold">{role}</h3>
              <div className="mt-2 whitespace-pre-wrap">{chunks}</div>
            </div>
          );
        })}
      </div>

      {/* 顯示 Summary */}
      {events
        .filter((e) => e.type === 'summary')
        .map((e, i) => (
          <div key={i} className="mt-4 p-4 bg-gray-100">
            <h3 className="font-bold">總結</h3>
            <p>{e.content}</p>
          </div>
        ))}
    </div>
  );
}
```

## 事件流程

1. **前端建立 Session**: `POST /api/v6/war-room/session`
2. **前端連線 WebSocket**: `WS /ws/v6/war-room/{session_id}`
3. **前端發送請求**: 透過 WebSocket 發送 JSON 請求
4. **後端推送事件**:
   - `session_start` - Session 開始
   - `role_start` - 每個角色開始（並行）
   - `role_chunk` - Streaming chunk（多次，並行）
   - `role_done` - 每個角色完成
   - `summary` - 最終總結
   - `error` - 錯誤（如果發生）

## 環境變數

確保設定以下 API Keys（與 v5 相同）：

- `OPENAI_API_KEY` - GPT Provider
- `ANTHROPIC_API_KEY` - Claude Provider
- `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` - Gemini Provider
- `PERPLEXITY_API_KEY` - Perplexity Provider

## 注意事項

1. **CORS**: 目前設定為允許所有來源（`allow_origins=["*"]`），生產環境請改為特定域名
2. **Port**: 預設使用 8081，可在 `main.py` 中修改
3. **WebSocket 連線**: 一個 session 可以有多個 WebSocket 連線（廣播模式）
4. **事件順序**: 事件是即時的，多個角色會並行產生 chunk 事件

