"use client";

import { WarRoomSessionState } from "@/lib/types/warRoom";
import { Badge } from "../common/Badge";

interface MissionSummaryProps {
  state: WarRoomSessionState;
}

export function MissionSummary({ state }: MissionSummaryProps) {
  const allDone = Object.values(state.roles).every(
    (r) => r.status === "done" || r.status === "error"
  );

  if (!allDone || !state.finishedAt) {
    return null;
  }

  // 從各角色內容中提取關鍵資訊（使用 RoleKey）
  const strategist = state.roles["strategist"];
  const riskOfficer = state.roles["risk_officer"];
  const quantLead = state.roles["quant_lead"];

  const getConsensus = () => {
    const successfulRoles = Object.values(state.roles).filter((r) => r.status === "done");
    return successfulRoles.length;
  };

  const extractDirection = (content: string): "多" | "空" | "中性" | null => {
    if (/多|買|看漲|bullish|long/i.test(content)) return "多";
    if (/空|賣|看跌|bearish|short/i.test(content)) return "空";
    if (/中性|持平|neutral/i.test(content)) return "中性";
    return null;
  };

  const direction = strategist?.content ? extractDirection(strategist.content) : null;

  return (
    <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 border-2 border-purple-500/30 rounded-2xl p-6 shadow-[0_0_30px_rgba(147,51,234,0.2)]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-200">
          <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            🎯 Mission Summary
          </span>
        </h3>
        <Badge variant="success">完成</Badge>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="space-y-2">
          <div className="text-sm text-gray-400">AI 共識</div>
          <div className="text-2xl font-bold text-gray-200">
            {getConsensus()}/{Object.keys(state.roles).length}
          </div>
        </div>
        <div className="space-y-2">
          <div className="text-sm text-gray-400">總耗時</div>
          <div className="text-2xl font-bold text-gray-200 font-mono">
            {state.finishedAt && state.startedAt
              ? `${((state.finishedAt - state.startedAt) / 1000).toFixed(1)}s`
              : "N/A"}
          </div>
        </div>
      </div>

      {direction && (
        <div className="mb-4 p-4 bg-gray-800/50 rounded-xl border border-gray-700">
          <div className="text-sm text-gray-400 mb-2">短線方向</div>
          <div
            className={`text-3xl font-bold ${
              direction === "多"
                ? "text-green-400"
                : direction === "空"
                ? "text-red-400"
                : "text-gray-400"
            }`}
          >
            {direction === "多" ? "📈 看多" : direction === "空" ? "📉 看空" : "➡️ 中性"}
          </div>
        </div>
      )}

      {riskOfficer?.content && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
          <div className="text-sm font-semibold text-red-400 mb-2">⚠️ 風控建議</div>
          <div className="text-sm text-gray-300 line-clamp-3">
            {riskOfficer.content.substring(0, 200)}...
          </div>
        </div>
      )}

      {quantLead?.content && (
        <div className="mb-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
          <div className="text-sm font-semibold text-blue-400 mb-2">📊 量化分析</div>
          <div className="text-sm text-gray-300 line-clamp-3">
            {quantLead.content.substring(0, 200)}...
          </div>
        </div>
      )}

      {strategist?.content && (
        <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-xl">
          <div className="text-sm font-semibold text-purple-400 mb-2">💡 策略統整</div>
          <div className="text-sm text-gray-300 line-clamp-4">
            {strategist.content.substring(0, 300)}...
          </div>
        </div>
      )}
    </div>
  );
}

