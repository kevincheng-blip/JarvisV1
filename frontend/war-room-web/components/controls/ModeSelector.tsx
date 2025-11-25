"use client";

interface ModeSelectorProps {
  mode: "god" | "custom";
  onChange: (mode: "god" | "custom") => void;
}

export function ModeSelector({ mode, onChange }: ModeSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-300">模式</label>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onChange("god")}
          className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
            mode === "god"
              ? "bg-blue-500/20 border-blue-500 text-blue-400"
              : "bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600"
          }`}
        >
          ⚔️ God
        </button>
        <button
          type="button"
          onClick={() => onChange("custom")}
          className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
            mode === "custom"
              ? "bg-blue-500/20 border-blue-500 text-blue-400"
              : "bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600"
          }`}
        >
          ⚙️ Custom
        </button>
      </div>
    </div>
  );
}

