"use client";

import { ControlPanel } from "../controls/ControlPanel";
import { RoleGrid } from "../war-room/RoleGrid";
import { StatusBar } from "../war-room/StatusBar";
import { EventTimeline } from "../war-room/EventTimeline";
import { MissionSummary } from "../war-room/MissionSummary";
import { ThemeToggle } from "../common/ThemeToggle";
import { WarRoomSessionState, ProviderKey } from "@/lib/types/warRoom";

interface WarRoomLayoutProps {
  state: WarRoomSessionState;
  onStart: (config: {
    mode: "god" | "custom";
    enabledProviders: ProviderKey[];
    stockIds: string[];
    userPrompt: string;
  }) => void;
  isReconnecting?: boolean;
}

export function WarRoomLayout({ state, onStart, isReconnecting = false }: WarRoomLayoutProps) {
  const stockIds = state.events
    .find((e) => e.type === "session_start")
    ?.meta?.stock_ids as string[] || [];

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <div className="border-b-2 border-gray-800/50 bg-gradient-to-r from-gray-900/90 to-gray-950/90 px-6 py-4 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-200 tracking-wide">
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                J-GOD Multi-AI War Room v6 PRO
              </span>
            </h1>
            <p className="text-xs text-gray-500 mt-1">Professional Trading Command Center</p>
          </div>
          <div className="flex items-center gap-3">
            {isReconnecting && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/20 border border-yellow-500/50 rounded-lg">
                <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                <span className="text-xs text-yellow-400">重新連線中...</span>
              </div>
            )}
            <ThemeToggle />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left: Control Panel */}
          <div className="col-span-12 lg:col-span-3">
            <ControlPanel onStart={onStart} isRunning={state.isRunning} />
          </div>

          {/* Right: War Room */}
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

            {/* Mission Summary */}
            <MissionSummary state={state} />

            {/* Event Timeline */}
            <EventTimeline events={state.events} />
          </div>
        </div>
      </div>
    </div>
  );
}

