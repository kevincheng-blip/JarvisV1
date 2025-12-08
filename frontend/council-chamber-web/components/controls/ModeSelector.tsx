"use client";

interface ModeSelectorProps {
  mode: "god" | "custom";
  onChange: (mode: "god" | "custom") => void;
}

export function ModeSelector({ mode, onChange }: ModeSelectorProps) {
  return (
    <div className="space-y-3">
      <label className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
        模式選擇
      </label>
      <div className="relative bg-gray-900/50 border-2 border-gray-800 rounded-xl p-1 flex">
        <button
          type="button"
          onClick={() => onChange("god")}
          className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all duration-300 relative ${
            mode === "god"
              ? "bg-gradient-to-r from-blue-600/30 to-purple-600/30 border-2 border-blue-500/50 text-blue-300 shadow-[0_0_20px_rgba(59,130,246,0.3)]"
              : "text-gray-500 hover:text-gray-300"
          }`}
        >
          <span className="relative z-10">⚔️ God Mode</span>
          {mode === "god" && (
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg animate-pulse" />
          )}
        </button>
        <button
          type="button"
          onClick={() => onChange("custom")}
          className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all duration-300 relative ${
            mode === "custom"
              ? "bg-gradient-to-r from-amber-600/30 to-orange-600/30 border-2 border-amber-500/50 text-amber-300 shadow-[0_0_20px_rgba(234,179,8,0.3)]"
              : "text-gray-500 hover:text-gray-300"
          }`}
        >
          <span className="relative z-10">⚙️ Custom</span>
          {mode === "custom" && (
            <div className="absolute inset-0 bg-gradient-to-r from-amber-600/20 to-orange-600/20 rounded-lg animate-pulse" />
          )}
        </button>
      </div>
    </div>
  );
}

