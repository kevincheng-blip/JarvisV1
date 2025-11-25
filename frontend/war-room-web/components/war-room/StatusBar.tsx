"use client";

import { ProviderKey, PROVIDER_CONFIG } from "@/lib/types/warRoom";
import { LoadingDots } from "../common/LoadingDots";
import { Badge } from "../common/Badge";

interface StatusBarProps {
  mode: "god" | "custom";
  enabledProviders: ProviderKey[];
  stockIds: string[];
  isRunning: boolean;
  startedAt?: number;
  finishedAt?: number;
}

export function StatusBar({
  mode,
  enabledProviders,
  stockIds,
  isRunning,
  startedAt,
  finishedAt,
}: StatusBarProps) {
  const getElapsedTime = () => {
    if (!startedAt) return null;
    const end = finishedAt || Date.now();
    return ((end - startedAt) / 1000).toFixed(1);
  };

  return (
    <div className="glass-panel border-2 border-titanium/50 rounded-xl p-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4 flex-wrap">
          <Badge variant="default" className="border-ai-blue/50 text-ai-blue">
            Mode: {mode === "god" ? "⚔️ God" : "⚙️ Custom"}
          </Badge>
          
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 uppercase tracking-wide">Providers:</span>
            <div className="flex gap-1">
              {enabledProviders.map((provider) => (
                <Badge key={provider} variant="default" className="font-mono text-xs">
                  {PROVIDER_CONFIG[provider].label}
                </Badge>
              ))}
            </div>
          </div>

          {stockIds.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 uppercase tracking-wide">股票:</span>
              <span className="text-sm text-foreground font-mono font-semibold">{stockIds.join(", ")}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-4">
          {isRunning ? (
            <>
              <LoadingDots />
              <span className="text-sm text-ai-blue font-semibold">戰情室運行中...</span>
            </>
          ) : startedAt ? (
            <span className="text-sm text-military-green font-mono font-semibold">
              Total: {getElapsedTime()}s
            </span>
          ) : null}
        </div>
      </div>
    </div>
  );
}

