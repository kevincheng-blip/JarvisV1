"use client";

import { useEffect, useRef } from "react";
import { CouncilChamberEvent } from "@/lib/types/councilChamber";

interface EventTimelineProps {
  events: CouncilChamberEvent[];
}

export function EventTimeline({ events }: EventTimelineProps) {
  const timelineRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 自動滾到底
    if (timelineRef.current) {
      timelineRef.current.scrollTop = timelineRef.current.scrollHeight;
    }
  }, [events]);

  const formatTime = (timestamp?: number) => {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    return date.toLocaleTimeString("zh-TW", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const getEventDisplay = (event: CouncilChamberEvent) => {
    const time = formatTime(Date.now()); // 簡化版，實際可用 event.meta?.timestamp

    switch (event.type) {
      case "session_start":
        return `[${time}] Session 啟動`;
      case "role_start":
        return `[${time}] [${event.role_label || event.role} / ${event.provider}] 開始分析`;
      case "role_chunk":
        const chunkPreview = event.chunk?.substring(0, 40) || "";
        return `[${time}] [${event.role_label || event.role}] ${chunkPreview}${chunkPreview.length >= 40 ? "..." : ""}`;
      case "role_done":
        return `[${time}] [${event.role_label || event.role}] 完成`;
      case "summary":
        return `[${time}] [Strategist] 總結已產生`;
      case "error":
        return `[${time}] ❌ 錯誤: ${event.error || "Unknown error"}`;
      default:
        return `[${time}] ${event.type}`;
    }
  };

  const getEventIcon = (type: CouncilChamberEvent["type"]) => {
    switch (type) {
      case "session_start":
        return "🚀";
      case "role_start":
        return "▶️";
      case "role_chunk":
        return "💬";
      case "role_done":
        return "✅";
      case "summary":
        return "📋";
      case "error":
        return "❌";
      default:
        return "•";
    }
  };

  return (
    <div className="bg-gradient-to-br from-gray-900/80 to-gray-950/80 border-2 border-gray-800/50 rounded-xl p-4 h-80 overflow-y-auto custom-scrollbar" ref={timelineRef}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
          戰情時間軸
        </h3>
        <span className="text-xs text-gray-500">{events.length} 事件</span>
      </div>
      <div className="space-y-2">
        {events.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-8">等待事件...</div>
        ) : (
          events.map((event, index) => (
            <div
              key={index}
              className={`flex items-start gap-3 p-2 rounded-lg transition-colors ${
                event.type === "error"
                  ? "bg-red-500/10 border-l-2 border-red-500"
                  : event.type === "summary"
                  ? "bg-green-500/10 border-l-2 border-green-500"
                  : event.type === "session_start"
                  ? "bg-blue-500/10 border-l-2 border-blue-500"
                  : "bg-gray-800/30 border-l-2 border-gray-700 hover:bg-gray-800/50"
              }`}
            >
              <span className="text-lg flex-shrink-0">{getEventIcon(event.type)}</span>
              <div className="flex-1 min-w-0">
                <div
                  className={`text-xs font-mono ${
                    event.type === "error"
                      ? "text-red-400"
                      : event.type === "summary"
                      ? "text-green-400"
                      : event.type === "session_start"
                      ? "text-blue-400"
                      : "text-gray-400"
                  }`}
                >
                  {getEventDisplay(event)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

