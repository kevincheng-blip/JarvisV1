"use client";

import { ProviderKey, PROVIDER_CONFIG } from "@/lib/types/warRoom";

interface ProviderTagProps {
  provider: ProviderKey;
  className?: string;
}

export function ProviderTag({ provider, className = "" }: ProviderTagProps) {
  const config = PROVIDER_CONFIG[provider];
  
  const colorMap: Record<ProviderKey, string> = {
    gpt: "bg-ai-blue/20 text-ai-blue border-ai-blue/30",
    claude: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    gemini: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    perplexity: "bg-military-green/20 text-military-green border-military-green/30",
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${colorMap[provider]} ${className}`}
    >
      {config.label}
    </span>
  );
}

