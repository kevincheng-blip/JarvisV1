"use client";

import { useEffect, useRef } from "react";
import { CouncilChamberEvent } from "@/lib/types/councilChamber";
import { motion } from "framer-motion";
import clsx from "clsx";

interface TimelineProProps {
  events: CouncilChamberEvent[];
}

const EVENT_ICONS: Record<CouncilChamberEvent["type"], string> = {
  session_start: "🚀",
  role_start: "🎯",
  role_chunk: "🔹",
  role_done: "✔️",
  summary: "📘",
  error: "❌",
};

export function TimelinePro({ events }: TimelineProProps) {
  const timelineRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 自動滾到底
    if (timelineRef.current) {
      timelineRef.current.scrollTop = timelineRef.current.scrollHeight;
    }
  }, [events]);

  const formatTime = () => {
    const now = new Date();
    return now.toLocaleTimeString("zh-TW", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const getEventDisplay = (event: CouncilChamberEvent) => {
    const time = formatTime();

    switch (event.type) {
      case "session_start":
        return `Session 啟動`;
      case "role_start":
        return `${event.role_label || event.role} / ${event.provider} 開始分析`;
      case "role_chunk":
        const chunkPreview = event.chunk?.substring(0, 40) || "";
        return `${event.role_label || event.role}: ${chunkPreview}${chunkPreview.length >= 40 ? "..." : ""}`;
      case "role_done":
        return `${event.role_label || event.role} 完成`;
      case "summary":
        return `總結已產生`;
      case "error":
        return `錯誤: ${event.error || "Unknown error"}`;
      default:
        return `${event.type}`;
    }
  };

  const getEventStyles = (type: CouncilChamberEvent["type"]) => {
    switch (type) {
      case "session_start":
        return "bg-ai-blue/10 border-l-ai-blue text-ai-blue";
      case "role_start":
        return "bg-military-green/10 border-l-military-green text-military-green";
      case "role_chunk":
        return "bg-titanium/50 border-l-titanium text-gray-400";
      case "role_done":
        return "bg-military-green/10 border-l-military-green text-military-green";
      case "summary":
        return "bg-metal-gold/10 border-l-metal-gold text-metal-gold";
      case "error":
        return "bg-command-red/10 border-l-command-red text-command-red";
      default:
        return "bg-titanium/50 border-l-titanium text-gray-400";
    }
  };

  return (
    <div
      className="glass-panel border-2 border-titanium/50 rounded-xl p-4 h-80 overflow-y-auto custom-scrollbar"
      ref={timelineRef}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
          戰情時間軸
        </h3>
        <span className="text-xs text-gray-500 font-mono">{events.length} 事件</span>
      </div>
      <div className="space-y-2">
        {events.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-8">等待事件...</div>
        ) : (
          events.map((event, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className={clsx(
                "flex items-start gap-3 p-3 rounded-lg border-l-4 transition-colors",
                getEventStyles(event.type)
              )}
            >
              <span className="text-lg flex-shrink-0">{EVENT_ICONS[event.type]}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-gray-500">{formatTime()}</span>
                  <span className="text-xs font-semibold uppercase">{event.type}</span>
                </div>
                <div className="text-xs font-mono leading-relaxed">
                  {getEventDisplay(event)}
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}

