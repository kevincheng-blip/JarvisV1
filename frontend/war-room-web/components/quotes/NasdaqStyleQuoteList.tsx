"use client";

import { Quote } from "@/lib/types/quotes";

interface NasdaqStyleQuoteListProps {
  quotes: Quote[];
  onSelectSymbol?: (symbol: string) => void;
  className?: string;
}

export function NasdaqStyleQuoteList({
  quotes,
  onSelectSymbol,
  className = "",
}: NasdaqStyleQuoteListProps) {
  const formatPrice = (price: number): string => {
    return price.toFixed(2);
  };

  const formatChange = (change: number): string => {
    const sign = change >= 0 ? "+" : "";
    return `${sign}${change.toFixed(2)}%`;
  };

  const formatVolume = (volume: number): string => {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(2)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(2)}K`;
    }
    return volume.toString();
  };

  const getChangeColor = (change: number): string => {
    if (change > 0) {
      return "text-green-600";
    } else if (change < 0) {
      return "text-red-600";
    }
    return "text-gray-500";
  };

  const handleRowClick = (symbol: string) => {
    if (onSelectSymbol) {
      onSelectSymbol(symbol);
    }
  };

  return (
    <div className={`bg-white border border-blue-200 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gray-50 border-b border-blue-200 px-4 py-3">
        <div className="grid grid-cols-12 gap-4 text-xs font-semibold text-gray-800">
          <div className="col-span-3">Symbol</div>
          <div className="col-span-2 text-right">Price</div>
          <div className="col-span-2 text-right">Change %</div>
          <div className="col-span-5 text-right">Volume</div>
        </div>
      </div>

      {/* Body */}
      <div className="divide-y divide-gray-100">
        {quotes.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500 text-sm">
            暫無報價資料
          </div>
        ) : (
          quotes.map((quote, index) => (
            <div
              key={`${quote.symbol}-${index}`}
              onClick={() => handleRowClick(quote.symbol)}
              className={`px-4 py-3 hover:bg-blue-50 cursor-pointer transition-colors ${
                onSelectSymbol ? "" : "cursor-default"
              }`}
            >
              <div className="grid grid-cols-12 gap-4 text-sm text-gray-800">
                {/* Symbol */}
                <div className="col-span-3 font-medium">
                  {quote.symbol}
                </div>

                {/* Price */}
                <div className="col-span-2 text-right font-mono">
                  {formatPrice(quote.price)}
                </div>

                {/* Change */}
                <div className={`col-span-2 text-right font-mono ${getChangeColor(quote.change)}`}>
                  {formatChange(quote.change)}
                </div>

                {/* Volume */}
                <div className="col-span-5 text-right font-mono text-gray-600">
                  {formatVolume(quote.volume)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

