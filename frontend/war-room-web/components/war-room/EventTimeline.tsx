"use client";

import { useEffect, useRef } from "react";
import { WarRoomEvent } from "@/lib/types/warRoom";

interface EventTimelineProps {
  events: WarRoomEvent[];
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

  const getEventDisplay = (event: WarRoomEvent) => {
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

  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 h-64 overflow-y-auto" ref={timelineRef}>
      <h3 className="text-sm font-semibold text-gray-300 mb-3">事件時間軸</h3>
      <div className="space-y-1">
        {events.length === 0 ? (
          <div className="text-gray-500 text-sm">等待事件...</div>
        ) : (
          events.map((event, index) => (
            <div
              key={index}
              className={`text-xs font-mono ${
                event.type === "error"
                  ? "text-red-400"
                  : event.type === "summary"
                  ? "text-green-400"
                  : "text-gray-400"
              }`}
            >
              {getEventDisplay(event)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

