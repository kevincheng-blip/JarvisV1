"use client";

import { RoleState } from "@/lib/types/warRoom";
import { ProviderTag } from "../common/ProviderTag";
import { LoadingDots } from "../common/LoadingDots";

interface RoleCardProps {
  role: RoleState;
}

export function RoleCard({ role }: RoleCardProps) {
  const getStatusDisplay = () => {
    switch (role.status) {
      case "idle":
        return <span className="text-gray-500 text-xs">等待啟動</span>;
      case "pending":
        return <span className="text-yellow-400 text-xs animate-pulse">準備中...</span>;
      case "running":
        return <LoadingDots />;
      case "done":
        return <span className="text-green-400 text-xs font-semibold">✓ 完成</span>;
      case "error":
        return <span className="text-red-400 text-xs font-semibold">✗ 錯誤</span>;
      default:
        return null;
    }
  };

  const getCardStyles = () => {
    const base = "bg-gradient-to-br from-gray-900/80 to-gray-950/80 border-2 rounded-2xl p-5 h-full flex flex-col transition-all duration-500 backdrop-blur-sm";
    
    switch (role.status) {
      case "running":
        return `${base} border-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.3)] animate-pulse-border`;
      case "done":
        return `${base} border-green-500/50 shadow-[0_0_20px_rgba(34,197,94,0.2)]`;
      case "error":
        return `${base} border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.2)]`;
      default:
        return `${base} border-gray-800/50`;
    }
  };

  const getExecutionTime = () => {
    if (role.finishedAt && role.startedAt) {
      return ((role.finishedAt - role.startedAt) / 1000).toFixed(2);
    }
    if (role.startedAt) {
      return ((Date.now() - role.startedAt) / 1000).toFixed(1);
    }
    return null;
  };

  return (
    <div className={getCardStyles()}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-200 mb-2 tracking-wide">
            <span className="bg-gradient-to-r from-gray-200 to-gray-400 bg-clip-text text-transparent">
              {role.label}
            </span>
          </h3>
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
          <div className="text-red-400 text-sm space-y-2">
            <div className="font-semibold text-red-300 border-l-2 border-red-500 pl-2">
              【錯誤】
            </div>
            <div className="text-red-400/80 whitespace-pre-wrap">{role.error}</div>
          </div>
        ) : role.content ? (
          <div className="text-gray-300 text-sm whitespace-pre-wrap leading-relaxed font-mono">
            {role.status === "running" ? (
              <span className="animate-typing">{role.content}</span>
            ) : (
              role.content
            )}
          </div>
        ) : role.status === "idle" || role.status === "pending" ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">
            <div className="text-center">
              <div className="mb-2">⏳</div>
              <div>等待分析開始...</div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Footer */}
      {role.status === "done" && role.finishedAt && role.startedAt && (
        <div className="mt-3 pt-3 border-t border-gray-800 flex items-center justify-between text-xs">
          <span className="text-gray-500">執行完成</span>
          <span className="text-gray-400 font-mono">
            {((role.finishedAt - role.startedAt) / 1000).toFixed(2)}s
          </span>
        </div>
      )}
    </div>
  );
}

