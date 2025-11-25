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
    <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 space-y-6">
      <h2 className="text-xl font-bold text-gray-200">控制面板</h2>
      
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
        className={`w-full px-6 py-3 rounded-lg font-semibold transition-colors ${
          canStart
            ? "bg-blue-600 hover:bg-blue-700 text-white"
            : "bg-gray-700 text-gray-500 cursor-not-allowed"
        }`}
      >
        ⚔️ 啟動 J-GOD 戰情室
      </button>
    </div>
  );
}

