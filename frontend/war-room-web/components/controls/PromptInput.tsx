"use client";

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function PromptInput({ value, onChange }: PromptInputProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-300">使用者指令</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="請描述你要戰情室分析的重點，例如：『短線留意 1 週內的反轉風險』"
        rows={4}
        className="w-full px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
      />
    </div>
  );
}

