"use client";

import { useState, useCallback } from "react";
import { WarRoomLayoutPro } from "@/components/layout/WarRoomLayoutPro";
import {
  WarRoomSessionState,
  createInitialSessionState,
  RoleKey,
  ProviderKey,
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
          max_tokens: 512,
        });

        const sessionId = sessionResponse.session_id;

        // 2. 初始化狀態
        const newState = createInitialSessionState();
        newState.sessionId = sessionId;
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
            isRunning: false,
          }));
        });

        client.onClose(() => {
          console.log("[WS] Closed");
          setState((prev) => ({
            ...prev,
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
          max_tokens: 512,
        });

        setWsClient(client);
      } catch (error) {
        console.error("Failed to start war room:", error);
        alert(`啟動失敗: ${error instanceof Error ? error.message : "Unknown error"}`);
        setState((prev) => ({
          ...prev,
          isRunning: false,
        }));
      }
    },
    []
  );

  const handleEvent = (prev: WarRoomSessionState, event: WarRoomEvent): WarRoomSessionState => {
    const newState = { ...prev };
    newState.events = [...prev.events, event];

    switch (event.type) {
      case "session_start":
        newState.isRunning = true;
        break;

      case "role_start":
        if (event.role) {
          const role = newState.roles[event.role as RoleKey];
          if (role) {
            role.status = "running";
            role.provider = event.provider || null;
            role.startedAt = Date.now();
          }
        }
        break;

      case "role_chunk":
        if (event.role && event.chunk) {
          const role = newState.roles[event.role as RoleKey];
          if (role) {
            role.content += event.chunk;
            role.status = "running";
          }
        }
        break;

      case "role_done":
        if (event.role) {
          const role = newState.roles[event.role as RoleKey];
          if (role) {
            role.status = event.error ? "error" : "done";
            role.finishedAt = Date.now();
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
        const strategist = newState.roles["Strategist"];
        if (strategist && event.content) {
          strategist.content += "\n\n--- 總結 ---\n" + event.content;
        }
        break;

      case "error":
        if (event.role) {
          const role = newState.roles[event.role as RoleKey];
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

    if (allDone && newState.isRunning) {
      newState.isRunning = false;
      newState.finishedAt = Date.now();
    }

    return newState;
  };

  return <WarRoomLayoutPro state={state} onStart={handleStart} wsStatus={wsStatus} />;
}
