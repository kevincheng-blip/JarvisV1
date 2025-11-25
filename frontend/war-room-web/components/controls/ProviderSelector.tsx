"use client";

import { ProviderKey, PROVIDER_CONFIG } from "@/lib/types/warRoom";

interface ProviderSelectorProps {
  enabledProviders: ProviderKey[];
  mode: "god" | "custom";
  onChange: (providers: ProviderKey[]) => void;
}

export function ProviderSelector({
  enabledProviders,
  mode,
  onChange,
}: ProviderSelectorProps) {
  const allProviders: ProviderKey[] = ["gpt", "claude", "gemini", "perplexity"];

  const handleToggle = (provider: ProviderKey) => {
    if (mode === "god") {
      return; // God 模式不可更改
    }

    if (enabledProviders.includes(provider)) {
      onChange(enabledProviders.filter((p) => p !== provider));
    } else {
      onChange([...enabledProviders, provider]);
    }
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-300">Provider</label>
      <div className="grid grid-cols-2 gap-2">
        {allProviders.map((provider) => {
          const config = PROVIDER_CONFIG[provider];
          const isEnabled = enabledProviders.includes(provider);
          const isDisabled = mode === "god";

          return (
            <button
              key={provider}
              type="button"
              onClick={() => handleToggle(provider)}
              disabled={isDisabled}
              className={`px-3 py-2 rounded-lg border text-sm transition-colors ${
                isEnabled
                  ? "bg-blue-500/20 border-blue-500 text-blue-400"
                  : "bg-gray-800/50 border-gray-700 text-gray-400"
              } ${isDisabled ? "opacity-60 cursor-not-allowed" : "hover:border-gray-600"}`}
            >
              {config.displayName}
            </button>
          );
        })}
      </div>
    </div>
  );
}

