"use client";

import { ProviderKey, PROVIDER_CONFIG } from "@/lib/types/warRoom";

interface ProviderTagProps {
  provider: ProviderKey;
  className?: string;
}

export function ProviderTag({ provider, className = "" }: ProviderTagProps) {
  const config = PROVIDER_CONFIG[provider];
  
  const colorMap: Record<ProviderKey, string> = {
    gpt: "bg-green-500/20 text-green-400 border-green-500/30",
    claude: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    gemini: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    perplexity: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${colorMap[provider]} ${className}`}
    >
      {config.label}
    </span>
  );
}

