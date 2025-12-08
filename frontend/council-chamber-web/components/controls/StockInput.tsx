"use client";

import { useState } from "react";

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

  const stockIds = parseStockIds(value);

  const removeStock = (stockId: string) => {
    const newValue = value
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter((s) => s !== stockId)
      .join(", ");
    onChange(newValue);
  };

  return (
    <div className="space-y-3">
      <label className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
        股票代碼
      </label>
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="輸入股票代碼，例如：2330, 2412, 2603"
          className="w-full px-4 py-3 bg-gray-900/50 border-2 border-gray-800 rounded-xl text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
        />
      </div>
      {stockIds.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {stockIds.map((stockId) => (
            <span
              key={stockId}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/20 border border-blue-500/50 rounded-lg text-sm text-blue-300"
            >
              <span className="font-mono font-semibold">{stockId}</span>
              <button
                type="button"
                onClick={() => removeStock(stockId)}
                className="text-blue-400 hover:text-blue-300 transition-colors"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

