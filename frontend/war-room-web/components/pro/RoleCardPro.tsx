"use client";

import { RoleState, ROLE_NAME_MAP } from "@/lib/types/warRoom";
import { ProviderTag } from "../common/ProviderTag";
import { LoadingDots } from "../common/LoadingDots";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import clsx from "clsx";

interface RoleCardProProps {
  role: RoleState;
}

export function RoleCardPro({ role }: RoleCardProProps) {
  const getStatusDisplay = () => {
    switch (role.status) {
      case "idle":
        return <span className="text-gray-500 text-xs">等待啟動</span>;
      case "pending":
        return <span className="text-yellow-400 text-xs animate-pulse">準備中...</span>;
      case "running":
        return <LoadingDots />;
      case "done":
        return <span className="text-military-green text-xs font-semibold">✓ 完成</span>;
      case "error":
        return <span className="text-command-red text-xs font-semibold">✗ 錯誤</span>;
      default:
        return null;
    }
  };

  const getCardStyles = () => {
    const base = "glass-panel border-2 rounded-2xl p-5 h-full flex flex-col transition-all duration-500";
    
    switch (role.status) {
      case "running":
        return `${base} border-ai-blue/50 pulse-border-blue`;
      case "done":
        return `${base} border-military-green/50 glow-green`;
      case "error":
        return `${base} border-command-red/50 glow-red`;
      default:
        return `${base} border-titanium/50`;
    }
  };

  const getExecutionTime = () => {
    if (role.finishedAt && role.startedAt) {
      const totalTime = ((role.finishedAt - role.startedAt) / 1000).toFixed(1);
      if (role.firstChunkAt) {
        const firstChunkTime = ((role.firstChunkAt - role.startedAt) / 1000).toFixed(1);
        return `首響：${firstChunkTime}s｜總耗時：${totalTime}s`;
      }
      return `總耗時：${totalTime}s`;
    }
    if (role.startedAt) {
      const elapsed = ((Date.now() - role.startedAt) / 1000).toFixed(1);
      if (role.firstChunkAt) {
        const firstChunkTime = ((role.firstChunkAt - role.startedAt) / 1000).toFixed(1);
        return `首響：${firstChunkTime}s｜進行中：${elapsed}s`;
      }
      return `進行中：${elapsed}s`;
    }
    return null;
  };

  return (
    <motion.div
      className={getCardStyles()}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-baseline gap-2 mb-2">
            <h3 className="text-lg font-bold text-foreground tracking-wide">
              <span className="bg-gradient-to-r from-ai-blue to-military-green bg-clip-text text-transparent">
                {ROLE_NAME_MAP[role.key]?.labelZh || role.key}
              </span>
            </h3>
            <span className="text-xs text-gray-500">
              {ROLE_NAME_MAP[role.key]?.labelEn || role.key}
            </span>
          </div>
          {role.provider && (
            <div className="mt-1">
              <ProviderTag provider={role.provider} />
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1">
          {getStatusDisplay()}
          {getExecutionTime() && (
            <span className="text-xs text-gray-500 font-mono">
              {getExecutionTime()}s
            </span>
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto max-h-64 pr-2 custom-scrollbar">
        {role.status === "error" && role.error ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-command-red text-sm space-y-2"
          >
            <div className="font-semibold text-command-red border-l-2 border-command-red pl-2">
              【錯誤】
            </div>
            <div className="text-command-red/80 whitespace-pre-wrap">{role.error}</div>
          </motion.div>
        ) : role.content ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-foreground text-sm leading-relaxed"
          >
            {role.status === "running" ? (
              <div className="font-mono whitespace-pre-wrap animate-typing">
                {role.content}
              </div>
            ) : (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {role.content}
                </ReactMarkdown>
              </div>
            )}
          </motion.div>
        ) : role.status === "idle" || role.status === "pending" ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">
            <div className="text-center">
              <div className="mb-2 text-2xl">⏳</div>
              <div>等待分析開始...</div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Footer */}
      {role.status === "done" && role.finishedAt && role.startedAt && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-3 pt-3 border-t border-titanium/50 flex items-center justify-between text-xs"
        >
          <span className="text-gray-500">執行完成</span>
          <span className="text-military-green font-mono font-semibold">
            {((role.finishedAt - role.startedAt) / 1000).toFixed(2)}s
          </span>
        </motion.div>
      )}
    </motion.div>
  );
}

