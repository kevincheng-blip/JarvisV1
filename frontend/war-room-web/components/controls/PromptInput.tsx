"use client";

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function PromptInput({ value, onChange }: PromptInputProps) {
  return (
    <div className="space-y-3">
      <label className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
        任務指令
      </label>
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="請描述你要戰情室分析的重點，例如：『短線留意 1 週內的反轉風險』"
          rows={6}
          className="w-full px-4 py-3 bg-gray-900/50 border-2 border-gray-800 rounded-xl text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 resize-none transition-all font-mono text-sm leading-relaxed"
        />
        <div className="absolute bottom-3 right-3 text-xs text-gray-500">
          {value.length} 字元
        </div>
      </div>
    </div>
  );
}

