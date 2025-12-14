/**
 * Ledger Status Card
 * 
 * Displays execution ledger status: NAV, cash, P&L, position
 * with buttons to reset ledger and simulate orders.
 */

import React from "react";
import { useLedgerLatest, useRecomputeLedger, useSimulateOrder } from "../../hooks/useExecution";

interface LedgerStatusCardProps {
  symbol: string | null;
}

export function LedgerStatusCard({ symbol }: LedgerStatusCardProps) {
  const selectedSymbol = symbol || "2330";
  
  const { data: ledger, isLoading: ledgerLoading } = useLedgerLatest(selectedSymbol);
  const recomputeLedger = useRecomputeLedger();
  const { data: orderSim, isLoading: orderSimLoading, refetch: refetchOrderSim } = useSimulateOrder(selectedSymbol);

  const handleResetLedger = () => {
    recomputeLedger.mutate(
      { symbol: selectedSymbol, initialCash: 1000000.0 },
      {
        onSuccess: () => {
          refetchOrderSim();
        },
      }
    );
  };

  const handleSimulateOrder = () => {
    refetchOrderSim();
  };

  if (ledgerLoading) {
    return (
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="text-sm text-gray-500 dark:text-gray-400">載入帳本中...</div>
      </div>
    );
  }

  const ledgerData = ledger?.ledger;
  const isDefault = ledger?.is_default || false;

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">執行帳本 (Ledger)</h4>
        {isDefault && (
          <span className="px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
            預設帳本
          </span>
        )}
      </div>

      {!ledgerData ? (
        <div className="text-sm text-gray-500 dark:text-gray-400">無帳本資料</div>
      ) : (
        <>
          {/* NAV and Cash */}
          <div className="mb-3 space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">NAV:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {ledgerData.nav.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">現金:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {ledgerData.cash.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* P&L */}
          <div className="mb-3 pt-3 border-t border-gray-200 dark:border-gray-700 space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">已實現損益:</span>
              <span
                className={`font-medium ${
                  ledgerData.realized_pnl >= 0
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                {ledgerData.realized_pnl >= 0 ? "+" : ""}
                {ledgerData.realized_pnl.toLocaleString("zh-TW", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">未實現損益:</span>
              <span
                className={`font-medium ${
                  ledgerData.unrealized_pnl >= 0
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                {ledgerData.unrealized_pnl >= 0 ? "+" : ""}
                {ledgerData.unrealized_pnl.toLocaleString("zh-TW", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          </div>

          {/* Position */}
          {ledgerData.position.qty > 0 && (
            <div className="mb-3 pt-3 border-t border-gray-200 dark:border-gray-700 space-y-1">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">持倉</div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">數量:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {ledgerData.position.qty.toLocaleString("zh-TW")} 股
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">平均成本:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {ledgerData.position.avg_cost.toLocaleString("zh-TW", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">市值:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {ledgerData.position.market_value.toLocaleString("zh-TW", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>
            </div>
          )}

          {/* Buttons */}
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 flex gap-2">
            <button
              onClick={handleResetLedger}
              disabled={recomputeLedger.isPending}
              className="flex-1 px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {recomputeLedger.isPending ? "重置中..." : "Reset Ledger"}
            </button>
            <button
              onClick={handleSimulateOrder}
              disabled={orderSimLoading}
              className="flex-1 px-2 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {orderSimLoading ? "計算中..." : "Simulate Order"}
            </button>
          </div>

          {/* Order Simulation Result */}
          {orderSim && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">訂單模擬結果</div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">動作:</span>
                  <span
                    className={`font-medium ${
                      orderSim.order_request.side === "BUY"
                        ? "text-green-600 dark:text-green-400"
                        : orderSim.order_request.side === "SELL"
                        ? "text-red-600 dark:text-red-400"
                        : "text-gray-600 dark:text-gray-400"
                    }`}
                  >
                    {orderSim.order_request.side}
                  </span>
                </div>
                {orderSim.order_request.qty > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">數量:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {orderSim.order_request.qty.toLocaleString("zh-TW")} 股
                    </span>
                  </div>
                )}
                {orderSim.order_request.reason && (
                  <div className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                    {orderSim.order_request.reason}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

