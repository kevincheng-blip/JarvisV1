"use client";

interface StockInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function StockInput({ value, onChange }: StockInputProps) {
  const parseStockIds = (input: string): string[] => {
    return input
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-300">股票代碼</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="輸入股票代碼，例如：2330, 2412, 2603"
        className="w-full px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
      />
      {value && (
        <div className="text-xs text-gray-400">
          已輸入: {parseStockIds(value).join(", ") || "無"}
        </div>
      )}
    </div>
  );
}

