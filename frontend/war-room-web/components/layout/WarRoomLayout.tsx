"use client";

import { ControlPanel } from "../controls/ControlPanel";
import { RoleGrid } from "../war-room/RoleGrid";
import { StatusBar } from "../war-room/StatusBar";
import { EventTimeline } from "../war-room/EventTimeline";
import { WarRoomSessionState, ProviderKey } from "@/lib/types/warRoom";

interface WarRoomLayoutProps {
  state: WarRoomSessionState;
  onStart: (config: {
    mode: "god" | "custom";
    enabledProviders: ProviderKey[];
    stockIds: string[];
    userPrompt: string;
  }) => void;
}

export function WarRoomLayout({ state, onStart }: WarRoomLayoutProps) {
  const stockIds = state.events
    .find((e) => e.type === "session_start")
    ?.meta?.stock_ids as string[] || [];

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/50 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-200">
          J-GOD Multi-AI War Room v6
        </h1>
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

            {/* Event Timeline */}
            <EventTimeline events={state.events} />
          </div>
        </div>
      </div>
    </div>
  );
}

