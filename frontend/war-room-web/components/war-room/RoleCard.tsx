"use client";

import { RoleState, ProviderKey } from "@/lib/types/warRoom";
import { ProviderTag } from "../common/ProviderTag";
import { LoadingDots } from "../common/LoadingDots";

interface RoleCardProps {
  role: RoleState;
}

export function RoleCard({ role }: RoleCardProps) {
  const getStatusDisplay = () => {
    switch (role.status) {
      case "idle":
        return <span className="text-gray-500">等待啟動</span>;
      case "pending":
        return <span className="text-yellow-400">準備中...</span>;
      case "running":
        return <LoadingDots />;
      case "done":
        return <span className="text-green-400">✓ 完成</span>;
      case "error":
        return <span className="text-red-400">✗ 錯誤</span>;
      default:
        return null;
    }
  };

  const getBorderColor = () => {
    switch (role.status) {
      case "running":
        return "border-blue-500";
      case "done":
        return "border-green-500";
      case "error":
        return "border-red-500";
      default:
        return "border-gray-700";
    }
  };

  return (
    <div
      className={`bg-gray-900/50 border-2 ${getBorderColor()} rounded-2xl p-4 h-full flex flex-col transition-all duration-300`}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-gray-200">{role.label}</h3>
          {role.provider && (
            <div className="mt-1">
              <ProviderTag provider={role.provider} />
            </div>
          )}
        </div>
        <div className="text-sm">{getStatusDisplay()}</div>
      </div>

      <div className="flex-1 overflow-y-auto max-h-64">
        {role.status === "error" && role.error ? (
          <div className="text-red-400 text-sm">
            <div className="font-semibold mb-1">【錯誤】</div>
            <div>{role.error}</div>
          </div>
        ) : role.content ? (
          <div className="text-gray-300 text-sm whitespace-pre-wrap leading-relaxed">
            {role.content}
          </div>
        ) : role.status === "idle" || role.status === "pending" ? (
          <div className="text-gray-500 text-sm">等待分析開始...</div>
        ) : null}
      </div>

      {role.status === "done" && role.finishedAt && role.startedAt && (
        <div className="mt-2 text-xs text-gray-500">
          耗時: {((role.finishedAt - role.startedAt) / 1000).toFixed(2)}s
        </div>
      )}
    </div>
  );
}

