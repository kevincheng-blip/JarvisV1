"use client";

import { useEffect, useState, useCallback } from "react";
import { WarRoomLayoutPro } from "@/components/layout/WarRoomLayoutPro";
import {
  WarRoomSessionState,
  createInitialSessionState,
  RoleKey,
  ProviderKey,
  resolveRoleKeyFromBackendName,
} from "@/lib/types/warRoom";
import { WarRoomWebSocketClientPro, createSession, WebSocketStatus } from "@/lib/ws/warRoomClientPro";
import { WarRoomEvent } from "@/lib/types/warRoom";

export default function DemoTsmcPage() {
  const [state, setState] = useState<WarRoomSessionState>(createInitialSessionState());
  const [wsClient, setWsClient] = useState<WarRoomWebSocketClientPro | null>(null);
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>("disconnected");
  const [autoStarted, setAutoStarted] = useState(false);

  const handleStart = useCallback(
    async (config: {
      mode: "god" | "custom";
      enabledProviders: ProviderKey[];
      stockIds: string[];
      userPrompt: string;
    }) => {
      try {
        const sessionResponse = await createSession({
          stock_ids: config.stockIds,
          mode: config.mode,
          enabled_providers: config.enabledProviders,
          user_prompt: config.userPrompt,
          max_tokens: 2048,
        });

        const sessionId = sessionResponse.session_id;
        const newState = createInitialSessionState();
        newState.sessionId = sessionId;
        newState.status = "running";
        newState.isRunning = true;
        newState.mode = config.mode;
        newState.enabledProviders = config.enabledProviders;
        newState.startedAt = Date.now();

        Object.keys(newState.roles).forEach((key) => {
          newState.roles[key as RoleKey].status = "pending";
        });

        setState(newState);

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
          max_tokens: 2048,
        });

        setWsClient(client);
      } catch (error) {
        console.error("Failed to start war room:", error);
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
        const strategist = newState.roles["strategist"];
        if (strategist && event.content) {
          strategist.content += "\n\n--- 總結 ---\n" + event.content;
        }
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

    const allRoles = Object.values(newState.roles);
    const allDone = allRoles.every((r) => r.status === "done" || r.status === "error");

    if (allDone && newState.isRunning && newState.status === "running") {
      newState.status = "finished";
      newState.isRunning = false;
      newState.finishedAt = Date.now();
    }

    return newState;
  };

  // 自動啟動
  useEffect(() => {
    if (!autoStarted) {
      setAutoStarted(true);
      setTimeout(() => {
        handleStart({
          mode: "god",
          enabledProviders: ["gpt", "claude", "gemini", "perplexity"],
          stockIds: ["2330"],
          userPrompt: "請分析台積電（TSMC）的短線投資建議，重點關注技術面與基本面",
        });
      }, 1000);
    }
  }, [autoStarted, handleStart]);

  return (
    <div>
      <div className="bg-ai-blue/10 border-b border-ai-blue/30 px-6 py-2 text-center">
        <p className="text-sm text-ai-blue font-semibold">
          🎬 Demo 模式：自動執行台積電（2330）分析
        </p>
      </div>
      <WarRoomLayoutPro state={state} onStart={handleStart} wsStatus={wsStatus} />
    </div>
  );
}

