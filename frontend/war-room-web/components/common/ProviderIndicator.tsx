"use client";

import { ProviderKey, PROVIDER_CONFIG } from "@/lib/types/warRoom";

interface ProviderIndicatorProps {
  provider: ProviderKey;
  isActive: boolean;
  className?: string;
}

export function ProviderIndicator({ provider, isActive, className = "" }: ProviderIndicatorProps) {
  const config = PROVIDER_CONFIG[provider];
  
  const colorMap: Record<ProviderKey, { glow: string; bg: string; border: string }> = {
    gpt: {
      glow: "shadow-[0_0_10px_rgba(59,130,246,0.5)]",
      bg: "bg-blue-500/20",
      border: "border-blue-500/50",
    },
    claude: {
      glow: "shadow-[0_0_10px_rgba(234,179,8,0.5)]",
      bg: "bg-yellow-500/20",
      border: "border-yellow-500/50",
    },
    gemini: {
      glow: "shadow-[0_0_10px_rgba(34,211,238,0.5)]",
      bg: "bg-cyan-500/20",
      border: "border-cyan-500/50",
    },
    perplexity: {
      glow: "shadow-[0_0_10px_rgba(34,197,94,0.5)]",
      bg: "bg-green-500/20",
      border: "border-green-500/50",
    },
  };

  const colors = colorMap[provider];

  return (
    <div
      className={`relative px-3 py-2 rounded-lg border transition-all ${
        isActive
          ? `${colors.bg} ${colors.border} ${colors.glow}`
          : "bg-gray-800/30 border-gray-700 opacity-50"
      } ${className}`}
    >
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${
            isActive
              ? provider === "gpt"
                ? "bg-blue-400 animate-pulse"
                : provider === "claude"
                ? "bg-yellow-400 animate-pulse"
                : provider === "gemini"
                ? "bg-cyan-400 animate-pulse"
                : "bg-green-400 animate-pulse"
              : "bg-gray-600"
          }`}
        />
        <span className="text-xs font-medium text-gray-300">{config.label}</span>
      </div>
    </div>
  );
}

