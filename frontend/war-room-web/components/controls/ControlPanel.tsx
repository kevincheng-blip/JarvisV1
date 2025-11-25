"use client";

import { useState } from "react";
import { ProviderKey } from "@/lib/types/warRoom";
import { ModeSelector } from "./ModeSelector";
import { ProviderSelector } from "./ProviderSelector";
import { StockInput } from "./StockInput";
import { PromptInput } from "./PromptInput";

interface ControlPanelProps {
  onStart: (config: {
    mode: "god" | "custom";
    enabledProviders: ProviderKey[];
    stockIds: string[];
    userPrompt: string;
  }) => void;
  isRunning: boolean;
}

export function ControlPanel({ onStart, isRunning }: ControlPanelProps) {
  const [mode, setMode] = useState<"god" | "custom">("god");
  const [enabledProviders, setEnabledProviders] = useState<ProviderKey[]>([
    "gpt",
    "claude",
    "gemini",
    "perplexity",
  ]);
  const [stockInput, setStockInput] = useState("");
  const [userPrompt, setUserPrompt] = useState("");

  const parseStockIds = (input: string): string[] => {
    return input
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  };

  const handleStart = () => {
    const stockIds = parseStockIds(stockInput);
    if (stockIds.length === 0) {
      alert("請輸入至少一個股票代碼");
      return;
    }
    if (mode === "custom" && enabledProviders.length === 0) {
      alert("請至少選擇一個 Provider");
      return;
    }

    onStart({
      mode,
      enabledProviders: mode === "god" ? ["gpt", "claude", "gemini", "perplexity"] : enabledProviders,
      stockIds,
      userPrompt,
    });
  };

  const canStart = !isRunning && parseStockIds(stockInput).length > 0 && (mode === "god" || enabledProviders.length > 0);

  return (
    <div className="relative bg-gradient-to-br from-gray-900/90 to-gray-950/90 border-2 border-gray-800/50 rounded-2xl p-6 space-y-6 shadow-[0_0_30px_rgba(0,0,0,0.5)] backdrop-blur-sm">
      {/* Glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 via-purple-600/5 to-blue-600/5 rounded-2xl pointer-events-none" />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-200 tracking-wide">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              指揮面板
            </span>
          </h2>
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
        </div>
        
        <ModeSelector mode={mode} onChange={setMode} />
        
        <ProviderSelector
          enabledProviders={enabledProviders}
          mode={mode}
          onChange={setEnabledProviders}
        />
        
        <StockInput value={stockInput} onChange={setStockInput} />
        
        <PromptInput value={userPrompt} onChange={setUserPrompt} />
        
        <button
          onClick={handleStart}
          disabled={!canStart}
          className={`w-full px-6 py-4 rounded-xl font-bold text-lg transition-all duration-300 relative overflow-hidden ${
            canStart
              ? "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-[0_0_20px_rgba(59,130,246,0.4)] hover:shadow-[0_0_30px_rgba(59,130,246,0.6)] transform hover:scale-[1.02]"
              : "bg-gray-800/50 text-gray-500 cursor-not-allowed border border-gray-700"
          }`}
        >
          {canStart ? (
            <>
              <span className="relative z-10 flex items-center justify-center gap-2">
                <span>⚔️</span>
                <span>啟動 J-GOD 戰情室</span>
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600/0 via-white/10 to-purple-600/0 animate-shimmer" />
            </>
          ) : (
            "⚔️ 啟動 J-GOD 戰情室"
          )}
        </button>
      </div>
    </div>
  );
}

