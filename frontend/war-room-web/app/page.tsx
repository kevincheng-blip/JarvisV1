"use client";

import { useState, useCallback } from "react";
import { WarRoomLayoutPro } from "@/components/layout/WarRoomLayoutPro";
import {
  WarRoomSessionState,
  createInitialSessionState,
  resetForNextRun,
  RoleKey,
  ProviderKey,
  resolveRoleKeyFromBackendName,
} from "@/lib/types/warRoom";
import { WarRoomWebSocketClientPro, createSession, WebSocketStatus } from "@/lib/ws/warRoomClientPro";
import { WarRoomEvent } from "@/lib/types/warRoom";

export default function Home() {
  const [state, setState] = useState<WarRoomSessionState>(createInitialSessionState());
  const [wsClient, setWsClient] = useState<WarRoomWebSocketClientPro | null>(null);
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>("disconnected");

  const handleStart = useCallback(
    async (config: {
      mode: "god" | "custom";
      enabledProviders: ProviderKey[];
      stockIds: string[];
      userPrompt: string;
    }) => {
      try {
        // 1. 建立 Session
        const sessionResponse = await createSession({
          stock_ids: config.stockIds,
          mode: config.mode,
          enabled_providers: config.enabledProviders,
          user_prompt: config.userPrompt,
          max_tokens: 2048,
        });

        const sessionId = sessionResponse.session_id;

        // 2. 初始化狀態（如果是新一輪，先重置）
        const currentState = state.status === "finished" ? resetForNextRun(state) : state;
        const newState = {
          ...createInitialSessionState(),
          // 保留上一輪的 events（如果有的話）
          events: currentState.status === "finished" ? currentState.events : [],
        };
        newState.sessionId = sessionId;
        newState.status = "running";
        newState.isRunning = true;
        newState.mode = config.mode;
        newState.enabledProviders = config.enabledProviders;
        newState.startedAt = Date.now();

        // 設定所有角色為 pending
        Object.keys(newState.roles).forEach((key) => {
          newState.roles[key as RoleKey].status = "pending";
        });

        setState(newState);

        // 3. 建立 WebSocket 連線
        const client = new WarRoomWebSocketClientPro();

        client.onEvent((event: WarRoomEvent) => {
          setState((prev) => handleEvent(prev, event));
        });

        client.onError((error) => {
          console.error("[WS] Error:", error);
          setState((prev) => ({
            ...prev,
            status: "finished",
            isRunning: false,
          }));
        });

        client.onClose(() => {
          console.log("[WS] Closed");
          setState((prev) => ({
            ...prev,
            status: "finished",
            isRunning: false,
            finishedAt: Date.now(),
          }));
        });

        client.onStatusChange((status) => {
          setWsStatus(status);
        });

        await client.connect(sessionId, {
          stock_ids: config.stockIds,
          mode: config.mode,
          enabled_providers: config.enabledProviders,
          user_prompt: config.userPrompt,
          max_tokens: 2048,
        });

        setWsClient(client);
      } catch (error) {
        console.error("Failed to start war room:", error);
        alert(`啟動失敗: ${error instanceof Error ? error.message : "Unknown error"}`);
        setState((prev) => ({
          ...prev,
          status: "finished",
          isRunning: false,
        }));
      }
    },
    []
  );

  const handleEvent = (prev: WarRoomSessionState, event: WarRoomEvent): WarRoomSessionState => {
    const newState = { ...prev };
    newState.events = [...prev.events, event];

    // 解析後端角色名稱為前端 RoleKey
    const resolvedRoleKey = event.role ? resolveRoleKeyFromBackendName(event.role) : null;
    
    // Debug log（開發模式）
    if (process.env.NODE_ENV === "development") {
      console.debug("[WS_EVENT]", event.type, event.role, resolvedRoleKey, resolvedRoleKey ? newState.roles[resolvedRoleKey] : null);
    }

    // 如果無法解析角色名稱，發出警告
    if (event.role && !resolvedRoleKey) {
      console.warn(`[WS_EVENT] Unknown role name from backend: "${event.role}"`);
    }

    switch (event.type) {
      case "session_start":
        newState.status = "running";
        newState.isRunning = true;
        break;

      case "role_start":
        if (resolvedRoleKey) {
          const role = newState.roles[resolvedRoleKey];
          if (role) {
            role.status = "running";
            role.provider = event.provider || null;
            role.startedAt = Date.now();
          }
        }
        break;

      case "role_chunk":
        if (resolvedRoleKey && event.chunk) {
          const role = newState.roles[resolvedRoleKey];
          if (role) {
            // 追蹤首響時間（向後兼容）
            if (!role.firstChunkAt && role.content.length === 0) {
              role.firstChunkAt = Date.now();
            }
            // 從後端接收首響時間（優先使用）
            if (event.first_token_ms !== null && event.first_token_ms !== undefined) {
              role.firstTokenMs = event.first_token_ms;
            }
            role.content += event.chunk;
            role.status = "running";
          }
        }
        break;

      case "role_done":
        if (resolvedRoleKey) {
          const role = newState.roles[resolvedRoleKey];
          if (role) {
            role.status = event.error ? "error" : "done";
            role.finishedAt = Date.now();
            // 從後端接收 timing 資訊
            if (event.first_token_ms !== null && event.first_token_ms !== undefined) {
              role.firstTokenMs = event.first_token_ms;
            }
            if (event.total_ms !== null && event.total_ms !== undefined) {
              role.totalMs = event.total_ms;
            }
            if (event.status) {
              role.roleStatus = event.status;
            }
            if (event.error) {
              role.error = event.error;
            }
            if (event.content) {
              role.content = event.content;
            }
          }
        }
        break;

      case "summary":
        // 將 summary 附加到 Strategist 角色
        const strategist = newState.roles["strategist"];
        if (strategist && event.content) {
          strategist.content += "\n\n--- 總結 ---\n" + event.content;
        }
        // Summary 事件表示所有角色完成，重置狀態以允許下一輪
        newState.status = "finished";
        newState.isRunning = false;
        newState.finishedAt = Date.now();
        break;

      case "error":
        if (resolvedRoleKey) {
          const role = newState.roles[resolvedRoleKey];
          if (role) {
            role.status = "error";
            role.error = event.error || "Unknown error";
          }
        }
        break;
    }

    // 檢查是否所有角色都完成
    const allRoles = Object.values(newState.roles);
    const allDone = allRoles.every(
      (r) => r.status === "done" || r.status === "error"
    );

    if (allDone && newState.isRunning && newState.status === "running") {
      // 所有角色完成，但還沒收到 summary，先標記為 finished
      // 如果之後收到 summary，會再次更新
      newState.status = "finished";
      newState.isRunning = false;
      newState.finishedAt = Date.now();
    }

    return newState;
  };

  return <WarRoomLayoutPro state={state} onStart={handleStart} wsStatus={wsStatus} />;
}
