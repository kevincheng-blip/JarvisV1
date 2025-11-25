"use client";

import { CommandPanelPro } from "../pro/CommandPanelPro";
import { RoleGrid } from "../war-room/RoleGrid";
import { StatusBar } from "../war-room/StatusBar";
import { TimelinePro } from "../pro/TimelinePro";
import { SummaryCardPro } from "../pro/SummaryCardPro";
import { ThemeToggle } from "../common/ThemeToggle";
import { WarRoomSessionState, ProviderKey } from "@/lib/types/warRoom";
import { WebSocketStatus } from "@/lib/ws/warRoomClientPro";

interface WarRoomLayoutProProps {
  state: WarRoomSessionState;
  onStart: (config: {
    mode: "god" | "custom";
    enabledProviders: ProviderKey[];
    stockIds: string[];
    userPrompt: string;
  }) => void;
  wsStatus?: WebSocketStatus;
}

export function WarRoomLayoutPro({ state, onStart, wsStatus = "disconnected" }: WarRoomLayoutProProps) {
  const stockIds = state.events
    .find((e) => e.type === "session_start")
    ?.meta?.stock_ids as string[] || [];

  const getStatusBadge = () => {
    switch (wsStatus) {
      case "connected":
        return (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-military-green/20 border border-military-green/50 rounded-lg">
            <div className="w-2 h-2 bg-military-green rounded-full animate-pulse glow-green" />
            <span className="text-xs text-military-green font-semibold">已連線</span>
          </div>
        );
      case "reconnecting":
        return (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/20 border border-yellow-500/50 rounded-lg">
            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
            <span className="text-xs text-yellow-400 font-semibold">重新連線中...</span>
          </div>
        );
      case "connecting":
        return (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-ai-blue/20 border border-ai-blue/50 rounded-lg">
            <div className="w-2 h-2 bg-ai-blue rounded-full animate-pulse" />
            <span className="text-xs text-ai-blue font-semibold">連線中...</span>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-ultra-dark text-foreground">
      {/* Header */}
      <div className="border-b-2 border-titanium/50 bg-titanium/30 px-6 py-4 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground tracking-wide">
              <span className="bg-gradient-to-r from-ai-blue via-military-green to-metal-gold bg-clip-text text-transparent">
                J-GOD Multi-AI War Room v6 PRO
              </span>
            </h1>
            <p className="text-xs text-gray-500 mt-1">Professional Trading Command Center</p>
          </div>
          <div className="flex items-center gap-3">
            {getStatusBadge()}
            <ThemeToggle />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left: Command Panel (25%) */}
          <div className="col-span-12 lg:col-span-3">
            <CommandPanelPro onStart={onStart} isRunning={state.status === "running"} wsStatus={wsStatus} />
          </div>

          {/* Right: War Room (75%) */}
          <div className="col-span-12 lg:col-span-9 space-y-6">
            {/* Status Bar */}
            <StatusBar
              mode={state.mode}
              enabledProviders={state.enabledProviders}
              stockIds={stockIds}
              isRunning={state.isRunning}
              startedAt={state.startedAt}
              finishedAt={state.finishedAt}
            />

            {/* Role Grid */}
            <RoleGrid roles={state.roles} />

            {/* Summary Card */}
            <SummaryCardPro state={state} />

            {/* Event Timeline */}
            <TimelinePro events={state.events} />
          </div>
        </div>
      </div>
    </div>
  );
}

