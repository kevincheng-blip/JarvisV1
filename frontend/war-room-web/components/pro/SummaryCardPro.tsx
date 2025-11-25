"use client";

import { WarRoomSessionState } from "@/lib/types/warRoom";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface SummaryCardProProps {
  state: WarRoomSessionState;
}

export function SummaryCardPro({ state }: SummaryCardProProps) {
  const allDone = Object.values(state.roles).every(
    (r) => r.status === "done" || r.status === "error"
  );

  const hasSummary = state.events.some((e) => e.type === "summary");

  if (!allDone || !hasSummary) {
    return null;
  }

  // 從各角色內容中提取關鍵資訊
  const strategist = state.roles["Strategist"];
  const riskOfficer = state.roles["Risk Officer"];
  const quantLead = state.roles["Quant Lead"];
  const intelOfficer = state.roles["Intel Officer"];

  const getConsensus = () => {
    const successfulRoles = Object.values(state.roles).filter((r) => r.status === "done");
    return successfulRoles.length;
  };

  const extractDirection = (content: string): "Long" | "Short" | "Neutral" | null => {
    if (/多|買|看漲|bullish|long|做多/i.test(content)) return "Long";
    if (/空|賣|看跌|bearish|short|做空/i.test(content)) return "Short";
    if (/中性|持平|neutral/i.test(content)) return "Neutral";
    return null;
  };

  const extractRiskLevel = (content: string): number => {
    // 簡化版：從內容中提取風險等級（1-5）
    if (/高風險|high risk|危險/i.test(content)) return 5;
    if (/中高風險|medium-high/i.test(content)) return 4;
    if (/中風險|medium/i.test(content)) return 3;
    if (/低風險|low risk/i.test(content)) return 2;
    if (/極低風險|very low/i.test(content)) return 1;
    return 3; // 預設
  };

  const direction = strategist?.content ? extractDirection(strategist.content) : null;
  const riskLevel = riskOfficer?.content ? extractRiskLevel(riskOfficer.content) : 3;
  const consensus = getConsensus();
  const totalRoles = Object.keys(state.roles).length;

  const summaryEvent = state.events.find((e) => e.type === "summary");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel-strong border-2 border-metal-gold/50 rounded-2xl p-6 glow-gold"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold text-foreground">
          <span className="bg-gradient-to-r from-metal-gold to-command-red bg-clip-text text-transparent">
            J-GOD FINAL DECISION — 作戰總評
          </span>
        </h3>
        <div className="px-3 py-1 bg-military-green/20 border border-military-green/50 rounded-lg">
          <span className="text-military-green text-sm font-semibold">完成</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-titanium/50 rounded-xl p-4 border border-titanium">
          <div className="text-xs text-gray-400 mb-1">AI 共識</div>
          <div className="text-2xl font-bold text-ai-blue font-mono">
            {consensus}/{totalRoles}
          </div>
        </div>
        <div className="bg-titanium/50 rounded-xl p-4 border border-titanium">
          <div className="text-xs text-gray-400 mb-1">總耗時</div>
          <div className="text-2xl font-bold text-military-green font-mono">
            {state.finishedAt && state.startedAt
              ? `${((state.finishedAt - state.startedAt) / 1000).toFixed(1)}s`
              : "N/A"}
          </div>
        </div>
        <div className="bg-titanium/50 rounded-xl p-4 border border-titanium">
          <div className="text-xs text-gray-400 mb-1">市場方向</div>
          <div
            className={`text-2xl font-bold font-mono ${
              direction === "Long"
                ? "text-military-green"
                : direction === "Short"
                ? "text-command-red"
                : "text-gray-400"
            }`}
          >
            {direction === "Long" ? "📈 Long" : direction === "Short" ? "📉 Short" : "➡️ Neutral"}
          </div>
        </div>
        <div className="bg-titanium/50 rounded-xl p-4 border border-titanium">
          <div className="text-xs text-gray-400 mb-1">風險等級</div>
          <div className="text-2xl font-bold text-command-red font-mono">
            {riskLevel}/5
          </div>
        </div>
      </div>

      {/* Summary Content */}
      {summaryEvent?.content && (
        <div className="mb-6 p-4 bg-titanium/30 rounded-xl border border-ai-blue/30">
          <div className="text-sm font-semibold text-ai-blue mb-2">📘 策略統整</div>
          <div className="prose prose-invert prose-sm max-w-none text-foreground">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {summaryEvent.content}
            </ReactMarkdown>
          </div>
        </div>
      )}

      {/* Risk Assessment */}
      {riskOfficer?.content && (
        <div className="mb-4 p-4 bg-command-red/10 border border-command-red/30 rounded-xl">
          <div className="text-sm font-semibold text-command-red mb-2">⚠️ 風控建議</div>
          <div className="text-sm text-foreground line-clamp-3">
            {riskOfficer.content.substring(0, 300)}...
          </div>
        </div>
      )}

      {/* Technical Analysis */}
      {quantLead?.content && (
        <div className="mb-4 p-4 bg-ai-blue/10 border border-ai-blue/30 rounded-xl">
          <div className="text-sm font-semibold text-ai-blue mb-2">📊 量化分析</div>
          <div className="text-sm text-foreground line-clamp-3">
            {quantLead.content.substring(0, 300)}...
          </div>
        </div>
      )}

      {/* Intel Summary */}
      {intelOfficer?.content && (
        <div className="p-4 bg-military-green/10 border border-military-green/30 rounded-xl">
          <div className="text-sm font-semibold text-military-green mb-2">🔍 情報摘要</div>
          <div className="text-sm text-foreground line-clamp-3">
            {intelOfficer.content.substring(0, 300)}...
          </div>
        </div>
      )}
    </motion.div>
  );
}

