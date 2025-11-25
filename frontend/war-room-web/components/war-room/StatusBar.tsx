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
    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <Badge variant="default">Mode: {mode === "god" ? "God" : "Custom"}</Badge>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Providers:</span>
            <div className="flex gap-1">
              {enabledProviders.map((provider) => (
                <Badge key={provider} variant="default">
                  {PROVIDER_CONFIG[provider].label}
                </Badge>
              ))}
            </div>
          </div>

          {stockIds.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">股票:</span>
              <span className="text-sm text-gray-300">{stockIds.join(", ")}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-4">
          {isRunning ? (
            <>
              <LoadingDots />
              <span className="text-sm text-blue-400">戰情室運行中...</span>
            </>
          ) : startedAt ? (
            <span className="text-sm text-gray-400">
              Total: {getElapsedTime()}s
            </span>
          ) : null}
        </div>
      </div>
    </div>
  );
}

