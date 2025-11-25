"use client";

import { useEffect } from "react";
import { WarRoomLayout } from "@/components/layout/WarRoomLayout";
import {
  WarRoomSessionState,
  createInitialSessionState,
  RoleKey,
  ProviderKey,
} from "@/lib/types/warRoom";
import { WarRoomWebSocketClient, createSession } from "@/lib/ws/warRoomClient";
import { WarRoomEvent } from "@/lib/types/warRoom";
import { useState, useCallback } from "react";

export default function DemoTsmcPage() {
  const [state, setState] = useState<WarRoomSessionState>(createInitialSessionState());
  const [wsClient, setWsClient] = useState<WarRoomWebSocketClient | null>(null);
  const [isReconnecting, setIsReconnecting] = useState(false);
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
          max_tokens: 512,
        });

        const sessionId = sessionResponse.session_id;
        const newState = createInitialSessionState();
        newState.sessionId = sessionId;
        newState.isRunning = true;
        newState.mode = config.mode;
        newState.enabledProviders = config.enabledProviders;
        newState.startedAt = Date.now();

        Object.keys(newState.roles).forEach((key) => {
          newState.roles[key as RoleKey].status = "pending";
        });

        setState(newState);

        const client = new WarRoomWebSocketClient();

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

        client.onReconnecting(() => {
          setIsReconnecting(true);
        });

        client.onReconnected(() => {
          setIsReconnecting(false);
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

    const allRoles = Object.values(newState.roles);
    const allDone = allRoles.every((r) => r.status === "done" || r.status === "error");

    if (allDone && newState.isRunning) {
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
      <div className="bg-blue-500/10 border-b border-blue-500/30 px-6 py-2 text-center">
        <p className="text-sm text-blue-400">
          🎬 Demo 模式：自動執行台積電（2330）分析
        </p>
      </div>
      <WarRoomLayout state={state} onStart={handleStart} isReconnecting={isReconnecting} />
    </div>
  );
}

