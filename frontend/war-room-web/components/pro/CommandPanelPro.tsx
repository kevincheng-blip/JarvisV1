"use client";

import { useState, useEffect } from "react";
import { ProviderKey, PROVIDER_CONFIG } from "@/lib/types/warRoom";
import { motion } from "framer-motion";
import clsx from "clsx";

interface CommandPanelProProps {
  onStart: (config: {
    mode: "god" | "custom";
    enabledProviders: ProviderKey[];
    stockIds: string[];
    userPrompt: string;
  }) => void;
  isRunning: boolean;
  wsStatus?: "disconnected" | "connecting" | "connected" | "reconnecting";
}

export function CommandPanelPro({ onStart, isRunning, wsStatus = "disconnected" }: CommandPanelProProps) {
  const [mode, setMode] = useState<"god" | "custom">("god");
  const [enabledProviders, setEnabledProviders] = useState<ProviderKey[]>([
    "gpt",
    "claude",
    "gemini",
    "perplexity",
  ]);
  const [stockInput, setStockInput] = useState("");
  const [userPrompt, setUserPrompt] = useState("");
  const [availableProviders, setAvailableProviders] = useState<ProviderKey[]>([]);

  // 自動偵測可用 Provider（簡化版，實際可從 backend health check 取得）
  useEffect(() => {
    // 預設所有 Provider 可用，實際可從 /health 端點取得
    setAvailableProviders(["gpt", "claude", "gemini", "perplexity"]);
  }, []);

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
  const stockIds = parseStockIds(stockInput);

  const removeStock = (stockId: string) => {
    const newValue = stockInput
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter((s) => s !== stockId)
      .join(", ");
    setStockInput(newValue);
  };

  return (
    <div className="glass-panel-strong rounded-2xl p-6 space-y-6 border-2 border-ai-blue/20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-foreground tracking-wide">
          <span className="bg-gradient-to-r from-ai-blue to-military-green bg-clip-text text-transparent">
            指揮面板
          </span>
        </h2>
        <div className="w-2 h-2 bg-military-green rounded-full animate-pulse glow-green" />
      </div>

      {/* Mode Selector */}
      <div className="space-y-3">
        <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          選擇戰情模式
        </label>
        <div className="relative bg-titanium border-2 border-titanium rounded-xl p-1 flex">
          <motion.button
            type="button"
            onClick={() => setMode("god")}
            className={clsx(
              "flex-1 px-4 py-3 rounded-lg font-bold transition-all duration-300 relative z-10",
              mode === "god"
                ? "bg-gradient-to-r from-ai-blue/30 to-military-green/30 border-2 border-ai-blue/50 text-ai-blue glow-blue"
                : "text-gray-500 hover:text-gray-300"
            )}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            ⚔️ God 模式（全 AI 啟動）
            {mode === "god" && (
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-ai-blue/20 to-military-green/20 rounded-lg"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            )}
          </motion.button>
          <motion.button
            type="button"
            onClick={() => setMode("custom")}
            className={clsx(
              "flex-1 px-4 py-3 rounded-lg font-bold transition-all duration-300 relative z-10",
              mode === "custom"
                ? "bg-gradient-to-r from-metal-gold/30 to-command-red/30 border-2 border-metal-gold/50 text-metal-gold glow-gold"
                : "text-gray-500 hover:text-gray-300"
            )}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            ⚙️ 自訂模式
            {mode === "custom" && (
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-metal-gold/20 to-command-red/20 rounded-lg"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            )}
          </motion.button>
        </div>
      </div>

      {/* Provider Selector */}
      <div className="space-y-3">
        <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          AI Provider 狀態
        </label>
        <div className="grid grid-cols-2 gap-3">
          {(["gpt", "claude", "gemini", "perplexity"] as ProviderKey[]).map((provider) => {
            const config = PROVIDER_CONFIG[provider];
            const isEnabled = enabledProviders.includes(provider);
            const isDisabled = mode === "god";
            const isAvailable = availableProviders.includes(provider);

            const colorMap = {
              gpt: "from-blue-500/30 to-blue-600/30 border-blue-500/50 text-blue-400",
              claude: "from-yellow-500/30 to-amber-600/30 border-yellow-500/50 text-yellow-400",
              gemini: "from-cyan-500/30 to-cyan-600/30 border-cyan-500/50 text-cyan-400",
              perplexity: "from-green-500/30 to-emerald-600/30 border-green-500/50 text-green-400",
            };

            return (
              <motion.button
                key={provider}
                type="button"
                onClick={() => {
                  if (!isDisabled) {
                    if (isEnabled) {
                      setEnabledProviders(enabledProviders.filter((p) => p !== provider));
                    } else {
                      setEnabledProviders([...enabledProviders, provider]);
                    }
                  }
                }}
                disabled={isDisabled || !isAvailable}
                className={clsx(
                  "relative px-3 py-3 rounded-lg border-2 transition-all duration-300",
                  isEnabled && !isDisabled
                    ? `bg-gradient-to-r ${colorMap[provider]} glow-soft`
                    : "bg-titanium/50 border-gray-700 text-gray-500",
                  isDisabled && "opacity-60 cursor-not-allowed",
                  !isAvailable && "opacity-30"
                )}
                whileHover={!isDisabled && isAvailable ? { scale: 1.05 } : {}}
                whileTap={!isDisabled && isAvailable ? { scale: 0.95 } : {}}
              >
                <div className="flex items-center gap-2">
                  <div
                    className={clsx(
                      "w-2 h-2 rounded-full",
                      isEnabled && !isDisabled
                        ? provider === "gpt"
                          ? "bg-blue-400 animate-pulse"
                          : provider === "claude"
                          ? "bg-yellow-400 animate-pulse"
                          : provider === "gemini"
                          ? "bg-cyan-400 animate-pulse"
                          : "bg-green-400 animate-pulse"
                        : "bg-gray-600"
                    )}
                  />
                  <span className="text-xs font-semibold">{config.label}</span>
                </div>
              </motion.button>
            );
          })}
        </div>
        {mode === "god" && (
          <p className="text-xs text-gray-500 italic">God 模式：四家 Provider 全開</p>
        )}
      </div>

      {/* Stock Input */}
      <div className="space-y-3">
        <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          股票代號（可輸入多檔，以逗號或空白分隔）
        </label>
        <div className="relative">
          <input
            type="text"
            value={stockInput}
            onChange={(e) => setStockInput(e.target.value)}
            placeholder="輸入股票代碼，例如：2330, 2412, 2603"
            className="w-full px-4 py-3 bg-titanium/50 border-2 border-titanium rounded-xl text-foreground placeholder-gray-500 focus:outline-none focus:border-ai-blue/50 focus:ring-2 focus:ring-ai-blue/20 transition-all font-mono"
          />
        </div>
        {stockIds.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {stockIds.map((stockId) => (
              <motion.span
                key={stockId}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-ai-blue/20 border border-ai-blue/50 rounded-lg text-sm text-ai-blue font-mono font-semibold"
              >
                <span>{stockId}</span>
                <button
                  type="button"
                  onClick={() => removeStock(stockId)}
                  className="text-ai-blue hover:text-military-green transition-colors"
                >
                  ×
                </button>
              </motion.span>
            ))}
          </div>
        )}
      </div>

      {/* User Prompt */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            任務指令
          </label>
          <span className="text-xs text-gray-500 font-mono">{userPrompt.length} 字元</span>
        </div>
        <div className="relative">
          <textarea
            value={userPrompt}
            onChange={(e) => setUserPrompt(e.target.value)}
            placeholder="請輸入你要 J-GOD 幫你判斷的盤勢 / 策略問題…"
            rows={6}
            className="w-full px-4 py-3 bg-titanium/50 border-2 border-titanium rounded-xl text-foreground placeholder-gray-500 focus:outline-none focus:border-ai-blue/50 focus:ring-2 focus:ring-ai-blue/20 resize-none transition-all font-mono text-sm leading-relaxed"
          />
        </div>
      </div>

      {/* Start Button */}
      <motion.button
        onClick={handleStart}
        disabled={!canStart || isRunning || wsStatus === "connecting"}
        className={clsx(
          "w-full px-6 py-4 rounded-xl font-bold text-lg transition-all duration-300 relative overflow-hidden",
          canStart
            ? "bg-gradient-to-r from-command-red to-command-red/80 hover:from-command-red/90 hover:to-command-red/70 text-white glow-red"
            : "bg-titanium border-2 border-gray-700 text-gray-500 cursor-not-allowed"
        )}
        whileHover={canStart ? { scale: 1.02 } : {}}
        whileTap={canStart ? { scale: 0.98 } : {}}
      >
        {canStart ? (
          <>
            <span className="relative z-10 flex items-center justify-center gap-2">
              <span>⚔️</span>
              <span>啟動 J-GOD 戰情室</span>
            </span>
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
              animate={{ x: ["-100%", "100%"] }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            />
          </>
        ) : (
          "⚔️ 啟動 J-GOD 戰情室"
        )}
      </motion.button>
    </div>
  );
}

