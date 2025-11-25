"use client";

import { ProviderKey } from "@/lib/types/warRoom";
import { ProviderIndicator } from "../common/ProviderIndicator";

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
    <div className="space-y-3">
      <label className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
        AI Provider 狀態
      </label>
      <div className="grid grid-cols-2 gap-3">
        {allProviders.map((provider) => {
          const isEnabled = enabledProviders.includes(provider);
          const isDisabled = mode === "god";

          return (
            <button
              key={provider}
              type="button"
              onClick={() => handleToggle(provider)}
              disabled={isDisabled}
              className={isDisabled ? "cursor-not-allowed" : "cursor-pointer"}
            >
              <ProviderIndicator provider={provider} isActive={isEnabled} />
            </button>
          );
        })}
      </div>
      {mode === "god" && (
        <p className="text-xs text-gray-500 italic">God 模式：四家 Provider 全開</p>
      )}
    </div>
  );
}

